export type Result<TValue, TError> = {
    ok: true;
    value: TValue;
} | {
    ok: false;
    error: TError;
};
export declare const Result: {
    ok<TValue>(value: TValue): Result<TValue, never>;
    err<TError>(error: TError): Result<never, TError>;
    isOk<TValue, TError>(result: Result<TValue, TError>): result is {
        ok: true;
        value: TValue;
    };
    isErr<TValue, TError>(result: Result<TValue, TError>): result is {
        ok: false;
        error: TError;
    };
};
export interface TaggedErrorValue<Tag extends string> extends Error {
    readonly _tag: Tag;
    toJSON(): {
        _tag: Tag;
        message: string;
    } & Record<string, unknown>;
}
export interface TaggedErrorFactory<Tag extends string> {
    new <Props extends {
        message: string;
    }>(props: Props): TaggedErrorValue<Tag> & Readonly<Props>;
    is(value: unknown): value is TaggedErrorValue<Tag>;
}
export declare function TaggedError<Tag extends string>(tag: Tag): TaggedErrorFactory<Tag>;
export type ErrorMatchers<TError extends TaggedErrorValue<string>, TValue> = {
    [Tag in TError["_tag"]]: (error: Extract<TError, {
        _tag: Tag;
    }>) => TValue;
};
export declare function matchError<TError extends TaggedErrorValue<string>, TValue>(error: TError, matchers: ErrorMatchers<TError, TValue>): TValue;
//# sourceMappingURL=result.d.ts.map