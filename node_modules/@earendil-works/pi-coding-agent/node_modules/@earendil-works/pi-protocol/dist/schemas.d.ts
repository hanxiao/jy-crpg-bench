import Type, { type Static } from "typebox";
export declare const PROTOCOL_VERSION: 1;
export type JsonValue = null | boolean | number | string | JsonValue[] | {
    [key: string]: JsonValue;
};
export declare const JsonValueSchema: Type.TUnsafe<JsonValue>;
export declare const ThinkingLevelSchema: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
export type ThinkingLevel = Static<typeof ThinkingLevelSchema>;
/** Matches AgentHarnessPhase so adapters do not need a second phase vocabulary. */
export declare const SessionPhaseSchema: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
export type SessionPhase = Static<typeof SessionPhaseSchema>;
export declare const ModelRefSchema: Type.TObject<{
    readonly provider: Type.TString;
    readonly id: Type.TString;
}>;
export type ModelRef = Static<typeof ModelRefSchema>;
export declare const ModelCostSchema: Type.TObject<{
    readonly input: Type.TNumber;
    readonly output: Type.TNumber;
    readonly cacheRead: Type.TNumber;
    readonly cacheWrite: Type.TNumber;
}>;
export declare const ModelMetadataSchema: Type.TObject<{
    readonly provider: Type.TString;
    readonly id: Type.TString;
    readonly name: Type.TString;
    readonly api: Type.TString;
    readonly reasoning: Type.TBoolean;
    readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
    readonly contextWindow: Type.TInteger;
    readonly maxTokens: Type.TInteger;
    readonly cost: Type.TObject<{
        readonly input: Type.TNumber;
        readonly output: Type.TNumber;
        readonly cacheRead: Type.TNumber;
        readonly cacheWrite: Type.TNumber;
    }>;
    readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
    readonly authenticated: Type.TBoolean;
}>;
export type ModelMetadata = Static<typeof ModelMetadataSchema>;
export declare const TextContentSchema: Type.TObject<{
    readonly type: Type.TLiteral<"text">;
    readonly text: Type.TString;
}>;
export declare const ThinkingContentSchema: Type.TObject<{
    readonly type: Type.TLiteral<"thinking">;
    readonly thinking: Type.TString;
    readonly redacted: Type.TOptional<Type.TBoolean>;
}>;
export declare const ImageContentSchema: Type.TObject<{
    readonly type: Type.TLiteral<"image">;
    readonly data: Type.TString;
    readonly mimeType: Type.TString;
}>;
export declare const ToolCallContentSchema: Type.TObject<{
    readonly type: Type.TLiteral<"toolCall">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
}>;
export declare const UserContentSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"text">;
    readonly text: Type.TString;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"image">;
    readonly data: Type.TString;
    readonly mimeType: Type.TString;
}>]>;
export declare const AssistantContentSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"text">;
    readonly text: Type.TString;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"thinking">;
    readonly thinking: Type.TString;
    readonly redacted: Type.TOptional<Type.TBoolean>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"toolCall">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
}>]>;
export declare const ToolContentSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"text">;
    readonly text: Type.TString;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"image">;
    readonly data: Type.TString;
    readonly mimeType: Type.TString;
}>]>;
export type TextContent = Static<typeof TextContentSchema>;
export type ThinkingContent = Static<typeof ThinkingContentSchema>;
export type ImageContent = Static<typeof ImageContentSchema>;
export type ToolCallContent = Static<typeof ToolCallContentSchema>;
export declare const UsageSchema: Type.TObject<{
    readonly input: Type.TInteger;
    readonly output: Type.TInteger;
    readonly cacheRead: Type.TInteger;
    readonly cacheWrite: Type.TInteger;
    readonly reasoning: Type.TOptional<Type.TInteger>;
    readonly totalTokens: Type.TInteger;
    readonly cost: Type.TObject<{
        readonly input: Type.TNumber;
        readonly output: Type.TNumber;
        readonly cacheRead: Type.TNumber;
        readonly cacheWrite: Type.TNumber;
        readonly total: Type.TNumber;
    }>;
}>;
export type Usage = Static<typeof UsageSchema>;
export declare const UserTranscriptItemSchema: Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"user">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly timestamp: Type.TInteger;
}>;
export declare const AssistantTranscriptItemSchema: Type.TUnion<[Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"streaming">;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"complete">;
    readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"error">;
    readonly stopReason: Type.TLiteral<"error">;
    readonly errorMessage: Type.TOptional<Type.TString>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"aborted">;
    readonly stopReason: Type.TLiteral<"aborted">;
    readonly errorMessage: Type.TOptional<Type.TString>;
}>]>;
export declare const ToolTranscriptItemSchema: Type.TUnion<[Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"running">;
    readonly isError: Type.TLiteral<false>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"complete">;
    readonly isError: Type.TLiteral<false>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"error">;
    readonly isError: Type.TLiteral<true>;
}>]>;
export declare const TranscriptItemSchema: Type.TUnion<[Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"user">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly timestamp: Type.TInteger;
}>, Type.TUnion<[Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"streaming">;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"complete">;
    readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"error">;
    readonly stopReason: Type.TLiteral<"error">;
    readonly errorMessage: Type.TOptional<Type.TString>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"assistant">;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"thinking">;
        readonly thinking: Type.TString;
        readonly redacted: Type.TOptional<Type.TBoolean>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"toolCall">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
    }>]>>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly responseModel: Type.TOptional<Type.TString>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"aborted">;
    readonly stopReason: Type.TLiteral<"aborted">;
    readonly errorMessage: Type.TOptional<Type.TString>;
}>]>, Type.TUnion<[Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"running">;
    readonly isError: Type.TLiteral<false>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"complete">;
    readonly isError: Type.TLiteral<false>;
}>, Type.TObject<{
    readonly id: Type.TString;
    readonly role: Type.TLiteral<"tool">;
    readonly toolCallId: Type.TString;
    readonly toolName: Type.TString;
    readonly input: Type.TUnsafe<JsonValue>;
    readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"text">;
        readonly text: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"image">;
        readonly data: Type.TString;
        readonly mimeType: Type.TString;
    }>]>>;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    readonly usage: Type.TOptional<Type.TObject<{
        readonly input: Type.TInteger;
        readonly output: Type.TInteger;
        readonly cacheRead: Type.TInteger;
        readonly cacheWrite: Type.TInteger;
        readonly reasoning: Type.TOptional<Type.TInteger>;
        readonly totalTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
            readonly total: Type.TNumber;
        }>;
    }>>;
    readonly timestamp: Type.TInteger;
    readonly status: Type.TLiteral<"error">;
    readonly isError: Type.TLiteral<true>;
}>]>]>;
export type UserTranscriptItem = Static<typeof UserTranscriptItemSchema>;
export type AssistantTranscriptItem = Static<typeof AssistantTranscriptItemSchema>;
export type ToolTranscriptItem = Static<typeof ToolTranscriptItemSchema>;
export type TranscriptItem = Static<typeof TranscriptItemSchema>;
/** Normalized incremental activity. Snapshots remain authoritative. */
export declare const TranscriptProgressSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"item_started">;
    readonly item: Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"user">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly timestamp: Type.TInteger;
    }>, Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"streaming">;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly stopReason: Type.TLiteral<"error">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"aborted">;
        readonly stopReason: Type.TLiteral<"aborted">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>]>, Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"running">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly isError: Type.TLiteral<true>;
    }>]>]>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"assistant_delta">;
    readonly messageId: Type.TString;
    readonly contentIndex: Type.TInteger;
    readonly kind: Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"thinking">, Type.TLiteral<"toolCall">]>;
    readonly delta: Type.TString;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"item_updated">;
    readonly item: Type.TUnion<[Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"streaming">;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly stopReason: Type.TLiteral<"error">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"aborted">;
        readonly stopReason: Type.TLiteral<"aborted">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>]>, Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"running">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly isError: Type.TLiteral<true>;
    }>]>]>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"item_finished">;
    readonly item: Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly stopReason: Type.TLiteral<"error">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"aborted">;
        readonly stopReason: Type.TLiteral<"aborted">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly isError: Type.TLiteral<true>;
    }>]>;
}>]>;
export type TranscriptProgress = Static<typeof TranscriptProgressSchema>;
export declare const SessionMetadataSchema: Type.TObject<{
    readonly id: Type.TString;
    readonly createdAt: Type.TInteger;
    readonly updatedAt: Type.TOptional<Type.TInteger>;
    readonly parentSessionId: Type.TOptional<Type.TString>;
    readonly sessionName: Type.TOptional<Type.TString>;
    readonly cwd: Type.TOptional<Type.TString>;
}>;
export declare const SessionSnapshotSchema: Type.TObject<{
    readonly id: Type.TString;
    readonly name: Type.TOptional<Type.TString>;
    readonly cwd: Type.TString;
    readonly createdAt: Type.TInteger;
    readonly updatedAt: Type.TInteger;
    readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
    readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
    readonly attached: Type.TBoolean;
    readonly locked: Type.TBoolean;
    readonly revision: Type.TInteger;
    readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"user">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly timestamp: Type.TInteger;
    }>, Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"streaming">;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly stopReason: Type.TLiteral<"error">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"assistant">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"thinking">;
            readonly thinking: Type.TString;
            readonly redacted: Type.TOptional<Type.TBoolean>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"toolCall">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
        }>]>>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly responseModel: Type.TOptional<Type.TString>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"aborted">;
        readonly stopReason: Type.TLiteral<"aborted">;
        readonly errorMessage: Type.TOptional<Type.TString>;
    }>]>, Type.TUnion<[Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"running">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"complete">;
        readonly isError: Type.TLiteral<false>;
    }>, Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"tool">;
        readonly toolCallId: Type.TString;
        readonly toolName: Type.TString;
        readonly input: Type.TUnsafe<JsonValue>;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
        readonly usage: Type.TOptional<Type.TObject<{
            readonly input: Type.TInteger;
            readonly output: Type.TInteger;
            readonly cacheRead: Type.TInteger;
            readonly cacheWrite: Type.TInteger;
            readonly reasoning: Type.TOptional<Type.TInteger>;
            readonly totalTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
                readonly total: Type.TNumber;
            }>;
        }>>;
        readonly timestamp: Type.TInteger;
        readonly status: Type.TLiteral<"error">;
        readonly isError: Type.TLiteral<true>;
    }>]>]>>;
    readonly queuedSteer: Type.TArray<Type.TObject<{
        readonly id: Type.TString;
        readonly role: Type.TLiteral<"user">;
        readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"text">;
            readonly text: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"image">;
            readonly data: Type.TString;
            readonly mimeType: Type.TString;
        }>]>>;
        readonly timestamp: Type.TInteger;
    }>>;
    readonly queuedSteerCount: Type.TInteger;
}>;
export type SessionMetadata = Static<typeof SessionMetadataSchema>;
export type SessionSnapshot = Static<typeof SessionSnapshotSchema>;
export declare const ServerSnapshotSchema: Type.TObject<{
    readonly serverId: Type.TString;
    readonly protocolVersion: Type.TLiteral<1>;
    readonly revision: Type.TInteger;
    readonly sessions: Type.TArray<Type.TObject<{
        readonly id: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TOptional<Type.TInteger>;
        readonly parentSessionId: Type.TOptional<Type.TString>;
        readonly sessionName: Type.TOptional<Type.TString>;
        readonly cwd: Type.TOptional<Type.TString>;
    }>>;
    readonly models: Type.TArray<Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
        readonly name: Type.TString;
        readonly api: Type.TString;
        readonly reasoning: Type.TBoolean;
        readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
        readonly contextWindow: Type.TInteger;
        readonly maxTokens: Type.TInteger;
        readonly cost: Type.TObject<{
            readonly input: Type.TNumber;
            readonly output: Type.TNumber;
            readonly cacheRead: Type.TNumber;
            readonly cacheWrite: Type.TNumber;
        }>;
        readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
        readonly authenticated: Type.TBoolean;
    }>>;
}>;
export type ServerSnapshot = Static<typeof ServerSnapshotSchema>;
export declare const ProtocolErrorCodeSchema: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
export declare const ProtocolErrorSchema: Type.TObject<{
    readonly code: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
    readonly message: Type.TString;
    readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
}>;
export type ProtocolErrorCode = Static<typeof ProtocolErrorCodeSchema>;
export type ProtocolError = Static<typeof ProtocolErrorSchema>;
export declare const ListCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"list">;
}>;
export declare const CreateCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"create">;
    readonly cwd: Type.TOptional<Type.TString>;
    readonly name: Type.TOptional<Type.TString>;
    readonly model: Type.TOptional<Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>>;
    readonly thinkingLevel: Type.TOptional<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
}>;
export declare const AttachCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"attach">;
    readonly sessionId: Type.TString;
}>;
export declare const DetachCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"detach">;
    readonly sessionId: Type.TString;
}>;
export declare const PromptCommandSchema: Type.TObject<{
    readonly sessionId: Type.TString;
    readonly text: Type.TString;
    readonly command: Type.TLiteral<"prompt">;
}>;
export declare const SteerCommandSchema: Type.TObject<{
    readonly sessionId: Type.TString;
    readonly text: Type.TString;
    readonly command: Type.TLiteral<"steer">;
}>;
export declare const AbortCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"abort">;
    readonly sessionId: Type.TString;
}>;
export declare const SetModelCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"set_model">;
    readonly sessionId: Type.TString;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
}>;
export declare const SetThinkingCommandSchema: Type.TObject<{
    readonly command: Type.TLiteral<"set_thinking">;
    readonly sessionId: Type.TString;
    readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
}>;
export declare const CommandSchema: Type.TUnion<[Type.TObject<{
    readonly command: Type.TLiteral<"list">;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"create">;
    readonly cwd: Type.TOptional<Type.TString>;
    readonly name: Type.TOptional<Type.TString>;
    readonly model: Type.TOptional<Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>>;
    readonly thinkingLevel: Type.TOptional<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"attach">;
    readonly sessionId: Type.TString;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"detach">;
    readonly sessionId: Type.TString;
}>, Type.TObject<{
    readonly sessionId: Type.TString;
    readonly text: Type.TString;
    readonly command: Type.TLiteral<"prompt">;
}>, Type.TObject<{
    readonly sessionId: Type.TString;
    readonly text: Type.TString;
    readonly command: Type.TLiteral<"steer">;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"abort">;
    readonly sessionId: Type.TString;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"set_model">;
    readonly sessionId: Type.TString;
    readonly model: Type.TObject<{
        readonly provider: Type.TString;
        readonly id: Type.TString;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"set_thinking">;
    readonly sessionId: Type.TString;
    readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
}>]>;
export type Command = Static<typeof CommandSchema>;
export type CommandName = Command["command"];
export declare const CreateResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"create">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const AttachResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"attach">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const PromptResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"prompt">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const SteerResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"steer">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const AbortResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"abort">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const SetModelResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"set_model">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const SetThinkingResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"set_thinking">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>;
export declare const ListResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"list">;
    readonly sessions: Type.TArray<Type.TObject<{
        readonly id: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TOptional<Type.TInteger>;
        readonly parentSessionId: Type.TOptional<Type.TString>;
        readonly sessionName: Type.TOptional<Type.TString>;
        readonly cwd: Type.TOptional<Type.TString>;
    }>>;
}>;
export declare const DetachResultSchema: Type.TObject<{
    readonly command: Type.TLiteral<"detach">;
    readonly sessionId: Type.TString;
}>;
export declare const CommandResultSchema: Type.TUnion<[Type.TObject<{
    readonly command: Type.TLiteral<"list">;
    readonly sessions: Type.TArray<Type.TObject<{
        readonly id: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TOptional<Type.TInteger>;
        readonly parentSessionId: Type.TOptional<Type.TString>;
        readonly sessionName: Type.TOptional<Type.TString>;
        readonly cwd: Type.TOptional<Type.TString>;
    }>>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"create">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"attach">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"detach">;
    readonly sessionId: Type.TString;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"prompt">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"steer">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"abort">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"set_model">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly command: Type.TLiteral<"set_thinking">;
    readonly session: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>]>;
export type CommandResult = Static<typeof CommandResultSchema>;
export type ResultForCommand<TCommand extends Command> = TCommand["command"] extends "list" ? Static<typeof ListResultSchema> : TCommand["command"] extends "detach" ? Static<typeof DetachResultSchema> : Extract<CommandResult, {
    command: TCommand["command"];
}>;
/** Must be the first frame sent by a client. Version is intentionally an integer, not a coercible string. */
export declare const ClientHelloSchema: Type.TObject<{
    readonly type: Type.TLiteral<"hello">;
    readonly version: Type.TInteger;
}>;
export type ClientHello = Static<typeof ClientHelloSchema>;
export declare const RequestEnvelopeSchema: Type.TObject<{
    readonly type: Type.TLiteral<"request">;
    readonly id: Type.TString;
    readonly request: Type.TUnion<[Type.TObject<{
        readonly command: Type.TLiteral<"list">;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"create">;
        readonly cwd: Type.TOptional<Type.TString>;
        readonly name: Type.TOptional<Type.TString>;
        readonly model: Type.TOptional<Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>>;
        readonly thinkingLevel: Type.TOptional<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"attach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"detach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly sessionId: Type.TString;
        readonly text: Type.TString;
        readonly command: Type.TLiteral<"prompt">;
    }>, Type.TObject<{
        readonly sessionId: Type.TString;
        readonly text: Type.TString;
        readonly command: Type.TLiteral<"steer">;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"abort">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_model">;
        readonly sessionId: Type.TString;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_thinking">;
        readonly sessionId: Type.TString;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
    }>]>;
}>;
export type RequestEnvelope = Static<typeof RequestEnvelopeSchema>;
export declare const ClientMessageSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"hello">;
    readonly version: Type.TInteger;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"request">;
    readonly id: Type.TString;
    readonly request: Type.TUnion<[Type.TObject<{
        readonly command: Type.TLiteral<"list">;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"create">;
        readonly cwd: Type.TOptional<Type.TString>;
        readonly name: Type.TOptional<Type.TString>;
        readonly model: Type.TOptional<Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>>;
        readonly thinkingLevel: Type.TOptional<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"attach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"detach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly sessionId: Type.TString;
        readonly text: Type.TString;
        readonly command: Type.TLiteral<"prompt">;
    }>, Type.TObject<{
        readonly sessionId: Type.TString;
        readonly text: Type.TString;
        readonly command: Type.TLiteral<"steer">;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"abort">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_model">;
        readonly sessionId: Type.TString;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_thinking">;
        readonly sessionId: Type.TString;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
    }>]>;
}>]>;
export type ClientMessage = Static<typeof ClientMessageSchema>;
export declare const ServerEventSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"server_snapshot">;
    readonly snapshot: Type.TObject<{
        readonly serverId: Type.TString;
        readonly protocolVersion: Type.TLiteral<1>;
        readonly revision: Type.TInteger;
        readonly sessions: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TOptional<Type.TInteger>;
            readonly parentSessionId: Type.TOptional<Type.TString>;
            readonly sessionName: Type.TOptional<Type.TString>;
            readonly cwd: Type.TOptional<Type.TString>;
        }>>;
        readonly models: Type.TArray<Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
            readonly name: Type.TString;
            readonly api: Type.TString;
            readonly reasoning: Type.TBoolean;
            readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
            readonly contextWindow: Type.TInteger;
            readonly maxTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
            }>;
            readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
            readonly authenticated: Type.TBoolean;
        }>>;
    }>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"session_snapshot">;
    readonly snapshot: Type.TObject<{
        readonly id: Type.TString;
        readonly name: Type.TOptional<Type.TString>;
        readonly cwd: Type.TString;
        readonly createdAt: Type.TInteger;
        readonly updatedAt: Type.TInteger;
        readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
        readonly model: Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
        }>;
        readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
        readonly attached: Type.TBoolean;
        readonly locked: Type.TBoolean;
        readonly revision: Type.TInteger;
        readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>>;
        readonly queuedSteer: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>>;
        readonly queuedSteerCount: Type.TInteger;
    }>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"session_progress">;
    readonly sessionId: Type.TString;
    readonly progress: Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"item_started">;
        readonly item: Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"user">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly timestamp: Type.TInteger;
        }>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"assistant_delta">;
        readonly messageId: Type.TString;
        readonly contentIndex: Type.TInteger;
        readonly kind: Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"thinking">, Type.TLiteral<"toolCall">]>;
        readonly delta: Type.TString;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"item_updated">;
        readonly item: Type.TUnion<[Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"streaming">;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>]>, Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"running">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>]>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"item_finished">;
        readonly item: Type.TUnion<[Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly stopReason: Type.TLiteral<"error">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"assistant">;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"thinking">;
                readonly thinking: Type.TString;
                readonly redacted: Type.TOptional<Type.TBoolean>;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"toolCall">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
            }>]>>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly responseModel: Type.TOptional<Type.TString>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"aborted">;
            readonly stopReason: Type.TLiteral<"aborted">;
            readonly errorMessage: Type.TOptional<Type.TString>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"complete">;
            readonly isError: Type.TLiteral<false>;
        }>, Type.TObject<{
            readonly id: Type.TString;
            readonly role: Type.TLiteral<"tool">;
            readonly toolCallId: Type.TString;
            readonly toolName: Type.TString;
            readonly input: Type.TUnsafe<JsonValue>;
            readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly type: Type.TLiteral<"text">;
                readonly text: Type.TString;
            }>, Type.TObject<{
                readonly type: Type.TLiteral<"image">;
                readonly data: Type.TString;
                readonly mimeType: Type.TString;
            }>]>>;
            readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
            readonly usage: Type.TOptional<Type.TObject<{
                readonly input: Type.TInteger;
                readonly output: Type.TInteger;
                readonly cacheRead: Type.TInteger;
                readonly cacheWrite: Type.TInteger;
                readonly reasoning: Type.TOptional<Type.TInteger>;
                readonly totalTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                    readonly total: Type.TNumber;
                }>;
            }>>;
            readonly timestamp: Type.TInteger;
            readonly status: Type.TLiteral<"error">;
            readonly isError: Type.TLiteral<true>;
        }>]>;
    }>]>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"session_removed">;
    readonly sessionId: Type.TString;
}>]>;
export type ServerEvent = Static<typeof ServerEventSchema>;
export declare const ServerHelloSchema: Type.TObject<{
    readonly type: Type.TLiteral<"hello">;
    readonly version: Type.TLiteral<1>;
    readonly connectionId: Type.TString;
    readonly snapshot: Type.TObject<{
        readonly serverId: Type.TString;
        readonly protocolVersion: Type.TLiteral<1>;
        readonly revision: Type.TInteger;
        readonly sessions: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TOptional<Type.TInteger>;
            readonly parentSessionId: Type.TOptional<Type.TString>;
            readonly sessionName: Type.TOptional<Type.TString>;
            readonly cwd: Type.TOptional<Type.TString>;
        }>>;
        readonly models: Type.TArray<Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
            readonly name: Type.TString;
            readonly api: Type.TString;
            readonly reasoning: Type.TBoolean;
            readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
            readonly contextWindow: Type.TInteger;
            readonly maxTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
            }>;
            readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
            readonly authenticated: Type.TBoolean;
        }>>;
    }>;
}>;
export declare const ServerHelloErrorSchema: Type.TObject<{
    readonly type: Type.TLiteral<"hello_error">;
    readonly error: Type.TObject<{
        readonly code: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
        readonly message: Type.TString;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    }>;
}>;
export declare const ResponseEnvelopeSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"response">;
    readonly id: Type.TString;
    readonly ok: Type.TLiteral<true>;
    readonly result: Type.TUnion<[Type.TObject<{
        readonly command: Type.TLiteral<"list">;
        readonly sessions: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TOptional<Type.TInteger>;
            readonly parentSessionId: Type.TOptional<Type.TString>;
            readonly sessionName: Type.TOptional<Type.TString>;
            readonly cwd: Type.TOptional<Type.TString>;
        }>>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"create">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"attach">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"detach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"prompt">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"steer">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"abort">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_model">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_thinking">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>]>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"response">;
    readonly id: Type.TString;
    readonly ok: Type.TLiteral<false>;
    readonly error: Type.TObject<{
        readonly code: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
        readonly message: Type.TString;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    }>;
}>]>;
export declare const EventEnvelopeSchema: Type.TObject<{
    readonly type: Type.TLiteral<"event">;
    readonly event: Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"server_snapshot">;
        readonly snapshot: Type.TObject<{
            readonly serverId: Type.TString;
            readonly protocolVersion: Type.TLiteral<1>;
            readonly revision: Type.TInteger;
            readonly sessions: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly createdAt: Type.TInteger;
                readonly updatedAt: Type.TOptional<Type.TInteger>;
                readonly parentSessionId: Type.TOptional<Type.TString>;
                readonly sessionName: Type.TOptional<Type.TString>;
                readonly cwd: Type.TOptional<Type.TString>;
            }>>;
            readonly models: Type.TArray<Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
                readonly name: Type.TString;
                readonly api: Type.TString;
                readonly reasoning: Type.TBoolean;
                readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
                readonly contextWindow: Type.TInteger;
                readonly maxTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                }>;
                readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
                readonly authenticated: Type.TBoolean;
            }>>;
        }>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_snapshot">;
        readonly snapshot: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_progress">;
        readonly sessionId: Type.TString;
        readonly progress: Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"item_started">;
            readonly item: Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"assistant_delta">;
            readonly messageId: Type.TString;
            readonly contentIndex: Type.TInteger;
            readonly kind: Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"thinking">, Type.TLiteral<"toolCall">]>;
            readonly delta: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"item_updated">;
            readonly item: Type.TUnion<[Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"item_finished">;
            readonly item: Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>;
        }>]>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_removed">;
        readonly sessionId: Type.TString;
    }>]>;
}>;
export declare const ServerMessageSchema: Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"hello">;
    readonly version: Type.TLiteral<1>;
    readonly connectionId: Type.TString;
    readonly snapshot: Type.TObject<{
        readonly serverId: Type.TString;
        readonly protocolVersion: Type.TLiteral<1>;
        readonly revision: Type.TInteger;
        readonly sessions: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TOptional<Type.TInteger>;
            readonly parentSessionId: Type.TOptional<Type.TString>;
            readonly sessionName: Type.TOptional<Type.TString>;
            readonly cwd: Type.TOptional<Type.TString>;
        }>>;
        readonly models: Type.TArray<Type.TObject<{
            readonly provider: Type.TString;
            readonly id: Type.TString;
            readonly name: Type.TString;
            readonly api: Type.TString;
            readonly reasoning: Type.TBoolean;
            readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
            readonly contextWindow: Type.TInteger;
            readonly maxTokens: Type.TInteger;
            readonly cost: Type.TObject<{
                readonly input: Type.TNumber;
                readonly output: Type.TNumber;
                readonly cacheRead: Type.TNumber;
                readonly cacheWrite: Type.TNumber;
            }>;
            readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
            readonly authenticated: Type.TBoolean;
        }>>;
    }>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"hello_error">;
    readonly error: Type.TObject<{
        readonly code: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
        readonly message: Type.TString;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    }>;
}>, Type.TUnion<[Type.TObject<{
    readonly type: Type.TLiteral<"response">;
    readonly id: Type.TString;
    readonly ok: Type.TLiteral<true>;
    readonly result: Type.TUnion<[Type.TObject<{
        readonly command: Type.TLiteral<"list">;
        readonly sessions: Type.TArray<Type.TObject<{
            readonly id: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TOptional<Type.TInteger>;
            readonly parentSessionId: Type.TOptional<Type.TString>;
            readonly sessionName: Type.TOptional<Type.TString>;
            readonly cwd: Type.TOptional<Type.TString>;
        }>>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"create">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"attach">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"detach">;
        readonly sessionId: Type.TString;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"prompt">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"steer">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"abort">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_model">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly command: Type.TLiteral<"set_thinking">;
        readonly session: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>]>;
}>, Type.TObject<{
    readonly type: Type.TLiteral<"response">;
    readonly id: Type.TString;
    readonly ok: Type.TLiteral<false>;
    readonly error: Type.TObject<{
        readonly code: Type.TUnion<[Type.TLiteral<"version">, Type.TLiteral<"busy">, Type.TLiteral<"session_locked">, Type.TLiteral<"not_found">, Type.TLiteral<"invalid_request">, Type.TLiteral<"not_implemented">, Type.TLiteral<"internal_error">]>;
        readonly message: Type.TString;
        readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
    }>;
}>]>, Type.TObject<{
    readonly type: Type.TLiteral<"event">;
    readonly event: Type.TUnion<[Type.TObject<{
        readonly type: Type.TLiteral<"server_snapshot">;
        readonly snapshot: Type.TObject<{
            readonly serverId: Type.TString;
            readonly protocolVersion: Type.TLiteral<1>;
            readonly revision: Type.TInteger;
            readonly sessions: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly createdAt: Type.TInteger;
                readonly updatedAt: Type.TOptional<Type.TInteger>;
                readonly parentSessionId: Type.TOptional<Type.TString>;
                readonly sessionName: Type.TOptional<Type.TString>;
                readonly cwd: Type.TOptional<Type.TString>;
            }>>;
            readonly models: Type.TArray<Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
                readonly name: Type.TString;
                readonly api: Type.TString;
                readonly reasoning: Type.TBoolean;
                readonly input: Type.TArray<Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"image">]>>;
                readonly contextWindow: Type.TInteger;
                readonly maxTokens: Type.TInteger;
                readonly cost: Type.TObject<{
                    readonly input: Type.TNumber;
                    readonly output: Type.TNumber;
                    readonly cacheRead: Type.TNumber;
                    readonly cacheWrite: Type.TNumber;
                }>;
                readonly supportedThinkingLevels: Type.TArray<Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>>;
                readonly authenticated: Type.TBoolean;
            }>>;
        }>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_snapshot">;
        readonly snapshot: Type.TObject<{
            readonly id: Type.TString;
            readonly name: Type.TOptional<Type.TString>;
            readonly cwd: Type.TString;
            readonly createdAt: Type.TInteger;
            readonly updatedAt: Type.TInteger;
            readonly phase: Type.TUnion<[Type.TLiteral<"idle">, Type.TLiteral<"turn">, Type.TLiteral<"compaction">, Type.TLiteral<"branch_summary">, Type.TLiteral<"retry">]>;
            readonly model: Type.TObject<{
                readonly provider: Type.TString;
                readonly id: Type.TString;
            }>;
            readonly thinkingLevel: Type.TUnion<[Type.TLiteral<"off">, Type.TLiteral<"minimal">, Type.TLiteral<"low">, Type.TLiteral<"medium">, Type.TLiteral<"high">, Type.TLiteral<"xhigh">, Type.TLiteral<"max">]>;
            readonly attached: Type.TBoolean;
            readonly locked: Type.TBoolean;
            readonly revision: Type.TInteger;
            readonly transcript: Type.TArray<Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>>;
            readonly queuedSteer: Type.TArray<Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>>;
            readonly queuedSteerCount: Type.TInteger;
        }>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_progress">;
        readonly sessionId: Type.TString;
        readonly progress: Type.TUnion<[Type.TObject<{
            readonly type: Type.TLiteral<"item_started">;
            readonly item: Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"user">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly timestamp: Type.TInteger;
            }>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"assistant_delta">;
            readonly messageId: Type.TString;
            readonly contentIndex: Type.TInteger;
            readonly kind: Type.TUnion<[Type.TLiteral<"text">, Type.TLiteral<"thinking">, Type.TLiteral<"toolCall">]>;
            readonly delta: Type.TString;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"item_updated">;
            readonly item: Type.TUnion<[Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"streaming">;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>]>, Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"running">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>]>;
        }>, Type.TObject<{
            readonly type: Type.TLiteral<"item_finished">;
            readonly item: Type.TUnion<[Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly stopReason: Type.TUnion<[Type.TLiteral<"stop">, Type.TLiteral<"length">, Type.TLiteral<"toolUse">]>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly stopReason: Type.TLiteral<"error">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"assistant">;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"thinking">;
                    readonly thinking: Type.TString;
                    readonly redacted: Type.TOptional<Type.TBoolean>;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"toolCall">;
                    readonly toolCallId: Type.TString;
                    readonly toolName: Type.TString;
                    readonly input: Type.TUnsafe<JsonValue>;
                }>]>>;
                readonly model: Type.TObject<{
                    readonly provider: Type.TString;
                    readonly id: Type.TString;
                }>;
                readonly responseModel: Type.TOptional<Type.TString>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"aborted">;
                readonly stopReason: Type.TLiteral<"aborted">;
                readonly errorMessage: Type.TOptional<Type.TString>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"complete">;
                readonly isError: Type.TLiteral<false>;
            }>, Type.TObject<{
                readonly id: Type.TString;
                readonly role: Type.TLiteral<"tool">;
                readonly toolCallId: Type.TString;
                readonly toolName: Type.TString;
                readonly input: Type.TUnsafe<JsonValue>;
                readonly content: Type.TArray<Type.TUnion<[Type.TObject<{
                    readonly type: Type.TLiteral<"text">;
                    readonly text: Type.TString;
                }>, Type.TObject<{
                    readonly type: Type.TLiteral<"image">;
                    readonly data: Type.TString;
                    readonly mimeType: Type.TString;
                }>]>>;
                readonly details: Type.TOptional<Type.TUnsafe<JsonValue>>;
                readonly usage: Type.TOptional<Type.TObject<{
                    readonly input: Type.TInteger;
                    readonly output: Type.TInteger;
                    readonly cacheRead: Type.TInteger;
                    readonly cacheWrite: Type.TInteger;
                    readonly reasoning: Type.TOptional<Type.TInteger>;
                    readonly totalTokens: Type.TInteger;
                    readonly cost: Type.TObject<{
                        readonly input: Type.TNumber;
                        readonly output: Type.TNumber;
                        readonly cacheRead: Type.TNumber;
                        readonly cacheWrite: Type.TNumber;
                        readonly total: Type.TNumber;
                    }>;
                }>>;
                readonly timestamp: Type.TInteger;
                readonly status: Type.TLiteral<"error">;
                readonly isError: Type.TLiteral<true>;
            }>]>;
        }>]>;
    }>, Type.TObject<{
        readonly type: Type.TLiteral<"session_removed">;
        readonly sessionId: Type.TString;
    }>]>;
}>]>;
export type ServerHello = Static<typeof ServerHelloSchema>;
export type ServerHelloError = Static<typeof ServerHelloErrorSchema>;
export type ResponseEnvelope = Static<typeof ResponseEnvelopeSchema>;
export type EventEnvelope = Static<typeof EventEnvelopeSchema>;
export type ServerMessage = Static<typeof ServerMessageSchema>;
//# sourceMappingURL=schemas.d.ts.map