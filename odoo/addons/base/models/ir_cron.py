# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import threading
import time
import os
import psycopg2
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from psycopg2 import sql

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

BASE_VERSION = odoo.modules.get_manifest('base')['version']
MAX_FAIL_TIME = timedelta(hours=5)  # chosen with a fair roll of the dice
MAX_BATCH_PER_CRON_JOB = 10
CONSECUTIVE_TIMEOUT_FOR_FAILURE = 3
MIN_FAILURE_COUNT_BEFORE_DEACTIVATION = 5
MIN_DELTA_BEFORE_DEACTIVATION = timedelta(days=7)
# Cron must satisfy both minimum before deactivation

# custom function to call instead of default PostgreSQL's `pg_notify`
ODOO_NOTIFY_FUNCTION = os.getenv('ODOO_NOTIFY_FUNCTION', 'pg_notify')


class BadVersion(Exception):
    pass

class BadModuleState(Exception):
    pass


_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class ir_cron(models.Model):
    """ Model describing cron jobs (also called actions or tasks).
    """

    # TODO: perhaps in the future we could consider a flag on ir.cron jobs
    # that would cause database wake-up even if the database has not been
    # loaded yet or was already unloaded (e.g. 'force_db_wakeup' or something)
    # See also odoo.cron

    _name = "ir.cron"
    _order = 'cron_name'
    _description = 'Scheduled Actions'
    _allow_sudo_commands = False

    ir_actions_server_id = fields.Many2one(
        'ir.actions.server', 'Server action',
        delegate=True, ondelete='restrict', required=True)
    cron_name = fields.Char('Name', compute='_compute_cron_name', store=True)
    user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)
    active = fields.Boolean(default=True)
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')
    nextcall = fields.Datetime(string='Next Execution Date', required=True, default=fields.Datetime.now, help="Next planned execution date for this job.")
    lastcall = fields.Datetime(string='Last Execution Date', help="Previous time the cron ran successfully, provided to the job through the context on the `lastcall` key")
    priority = fields.Integer(default=5, help='The priority of the job, as an integer: 0 means higher priority, 10 means lower priority.')
    failure_count = fields.Integer(default=0, help="The number of consecutive failures of this job, reset on success.")
    first_failure_date = fields.Datetime(string='First Failure Date', help="The first time the cron failed, reset on success.")

    _sql_constraints = [
        (
            'check_strictly_positive_interval',
            'CHECK(interval_number > 0)',
            'The interval number must be a strictly positive number.'
        ),
    ]

    @api.depends('ir_actions_server_id.name')
    def _compute_cron_name(self):
        for cron in self.with_context(lang='en_US'):
            cron.cron_name = cron.ir_actions_server_id.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['usage'] = 'ir_cron'
        if os.getenv('ODOO_NOTIFY_CRON_CHANGES'):
            self._cr.postcommit.add(self._notifydb)
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        # only 'code' state is supported for cron job so set it as default
        if not self._context.get('default_state'):
            self = self.with_context(default_state='code')
        return super(ir_cron, self).default_get(fields_list)

    def method_direct_trigger(self):
        self.ensure_one()
        self.check_access_rights('write')
        self._try_lock()
        _logger.info('Manually starting job `%s`.', self.name)
        self = self.with_user(self.user_id).with_context({'lastcall': self.lastcall})._add_progress()
        self.ir_actions_server_id.run()
        self.lastcall = fields.Datetime.now()
        self.env.flush_all()
        _logger.info('Job `%s` done.', self.name)
        return True

    @classmethod
    def _process_jobs(cls, db_name):
        """ Execute every job ready to be run on this database. """
        try:
            db = odoo.sql_db.db_connect(db_name)
            threading.current_thread().dbname = db_name
            with db.cursor() as cron_cr:
                cls._check_version(cron_cr)
                jobs = cls._get_all_ready_jobs(cron_cr)
                if not jobs:
                    return
                cls._check_modules_state(cron_cr, jobs)

                for job_id in (job['id'] for job in jobs):
                    try:
                        job = cls._acquire_one_job(cron_cr, job_id)
                    except psycopg2.extensions.TransactionRollbackError:
                        cron_cr.rollback()
                        _logger.debug("job %s has been processed by another worker, skip", job_id)
                        continue
                    if not job:
                        _logger.debug("another worker is processing job %s, skip", job_id)
                        continue
                    _logger.debug("job %s acquired", job_id)
                    # take into account overridings of _process_job() on that database
                    registry = odoo.registry(db_name)
                    registry[cls._name]._process_job(db, cron_cr, job)
                    _logger.debug("job %s updated and released", job_id)

        except BadVersion:
            _logger.warning('Skipping database %s as its base version is not %s.', db_name, BASE_VERSION)
        except BadModuleState:
            _logger.warning('Skipping database %s because of modules to install/upgrade/remove.', db_name)
        except psycopg2.ProgrammingError as e:
            if e.pgcode == '42P01':
                # Class 42 — Syntax Error or Access Rule Violation; 42P01: undefined_table
                # The table ir_cron does not exist; this is probably not an OpenERP database.
                _logger.warning('Tried to poll an undefined table on database %s.', db_name)
            else:
                raise
        except Exception:
            _logger.warning('Exception in cron:', exc_info=True)
        finally:
            if hasattr(threading.current_thread(), 'dbname'):
                del threading.current_thread().dbname

    @classmethod
    def _check_version(cls, cron_cr):
        """ Ensure the code version matches the database version """
        cron_cr.execute("""
            SELECT latest_version
            FROM ir_module_module
             WHERE name='base'
        """)
        (version,) = cron_cr.fetchone()
        if version is None:
            raise BadModuleState()
        if version != BASE_VERSION:
            raise BadVersion()

    @classmethod
    def _check_modules_state(cls, cr, jobs):
        """ Ensure no module is installing or upgrading """
        cr.execute("""
            SELECT COUNT(*)
            FROM ir_module_module
            WHERE state LIKE %s
        """, ['to %'])
        (changes,) = cr.fetchone()
        if not changes:
            return

        if not jobs:
            raise BadModuleState()

        oldest = min([
            fields.Datetime.from_string(job['nextcall'])
            for job in jobs
        ])
        if datetime.now() - oldest < MAX_FAIL_TIME:
            raise BadModuleState()

        # the cron execution failed around MAX_FAIL_TIME * 60 times (1 failure
        # per minute for 5h) in which case we assume that the crons are stuck
        # because the db has zombie states and we force a call to
        # reset_module_states.
        odoo.modules.reset_modules_state(cr.dbname)

    @classmethod
    def _get_all_ready_jobs(cls, cr):
        """ Return a list of all jobs that are ready to be executed """
        cr.execute("""
            SELECT *
            FROM ir_cron
            WHERE active = true
              AND (nextcall <= (now() at time zone 'UTC')
                OR id in (
                    SELECT cron_id
                    FROM ir_cron_trigger
                    WHERE call_at <= (now() at time zone 'UTC')
                )
              )
            ORDER BY failure_count, priority, id
        """)
        return cr.dictfetchall()

    @classmethod
    def _acquire_one_job(cls, cr, job_id):
        """
        Acquire for update the job whose id is job_id.
        The job should not have been processed yet.

        It is possible that this function raises a `psycopg2.errors.SerializationFailure`
        in case the job has been processed in another worker.
        In such case it is advised to roll back the transaction and to go on with the other jobs.
        """

        # We have to make sure ALL jobs are executed ONLY ONCE at a time no
        # matter how many cron workers may process them. The exclusion mechanism
        # is twofold: (i) prevent parallel processing of the same job,
        # and (ii) prevent re-processing jobs that have been processed
        # already and should not be re-processed.
        #
        # (i) is implemented via `LIMIT 1 FOR UPDATE SKIP LOCKED`, each
        # worker just acquire one available job at a time and lock it so
        # the other workers don't select it too.
        # (ii) is implemented via the `WHERE` statement, when a job has
        # been processed, its nextcall is updated to a date in the
        # future and the optional triggers are removed if there is no need
        # for additional processing.
        #
        # Note about (ii): it is possible that a job becomes available
        # again quickly (e.g. high frequency or self-triggering cron).
        # This function doesn't prevent from acquiring that job multiple
        # times at different moments. This can block a worker on
        # executing a same job in loop. To prevent this problem, the
        # callee is responsible for providing a `job_id` that has not
        # been executed yet.
        #
        # An `UPDATE` lock type is the strongest row lock, it conflicts
        # with ALL other lock types. Among them the `KEY SHARE` row lock
        # which is implicitly acquired by foreign keys to prevent the
        # referenced record from being removed while in use. Because we
        # never delete acquired cron jobs, foreign keys are safe to
        # concurrently reference cron jobs. Hence, the `NO KEY UPDATE`
        # row lock is used, it is a weaker lock that does conflict with
        # everything BUT `KEY SHARE`.
        #
        # Learn more: https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS

        query = """
            WITH last_cron_progress AS (
                SELECT id as progress_id, cron_id, timed_out_counter, done, remaining
                FROM ir_cron_progress
                WHERE cron_id = %s
                ORDER BY id DESC
                LIMIT 1
            )
            SELECT *
            FROM ir_cron
            LEFT JOIN last_cron_progress lcp ON lcp.cron_id = ir_cron.id
            WHERE ir_cron.active = true
              AND (nextcall <= (now() at time zone 'UTC')
                OR EXISTS (
                    SELECT cron_id
                    FROM ir_cron_trigger
                    WHERE call_at <= (now() at time zone 'UTC')
                      AND cron_id = ir_cron.id
                )
              )
              AND id = %s
            ORDER BY priority
            FOR NO KEY UPDATE SKIP LOCKED
        """
        try:
            cr.execute(query, [job_id, job_id], log_exceptions=False)
        except psycopg2.extensions.TransactionRollbackError:
            # A serialization error can occur when another cron worker
            # commits the new `nextcall` value of a cron it just ran and
            # that commit occured just before this query. The error is
            # genuine and the job should be skipped in this cron worker.
            raise
        except Exception as exc:
            _logger.error("bad query: %s\nERROR: %s", query, exc)
            raise

        job = cr.dictfetchone()
        for field_name in ('done', 'remaining', 'timed_out_counter'):
            job[field_name] = job[field_name] or 0
        return job

    def _notify_admin(self, message):
        _logger.warning(message)

    def _notify_admin_deactivation(self, cron_name, cron_id, action_id):
        self._notify_admin(_('The cron %s with id %s call from action %s has been deactivated after failing 5 consecutive times.\n'
                             'Verify the cron logs for more information.', cron_name, cron_id, action_id))

    @classmethod
    def _process_job(cls, db, cron_cr, job):
        """ Execute the cron's server action in a dedicated transaction if the timeout limit has not been reached yet.
        The server action can report progression using the ir.cron.progress model.
        In case it notify that not all records could have been processed,
        the cron will be executed again as soon as possible and process the remaining records.
        When the server action reported that all records have been processed,
        the cron is scheduled again in the future."""


        env = api.Environment(cron_cr, job['user_id'], {})
        ir_cron = env[cls._name]

        failed_by_timeout = (
            job['timed_out_counter'] >= CONSECUTIVE_TIMEOUT_FOR_FAILURE
            and not job['done']
        )

        if not failed_by_timeout:
            status = cls._run_job(job)
        else:
            status = 'FAILED'
            cron_cr.execute("""
                UPDATE ir_cron_progress
                SET timed_out_counter = 0
                WHERE id = %s
            """, (job['progress_id'],))
            _logger.error("Job `%s` (%s): Server action #%s timed-out.",
                          job['cron_name'], job['id'], job['ir_actions_server_id'])

        ir_cron._update_failure_count(cron_cr, job, status)

        if status in ('FULLY_DONE', 'FAILED'):
            ir_cron._mark_as_done(cron_cr, job)
        elif os.getenv('ODOO_NOTIFY_CRON_CHANGES'):     # See: `_notifydb`
            ir_cron._cr.postcommit.add(ir_cron._notifydb)

        cron_cr.commit()

    @classmethod
    def _run_job(cls, job):
        """ Execute the job's server action in a loop until it completes
        (i.e., the server action notifies no remaining records to process)
        or it fails without any record processed (i.e., the server action
        crashes and notifies no record done.)
        Each call to the server action is executed in its own transaction.
        The server action is called up to ``MAX_BATCH_PER_CRON_CALL`` (10)
        times in this loop.

        :return: a string with 3 possible values:
         - 'FULLY_DONE': There is no remaining record to process or no record has been processed
         - 'PARTIALLY_DONE': Record have been processed and there is remaining record to process,
                            even in case of exception
         - 'FAILED': There was an exception during the execution and either no record has been processed or there is no
                    remaining record to process.
        """
        timed_out_counter = job['timed_out_counter']

        with cls.pool.cursor() as job_cr:
            env = api.Environment(job_cr, job['user_id'], {'lastcall': job['lastcall'], 'cron_id': job['id']})
            cron = env[cls._name].browse(job['id'])
            status = None
            for i in range(MAX_BATCH_PER_CRON_JOB):
                cron = cron._add_progress(timed_out_counter=timed_out_counter)
                progress = cron._get_progress()
                job_cr.commit()

                try:
                    cron._callback(job['cron_name'], job['ir_actions_server_id'])
                except Exception:
                    # If some progress has been committed, we do not consider it a failure
                    status = 'PARTIALLY_DONE' if progress.done and progress.remaining else 'FAILED'
                else:
                    if not progress.remaining:
                        status = 'FULLY_DONE'
                    elif not progress.done:
                        # no work was done, we assume nothing has to be done
                        status = 'FULLY_DONE'
                    else:
                        status = 'PARTIALLY_DONE'
                finally:
                    progress.timed_out_counter = 0
                    timed_out_counter = 0
                    job_cr.commit()
                _logger.info('Job `%s`: %s records processed and %s records remaining.',
                             job['cron_name'], progress.done, progress.remaining)
                if status in ['FULLY_DONE', 'FAILED']:
                    break

        return status

    def _update_failure_count(self, cr, job, status):
        """ Update cron `failure_count` and `first_failure_date`.
        Count is increased on failure and both fields are reset on success.
        Cron that fail MIN_FAILURE_COUNT_BEFORE_DEACTIVATION times in a row over a period at least greater
        than MIN_DELTA_BEFORE_DEACTIVATION are deactivated.
        """
        now = fields.Datetime.context_timestamp(self, datetime.utcnow())

        if status == 'FAILED':
            failure_count = job['failure_count'] + 1
            first_failure_date = job['first_failure_date'] or now
            active = job['active']
            if (
                failure_count >= MIN_FAILURE_COUNT_BEFORE_DEACTIVATION
                and fields.Datetime.context_timestamp(self, first_failure_date) + MIN_DELTA_BEFORE_DEACTIVATION < now
            ):
                failure_count = 0
                first_failure_date = None
                active = False
                self._notify_admin_deactivation(job['cron_name'], job['id'], job['ir_actions_server_id'])
        else:
            failure_count = 0
            first_failure_date = None
            active = job['active']

        cr.execute("""
            UPDATE ir_cron
            SET failure_count = %s,
                first_failure_date = %s,
                active = %s
            WHERE id = %s
        """, [
            failure_count,
            first_failure_date,
            active,
            job['id'],
        ])

    def _mark_as_done(self, cr, job):
        """ Update cron `nextcall` and `lastcall` and delete past triggers."""
        # Use the user's timezone to compare and compute datetimes, otherwise unexpected results may appear.
        # For instance, adding 1 month in UTC to July 1st at midnight in GMT+2 gives July 30 instead of August 1st!
        now = fields.Datetime.context_timestamp(self, datetime.utcnow())
        nextcall = fields.Datetime.context_timestamp(self, job['nextcall'])
        interval = _intervalTypes[job['interval_type']](job['interval_number'])
        while nextcall <= now:
            nextcall += interval

        _logger.info('Job `%s` (%s): .',
                     job['cron_name'], job['id'])
        cr.execute("""
            UPDATE ir_cron
            SET nextcall = %s,
                lastcall = %s
            WHERE id = %s
        """, [
            fields.Datetime.to_string(nextcall.astimezone(pytz.UTC)),
            fields.Datetime.to_string(now.astimezone(pytz.UTC)),
            job['id'],
        ])

        cr.execute("""
            DELETE FROM ir_cron_trigger
            WHERE cron_id = %s
              AND call_at < (now() at time zone 'UTC')
        """, [job['id']])

    def _callback(self, cron_name, server_action_id):
        """ Run the method associated to a given job. It takes care of logging
        and exception handling. Note that the user running the server action
        is the user calling this method. """
        self.ensure_one()
        try:
            if self.pool != self.pool.check_signaling():
                # the registry has changed, reload self in the new registry
                self.env.reset()
                self = self.env()[self._name]

            log_depth = (None if _logger.isEnabledFor(logging.DEBUG) else 1)
            odoo.netsvc.log(_logger, logging.DEBUG, 'cron.object.execute', (self._cr.dbname, self._uid, '*', cron_name, server_action_id), depth=log_depth)
            _logger.info('Starting job `%s`.', cron_name)
            start_time = time.time()
            self.env['ir.actions.server'].browse(server_action_id).run()
            self.env.flush_all()
            end_time = time.time()
            _logger.info('Job done: `%s` (%.3fs).', cron_name, end_time - start_time)
            if start_time and _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('%.3fs (cron %s, server action %d with uid %d)', end_time - start_time, cron_name, server_action_id, self.env.uid)
            self.pool.signal_changes()
        except Exception:
            self.pool.reset_changes()
            _logger.exception("Call from cron %s for server action #%s failed in Job #%s",
                              cron_name, server_action_id, job_id)
            self.env.cr.rollback()
            raise

    def _try_lock(self, lockfk=False):
        """Try to grab a dummy exclusive write-lock to the rows with the given ids,
           to make sure a following write() or unlink() will not block due
           to a process currently executing those cron tasks.

           :param lockfk: acquire a strong row lock which conflicts with
                          the lock acquired by foreign keys when they
                          reference this row.
        """
        if not self:
            return
        row_level_lock = "UPDATE" if lockfk else "NO KEY UPDATE"
        try:
            self._cr.execute(f"""
                SELECT id
                FROM "{self._table}"
                WHERE id IN %s
                FOR {row_level_lock} NOWAIT
            """, [tuple(self.ids)], log_exceptions=False)
        except psycopg2.OperationalError:
            self._cr.rollback()  # early rollback to allow translations to work for the user feedback
            raise UserError(_("Record cannot be modified right now: "
                              "This cron task is currently being executed and may not be modified "
                              "Please try again in a few minutes"))

    def write(self, vals):
        self._try_lock()
        if ('nextcall' in vals or vals.get('active')) and os.getenv('ODOO_NOTIFY_CRON_CHANGES'):
            self._cr.postcommit.add(self._notifydb)
        return super(ir_cron, self).write(vals)

    def unlink(self):
        self._try_lock(lockfk=True)
        return super(ir_cron, self).unlink()

    def try_write(self, values):
        try:
            with self._cr.savepoint():
                self._cr.execute(f"""
                    SELECT id
                    FROM "{self._table}"
                    WHERE id IN %s
                    FOR NO KEY UPDATE NOWAIT
                """, [tuple(self.ids)], log_exceptions=False)
        except psycopg2.OperationalError:
            pass
        else:
            return super(ir_cron, self).write(values)
        return False

    @api.model
    def toggle(self, model, domain):
        # Prevent deactivated cron jobs from being re-enabled through side effects on
        # neutralized databases.
        if self.env['ir.config_parameter'].sudo().get_param('database.is_neutralized'):
            return True

        active = bool(self.env[model].search_count(domain))
        return self.try_write({'active': active})

    def _trigger(self, at=None):
        """
        Schedule a cron job to be executed soon independently of its
        ``nextcall`` field value.

        By default, the cron is scheduled to be executed the next time the cron worker
        wakes up but the optional `at` argument may be given to delay the execution
        later with a precision down to 1 minute.

        The method may be called with a datetime or an iterable of datetime.
        The actual implementation is in :meth:`~._trigger_list`, which is the
        recommended method for overrides.

        :param Optional[Union[datetime.datetime, list[datetime.datetime]]] at:
            When to execute the cron, at one or several moments in time instead
            of as soon as possible.
        :return: the created triggers records
        :rtype: recordset
        """
        if at is None:
            at_list = [fields.Datetime.now()]
        elif isinstance(at, datetime):
            at_list = [at]
        else:
            at_list = list(at)
            assert all(isinstance(at, datetime) for at in at_list)

        return self._trigger_list(at_list)

    def _trigger_list(self, at_list):
        """
        Implementation of :meth:`~._trigger`.

        :param list[datetime.datetime] at_list:
            Execute the cron later, at precise moments in time.
        :return: the created triggers records
        :rtype: recordset
        """
        self.ensure_one()
        now = fields.Datetime.now()

        if not self.sudo().active:
            # skip triggers that would be ignored
            at_list = [at for at in at_list if at > now]

        if not at_list:
            return self.env['ir.cron.trigger']

        triggers = self.env['ir.cron.trigger'].sudo().create([
            {'cron_id': self.id, 'call_at': at}
            for at in at_list
        ])
        if _logger.isEnabledFor(logging.DEBUG):
            ats = ', '.join(map(str, at_list))
            _logger.debug("will execute '%s' at %s", self.sudo().name, ats)

        if min(at_list) <= now or os.getenv('ODOO_NOTIFY_CRON_CHANGES'):
            self._cr.postcommit.add(self._notifydb)
        return triggers

    def _notifydb(self):
        """ Wake up the cron workers
        The ODOO_NOTIFY_CRON_CHANGES environment variable allows to force the notifydb on both
        ir_cron modification and on trigger creation (regardless of call_at)
        """
        with odoo.sql_db.db_connect('postgres').cursor() as cr:
            query = sql.SQL("SELECT {}('cron_trigger', %s)").format(sql.Identifier(ODOO_NOTIFY_FUNCTION))
            cr.execute(query, [self.env.cr.dbname])
        _logger.debug("cron workers notified")

    def _add_progress(self, *, timed_out_counter=None):
        """ Create a progress record for the given cron and add it to its context.

        :param int timed_out_counter: the number of times the cron has consecutively timed out
        """
        progress = self.env['ir.cron.progress'].create([{
                'cron_id': self.id,
                'remaining': 0,
                'done': 0,
                # we use timed_out_counter + 1 so that if the current execution
                # times out, the counter already takes it into account
                'timed_out_counter': 0 if timed_out_counter is None else timed_out_counter + 1,
        }])
        return self.with_context(ir_cron_progress_id=progress.id)

    def _get_progress(self):
        return self.env['ir.cron.progress'].browse(self.env.context.get('ir_cron_progress_id'))

    def _notify_progress(self, *, done, remaining):
        """ Log the progress of the cron job.
        :param int done: the number of tasks already executed
        :param int remaining: the number of tasks to be executed
        """
        if not (progress_id := self.env.context.get('ir_cron_progress_id')):
            return
        if done < 0 or remaining < 0:
            raise ValueError("`done` and `remaining` must be positive integers.")
        self.env['ir.cron.progress'].browse(progress_id).write({
            'remaining': remaining,
            'done': done,
        })


class ir_cron_trigger(models.Model):
    _name = 'ir.cron.trigger'
    _description = 'Triggered actions'
    _rec_name = 'cron_id'
    _allow_sudo_commands = False

    cron_id = fields.Many2one("ir.cron", index=True)
    call_at = fields.Datetime()

    @api.autovacuum
    def _gc_cron_triggers(self):
        self.search([('call_at', '<', datetime.now() + relativedelta(weeks=-1))]).unlink()


class ir_cron_progress(models.Model):
    _name = 'ir.cron.progress'
    _description = 'Progress of Scheduled Actions'
    _rec_name = 'cron_id'

    cron_id = fields.Many2one("ir.cron", required=True, index=True)
    remaining = fields.Integer(default=0)
    done = fields.Integer(default=0)
    timed_out_counter = fields.Integer(default=0)

    @api.autovacuum
    def _gc_cron_progress(self):
        self.search([('create_date', '<', datetime.now() - relativedelta(weeks=1))]).unlink()
