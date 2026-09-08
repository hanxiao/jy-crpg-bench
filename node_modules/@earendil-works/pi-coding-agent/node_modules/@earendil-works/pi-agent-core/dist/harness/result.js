export const Result = {
    ok(value) {
        return { ok: true, value };
    },
    err(error) {
        return { ok: false, error };
    },
    isOk(result) {
        return result.ok;
    },
    isErr(result) {
        return !result.ok;
    },
};
export function TaggedError(tag) {
    class TaggedErrorClass extends Error {
        _tag = tag;
        constructor(props) {
            super(props.message);
            this.name = tag;
            Object.assign(this, props);
        }
        toJSON() {
            const payload = {};
            for (const key of Object.keys(this)) {
                if (key !== "_tag")
                    payload[key] = this[key];
            }
            return { _tag: tag, message: this.message, ...payload };
        }
        static is(value) {
            return value instanceof TaggedErrorClass;
        }
    }
    return TaggedErrorClass;
}
export function matchError(error, matchers) {
    const matcher = matchers[error._tag];
    return matcher(error);
}
//# sourceMappingURL=result.js.map