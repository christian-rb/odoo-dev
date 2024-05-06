import base64
import datetime
from types import SimpleNamespace

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import constant_time, hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Is this hidden from server actions ?
STR_TO_HASH = {
    'sha1': hashes.SHA1(),
    'sha256': hashes.SHA256(),
}

class Certificate(models.Model):
    _name = 'certificate.certificate'
    _description = 'Certificate'

    name = fields.Char(string='Name', required=True)
    content = fields.Binary(string='Certificate', required=True, attachment=False)
    content_format = fields.Selection(
        string='Content format',
        help='The encoding type of the content.',
        selection=[
            ('der', 'DER'),
            ('pem', 'PEM'),
            ('pkcs12', 'PKCS12'),
        ],
        required=True,
        default='der',
    )
    pkcs12_password = fields.Char(string='Certificate Password', help='Password to decrypt the PKS file.')
    private_key = fields.Binary(string='Certificate Key', help='Certificate Key', attachment=False)
    private_key_password = fields.Char(string='Private key password', help='Password to decrypt the private key.')
    private_key_format = fields.Selection(
        string='Private key format',
        help='The encoding type of the private key.',
        selection=[
            ('der', 'DER'),
            ('pem', 'PEM'),
        ],
        default=False,
    )
    hashing_algorithm = fields.Selection(
        string='Hashing algorithm',
        help="This hashing algorithm will be used for all cryptographic operations involving this certificate.",
        selection=[
            ('sha1', 'SHA1'),
            ('sha256', 'SHA256'),
        ],
        default='sha256',
        required=True,
    )
    pem_certificate = fields.Binary(string='Certificate in PEM format', attachment=False, readonly=True)
    pem_private_key = fields.Binary(string='Private key in PEM format', attachment=False, readonly=True)
    serial_number = fields.Char(string='Serial number', help='The serial number to add to electronic documents', readonly=True, index=True)
    fingerprint = fields.Char(string='Certificate fingerprint', compute='_compute_fingerprint')
    date_start = fields.Datetime(string='Available date', help='The date on which the certificate starts to be valid (UTC)', readonly=True)
    date_end = fields.Datetime(string='Expiration date', help='The date on which the certificate expires (UTC)', readonly=True)
    is_valid = fields.Boolean(string='Valid', compute='_compute_is_valid', search='_search_is_valid')
    active = fields.Boolean(name='Active', help='Set active to false to archive the certificate.', default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    country_code = fields.Char(related='company_id.country_id.code', depends=['company_id'])

    @api.onchange('content_format')
    def _onchange_certificate_format(self):
        if self.content_format == 'pkcs12':
            self.private_key = False
            self.private_key_password = False
            self.private_key_format = False

    @api.constrains('pem_certificate', 'pem_private_key')
    def _constrains_certificate_key_compatibility(self):
        if self.pem_certificate and self.pem_private_key:
            cert = x509.load_pem_x509_certificate(base64.b64decode(self.pem_certificate))
            pkey = serialization.load_pem_private_key(base64.b64decode(self.pem_private_key), None)
            cert_public_key_bytes = cert.public_key().public_bytes(
                encoding=Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            pkey_public_key_bytes = pkey.public_key().public_bytes(
                encoding=Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            if not constant_time.bytes_eq(pkey_public_key_bytes, cert_public_key_bytes):
                raise UserError(_("The certificate and private key are not compatible."))

    @api.depends('date_start', 'date_end')
    def _compute_is_valid(self):
        # TODO somehow manage timezones better
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        for certificate in self:
            date_start = certificate.date_start.replace(tzinfo=datetime.timezone.utc)
            date_end = certificate.date_end.replace(tzinfo=datetime.timezone.utc)
            certificate.is_valid = not (utc_now < date_start or utc_now > date_end)

    def _search_is_valid(self, operator, value):
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise UserError(_('Operation not supported'))
        if operator != '=':
            value = not value
        certificates = self.env['certificate.certificate'].search([('active', '=', True)]).filtered(lambda cert: cert.is_valid == value)
        return [('id', 'in', certificates.ids)]

    @api.depends('pem_certificate', 'hashing_algorithm')
    def _compute_fingerprint(self):
        for certificate in self:
            if certificate.pem_certificate:
                cert = x509.load_pem_x509_certificate(base64.b64decode(certificate.pem_certificate))
                certificate.fingerprint = base64.b64encode(cert.fingerprint(STR_TO_HASH[certificate.hashing_algorithm])).decode()

    # Todo: change to a compute instead? it seems more logic because at the moment nothing changes when the cert is modified
    # Idea of imporvement: make a cascade of try catch so that the users does not have to specify the certificate/key format
    @api.model_create_multi
    def create(self, vals_list):
        certificates = super().create(vals_list)

        for certificate in certificates:
            # Manage certificate formatting
            try:
                content = base64.b64decode(certificate.content)
                if certificate.content_format == 'der':
                    cert = x509.load_der_x509_certificate(content)
                elif certificate.content_format == 'pkcs12':
                    pkcs12_password = certificate.pkcs12_password.encode('utf-8') if certificate.pkcs12_password else None
                    pkey, cert, _additionnal_certs = pkcs12.load_key_and_certificates(content, pkcs12_password)
                else:
                    cert = x509.load_pem_x509_certificate(content)
            except ValueError:
                raise UserError(_("The certificate could not be loaded. Make sure the correct format has been selected."))

            # Manage key formatting
            pkey_content = base64.b64decode(certificate.private_key) if certificate.private_key else b""
            pkey_password = certificate.private_key_password.encode('utf-8') if certificate.private_key_password else None
            try:
                if certificate.private_key_format == 'der':
                    pkey = serialization.load_der_private_key(pkey_content, pkey_password)
                elif certificate.private_key_format == 'pem':
                    pkey = serialization.load_pem_private_key(pkey_content, pkey_password)
            except ValueError:
                raise UserError(_("The private key could not be loaded. Make sure the correct format has been selected."))

            # Extract certificate data
            certificate.pem_certificate = base64.b64encode(cert.public_bytes(Encoding.PEM))
            certificate.date_start = cert.not_valid_before
            certificate.date_end = cert.not_valid_after
            certificate.serial_number = cert.serial_number

            # Extract private key data
            if pkey_content or certificate.content_format == 'pkcs12':
                certificate.pem_private_key = base64.b64encode(
                    pkey.private_bytes(
                        encoding=Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )
        return certificates
    
    # TODO make a function that return a the DER formatting of certificate, it is called often
    def _get_public_key_numbers(self):
        self.ensure_one()
        public_key = serialization.load_pem_private_key(base64.b64decode(self.pem_private_key), None).public_key()
        e = public_key.public_numbers().e
        e = base64.b64encode(e.to_bytes((e.bit_length() + 7) // 8, 'big')).decode('utf-8')
        n = public_key.public_numbers().n
        n = base64.b64encode(n.to_bytes((n.bit_length() + 7) // 8, 'big')).decode('utf-8')
        return e, n

    def _sign(self, message):
        """ Return the base64 encoded signature of message. """
        self.ensure_one()

        if not isinstance(message, bytes):
            message = message.encode('utf-8')
        private_key = serialization.load_pem_private_key(base64.b64decode(self.pem_private_key), None)
        signature = private_key.sign(
            message,
            padding.PKCS1v15(
                # mgf=padding.MGF1(STR_TO_HASH[self.hashing_algorithm]),
                # salt_length=padding.PSS.MAX_LENGTH
            ),
            STR_TO_HASH[self.hashing_algorithm]
        )
        return base64.b64encode(signature)
    
    @api.model
    def _sign_with_key(self, message, pem_key, pwd=None, hashing_algorithm='sha256'):
        """ Return the base64 encoded signature of message. """
        if not isinstance(message, bytes):
            message = message.encode('utf-8')
        private_key = serialization.load_pem_private_key(base64.b64decode(pem_key), pwd)
        signature = private_key.sign(
            message,
            padding.PKCS1v15(
                # mgf=padding.MGF1(STR_TO_HASH[self.hashing_algorithm]),
                # salt_length=padding.PSS.MAX_LENGTH
            ),
            STR_TO_HASH[hashing_algorithm]
        )
        return base64.b64encode(signature)

    def _verify(self, message, signature):
        """ Verify the base64 encoded signature of message. """
        self.ensure_one()

        if not isinstance(message, bytes):
            message = message.encode('utf-8')
        if not isinstance(signature, bytes):
            signature = signature.encode('utf-8')

        private_key = serialization.load_pem_private_key(base64.b64decode(self.pem_private_key), None)
        public_key = private_key.public_key()
        try:
            public_key.verify(
                base64.b64decode(signature),
                message,
                padding.PSS(
                    mgf=padding.MGF1(STR_TO_HASH[self.hashing_algorithm]),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                STR_TO_HASH[self.hashing_algorithm]
            )
            verification = True
        except InvalidSignature:
            verification = False
        return verification

    # Check if b64encode the return value is useful to reduce lines or not
    def _digest(self, messages):
        if not isinstance(messages, list):
            messages = [messages]
        digest = hashes.Hash(STR_TO_HASH[self.hashing_algorithm])
        for message in messages:
            if not isinstance(message, bytes):
                message = message.encode('utf-8')
            digest.update(message)
        return digest.finalize()

    def load_key_and_certificates(self):
        private_key, certificate, _dummy = pkcs12.load_key_and_certificates(self.content, self.pkcs12_password, backend=default_backend())

        def public_key():
            public_key = certificate.public_key()

            def public_numbers():
                public_numbers = public_key.public_numbers()
                return SimpleNamespace(**{
                    'n': public_numbers.n,
                    'e': public_numbers.e,
                })
            return SimpleNamespace(**{
                'public_numbers': public_numbers,
                'public_bytes': public_key.public_bytes,
            })

        simple_private_key = SimpleNamespace(**{
            '_sign': private_key._sign,
            'private_bytes': private_key.private_bytes,
        })

        simple_certificate = SimpleNamespace(**{
            'fingerprint': lambda algo: certificate.fingerprint(algo),
            'issuer': SimpleNamespace(**{
                'rfc4514_string': certificate.issuer.rfc4514_string,
                'rdns': [
                    SimpleNamespace(**{'rfc4514_string': item.rfc4514_string})
                    for item in certificate.issuer.rdns
                ],
                'get_attributes_for_oid': lambda oid: [
                    SimpleNamespace(**{'value': item.value})
                    for item in certificate.issuer.get_attributes_for_oid(oid)
                ]
            }),
            'not_valid_after': certificate.not_valid_after,
            'not_valid_before': certificate.not_valid_before,
            'public_key': public_key,
            'public_bytes': certificate.public_bytes,
            'serial_number': certificate.serial_number,
        })
        return simple_private_key, simple_certificate
