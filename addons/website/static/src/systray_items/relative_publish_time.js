import { RelativeTime } from "@mail/core/common/relative_time";
import { _t } from "@web/core/l10n/translation";

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;

export class RelativePublishTime extends RelativeTime {
    static props = {
        datetime: Object, 
        negativeDeltaCallback: {
            type: Function,
            optional: true,
        }
    }

    setup() {
        super.setup();
        this.computeRelativeTime();
    }

    computeRelativeTime() {
        if (!this.props.datetime) {
            this.relativeTime = "";
            return;
        }
        const delta = this.props.datetime.ts - Date.now();
        if (delta < 0) {
            this.props.negativeDeltaCallback();
            clearTimeout(this.timeout);
        } else if(delta < MINUTE) {
            this.relativeTime = _t("shortly");
        } else {
            this.relativeTime = this.props.datetime.toRelative();
        }
        const updateDelay = delta < HOUR ? MINUTE : HOUR;
        if (updateDelay) {
            this.timeout = setTimeout(() => {
                this.computeRelativeTime();
                this.render();
            }, updateDelay);
        }
    }
}
