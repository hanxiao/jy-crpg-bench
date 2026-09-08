export interface PromiseResolvers<T> {
    promise: Promise<T>;
    resolve(value: T | PromiseLike<T>): void;
    reject(reason?: unknown): void;
}
/** Remove in favor of `Promise.withResolvers()` when the repository's TypeScript lib baseline moves to ES2024. */
export declare function createPromiseResolvers<T>(): PromiseResolvers<T>;
//# sourceMappingURL=promise.d.ts.map