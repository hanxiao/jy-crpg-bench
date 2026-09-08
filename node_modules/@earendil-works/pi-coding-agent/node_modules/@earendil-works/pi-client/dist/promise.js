/** Remove in favor of `Promise.withResolvers()` when the repository's TypeScript lib baseline moves to ES2024. */
export function createPromiseResolvers() {
    let resolve;
    let reject;
    const promise = new Promise((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, resolve, reject };
}
//# sourceMappingURL=promise.js.map