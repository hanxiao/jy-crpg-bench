/**
 * AI Gateway transport over the Workers AI binding.
 *
 * pi's Cloudflare AI Gateway support speaks HTTPS
 * (`gateway.ai.cloudflare.com/v1/{account}/{gateway}/{provider}/...`, see `api/cloudflare.ts`),
 * which needs a Cloudflare API token even when the caller is a Worker in the gateway's own
 * account.
 *
 * In order to solve for this problem, `createGatewayBindingFetch` returns a {@link FetchFunction}
 * that translates requests under a gateway HTTPS prefix into calls to the Workers AI binding's
 * universal endpoint, `env.AI.gateway(id).run({provider, endpoint, headers, query})`.
 * Binding calls are pre-authenticated in-account and return the provider's native wire format as a
 * regular (streaming) `Response`, so API implementations behave identically over either
 * transport.
 *
 * The result is the transport for one gateway-bound client, not a general-purpose fetch:
 * requests it cannot serve — URLs outside the prefix, or in-prefix requests the universal
 * endpoint cannot express (non-POST, non-JSON body) — reject with a descriptive error.
 * Transport selection is the caller's job, per client: route such traffic over HTTPS with
 * real gateway auth instead of through this shim.
 */
import type { FetchFunction } from "../types.ts";
/**
 * Structural type for the Workers AI binding's gateway surface (`env.AI`), so this
 * module does not depend on `@cloudflare/workers-types`. Any real `Ai` binding satisfies it.
 */
export interface AiGatewayBinding {
    gateway(id: string): AiGatewayBindingGateway;
}
export interface AiGatewayBindingGateway {
    run(data: AiGatewayUniversalRequestLike, options?: {
        signal?: AbortSignal;
    }): Promise<Response>;
}
/** One universal-endpoint request entry, as accepted by `AiGateway.run()`. */
export interface AiGatewayUniversalRequestLike {
    provider: string;
    endpoint: string;
    headers: Record<string, string>;
    query: unknown;
}
/**
 * Placeholder value for auth headers on binding-routed requests. API implementations
 * require an API key or a recognized auth header (`authorization`, `x-api-key`,
 * `cf-aig-authorization`) before dispatch; binding calls are pre-authenticated, so pass
 * `cf-aig-authorization: Bearer ${CLOUDFLARE_GATEWAY_BINDING_AUTH_SENTINEL}` to satisfy
 * the check. The shim strips `cf-aig-authorization` before calling the binding. Pair it with
 * `Authorization: null` / `x-api-key: null` so the SDKs' placeholder auth headers never reach
 * the gateway, which would treat a request-supplied auth header as a BYOK provider key that
 * overrides its stored keys — the same as it would over HTTPS.
 */
export declare const CLOUDFLARE_GATEWAY_BINDING_AUTH_SENTINEL = "cloudflare-gateway-binding";
export interface GatewayBindingFetchOptions {
    /** The Workers AI binding (e.g. `env.AI`). */
    binding: AiGatewayBinding;
    /**
     * Gateway HTTPS prefix every request must fall under, without a trailing slash:
     * `https://gateway.ai.cloudflare.com/v1/{accountId}/{gatewayName}`.
     */
    baseUrl: string;
    /** Gateway name passed to `binding.gateway()`. Must match the `baseUrl` gateway. */
    gateway: string;
}
/**
 * Create a `fetch` that routes AI Gateway requests through the Workers AI binding.
 * See the module docs for behavior and composition notes.
 */
export declare function createGatewayBindingFetch(options: GatewayBindingFetchOptions): FetchFunction;
//# sourceMappingURL=cloudflare-gateway-binding.d.ts.map