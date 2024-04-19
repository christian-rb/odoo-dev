export class ChannelCommand {
    /** @type {number} */
    endPosition;
    /** @type {boolean} */
    hasSubCommand;
    /** @type {string} */
    methodName;
    /** @type {string} */
    name;
    /** @type {Object} */
    subCommandData;
    /** @type {string[]} */
    subCommandFields;

    constructor(params) {
        this.endPosition = params.endPosition;
        this.methodName = params.methodName;
        this.name = params.name;
        this.subCommandFields = params.subCommandFields;
        this.hasSubCommand = Boolean(params.subCommandFields);
        this.subCommandData = {};
    }

    get params() {
        const res = {};
        if (this.subCommandFields) {
            for (const field of this.subCommandFields) {
                res[field] = this.subCommandData[field] ?? false;
            }
        }
        return res;
    }
}
