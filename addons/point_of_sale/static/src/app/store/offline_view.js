import { ORM, ormService } from "@web/core/orm_service";
import { registry } from "@web/core/registry";
import { ConnectionLostError } from "@web/core/network/rpc";

/**
 * The idea is that we catch ch all the views that have to work offline
 */
class PosORM extends ORM {
    constructor() {
        super();
        this.cache = {};
    }
    async call(model, method, args = [], kwargs = {}) {
        console.log("PosORM call", this.cache);
        return super
            .call(...arguments)
            .then((res) => {
                if (!kwargs.context) {
                    return res;
                }
                if (!this.cache[model]) {
                    this.cache[model] = {};
                }
                this.cache[model][method] = res;
                return res;
            })
            .catch((e) => {
                if (e instanceof ConnectionLostError) {
                    return this.cache[model][method];
                }
            });
    }
}

export const posOrmService = {
    ...ormService,
    start() {
        return new PosORM();
    },
};

registry.category("services").remove("orm");
registry.category("services").add("orm", posOrmService);
