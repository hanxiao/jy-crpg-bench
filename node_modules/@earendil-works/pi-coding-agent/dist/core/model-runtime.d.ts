import { type Api, type AssistantMessage, type AssistantMessageEventStream, type AuthCheck, type AuthInteraction, type AuthOperationOptions, type AuthResult, type AuthType, type Context, type Credential, type CredentialInfo, type CredentialStore, type DeferredHandle, type Model, type Models, type ModelsApiStreamOptions, type ModelsDeferredCancelOptions, type ModelsDeferredFetchOptions, type ModelsRefreshOptions, type ModelsRefreshResult, type ModelsSimpleStreamOptions, type ModelsStore, type Provider } from "@earendil-works/pi-ai";
import { type AuthStatus, type CompatibilityRequestConfig, type ProviderConfigInput } from "./provider-composer.ts";
export interface CreateModelRuntimeOptions {
    /** Credential storage. Defaults to the file at authPath. */
    credentials?: CredentialStore;
    authPath?: string;
    modelsPath?: string | null;
    modelsStore?: ModelsStore;
    modelsStorePath?: string;
    /** Allow create() to refresh model catalogs over the network. Defaults to false. */
    allowModelNetwork?: boolean;
    /** Timeout for the create-time network model refresh. */
    modelRefreshTimeoutMs?: number;
    catalogBaseUrl?: string;
    /** Optional caller cancellation for initial cache restoration and availability checks. */
    signal?: AbortSignal;
    /** Skip initial catalog and availability refresh. Static models remain available. */
    refreshOnCreate?: boolean;
}
export interface ModelRuntimeAuthOverrides extends AuthOperationOptions {
    apiKey?: string;
    env?: Record<string, string>;
    /** Require this much remaining OAuth-token validity; defaults to five minutes. */
    minOAuthValidityMs?: number;
}
export type CredentialSynchronizationOperation = "login" | "logout" | "setRuntimeApiKey" | "removeRuntimeApiKey";
/** Credentials changed successfully, but the local model/auth snapshot could not be synchronized. */
export declare class CredentialSynchronizationError extends Error {
    readonly providerId: string;
    readonly operation: CredentialSynchronizationOperation;
    readonly credential: Credential | undefined;
    constructor(providerId: string, operation: CredentialSynchronizationOperation, credential: Credential | undefined, options: ErrorOptions);
}
/** Configured pi-ai Models collection used by coding-agent and SDK consumers. */
export declare class ModelRuntime implements Models {
    private readonly models;
    private readonly credentials;
    private readonly defaultBuiltins;
    private readonly builtins;
    private readonly nativeExtensionProviders;
    private readonly extensionProviders;
    private readonly compositionErrors;
    private readonly modelsPath;
    private readonly modelNetworkEnabled;
    private config;
    private snapshot;
    private availabilityRefreshSeq;
    private availabilityErrorSeq;
    private readonly providerAvailabilitySeq;
    private availabilityError;
    private readonly credentialOperations;
    private constructor();
    static create(options?: CreateModelRuntimeOptions): Promise<ModelRuntime>;
    private configureRadiusProviders;
    private providerIds;
    private recomposeProvider;
    private rebuildProviders;
    private updateModelSnapshot;
    private runAvailabilityRefresh;
    private queueAvailabilityRefresh;
    private refreshProviderAvailability;
    getProviders(): readonly Provider[];
    getProvider(providerId: string): Provider | undefined;
    getModels(providerId?: string): readonly Model<Api>[];
    getModel(providerId: string, modelId: string): Model<Api> | undefined;
    checkAuth(providerId: string, options?: AuthOperationOptions): Promise<AuthCheck | undefined>;
    getAvailable(providerId?: string, options?: AuthOperationOptions): Promise<readonly Model<Api>[]>;
    getAvailableSnapshot(): readonly Model<Api>[];
    getError(): string | undefined;
    getRegisteredProviderConfig(providerId: string): ProviderConfigInput | undefined;
    getRegisteredProviderIds(): readonly string[];
    getRegisteredNativeProvider(providerId: string): Provider | undefined;
    /** @internal Compatibility fallback for ModelRegistry when provider auth is unconfigured. */
    getCompatibilityRequestConfig(model: Model<Api>): CompatibilityRequestConfig;
    isUsingOAuth(providerId: string): boolean;
    isUsingSubscription(providerId: string): boolean;
    hasConfiguredAuth(providerId: string): boolean;
    getAuth(providerId: string, overrides?: ModelRuntimeAuthOverrides): Promise<AuthResult | undefined>;
    getAuth(model: Model<Api>, overrides?: ModelRuntimeAuthOverrides): Promise<AuthResult | undefined>;
    private enqueueCredentialOperation;
    private synchronizeCredentialState;
    setRuntimeApiKey(providerId: string, apiKey: string, options?: AuthOperationOptions): Promise<void>;
    removeRuntimeApiKey(providerId: string, options?: AuthOperationOptions): Promise<void>;
    listCredentials(options?: AuthOperationOptions): Promise<readonly CredentialInfo[]>;
    getProviderAuthStatus(providerId: string): AuthStatus;
    private prepareRequest;
    stream<TApi extends Api>(model: Model<TApi>, context: Context, options?: ModelsApiStreamOptions<TApi>): AssistantMessageEventStream;
    complete<TApi extends Api>(model: Model<TApi>, context: Context, options?: ModelsApiStreamOptions<TApi>): Promise<AssistantMessage>;
    streamSimple(model: Model<Api>, context: Context, options?: ModelsSimpleStreamOptions): AssistantMessageEventStream;
    completeSimple(model: Model<Api>, context: Context, options?: ModelsSimpleStreamOptions): Promise<AssistantMessage>;
    fetchDeferred(model: Model<Api>, handle: DeferredHandle, options?: ModelsDeferredFetchOptions): Promise<AssistantMessage>;
    cancelDeferred(model: Model<Api>, handle: DeferredHandle, options?: ModelsDeferredCancelOptions): Promise<void>;
    login(providerId: string, type: AuthType, interaction: AuthInteraction): Promise<Credential>;
    logout(providerId: string, options?: AuthOperationOptions): Promise<void>;
    refresh(options?: ModelsRefreshOptions): Promise<ModelsRefreshResult>;
    registerNativeProvider(provider: Provider): void;
    registerProvider(providerId: string, config: ProviderConfigInput): void;
    unregisterProvider(providerId: string): void;
}
//# sourceMappingURL=model-runtime.d.ts.map