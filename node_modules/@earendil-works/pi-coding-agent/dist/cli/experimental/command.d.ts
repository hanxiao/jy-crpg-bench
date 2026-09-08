export interface NamedCommandInvocation {
    readonly command: string;
}
export type CommandParseResult<TInvocation extends NamedCommandInvocation = NamedCommandInvocation> = {
    readonly ok: true;
    readonly command: TInvocation;
} | {
    readonly ok: false;
    readonly errors: readonly string[];
};
export type CommandExecutionResult<TInvocation extends NamedCommandInvocation = NamedCommandInvocation> = {
    readonly ok: true;
    readonly command: TInvocation;
} | {
    readonly ok: false;
    readonly errors: readonly string[];
};
export type CommandOptionParseResult<TValue> = {
    readonly ok: true;
    readonly value: TValue;
} | {
    readonly ok: false;
    readonly error: string;
};
export interface CommandOption<TValue> {
    readonly name: `--${string}`;
    parse(value: string): CommandOptionParseResult<TValue>;
}
export declare function valueOption<TValue>(name: `--${string}`, parse: (value: string) => CommandOptionParseResult<TValue>): CommandOption<TValue>;
export declare function stringOption(name: `--${string}`): CommandOption<string>;
export interface ParsedCommandInput {
    readonly remainingArgs: readonly string[];
    value<TValue>(option: CommandOption<TValue>): TValue | undefined;
    values<TValue>(option: CommandOption<TValue>): readonly TValue[];
}
export type CommandBuildResult<TInvocation extends NamedCommandInvocation> = {
    readonly ok: true;
    readonly command: TInvocation;
} | {
    readonly ok: false;
    readonly errors: readonly string[];
};
type CommandBuilder<TInvocation extends NamedCommandInvocation> = (input: ParsedCommandInput) => CommandBuildResult<TInvocation>;
type CommandAction<TInvocation extends NamedCommandInvocation, TContext> = (command: TInvocation, context: TContext) => void | Promise<void>;
export declare class Command<TOwnInvocation extends NamedCommandInvocation, TContext, TInvocation extends NamedCommandInvocation = TOwnInvocation> {
    readonly name: string;
    private readonly options;
    private readonly subcommands;
    private builder?;
    private commandAction?;
    constructor(name: string);
    option<TValue>(option: CommandOption<TValue>): this;
    build(builder: CommandBuilder<TOwnInvocation>): this;
    action(action: CommandAction<TOwnInvocation, TContext>): this;
    command<TSubcommandOwnInvocation extends NamedCommandInvocation, TSubcommandContext, TSubcommandInvocation extends NamedCommandInvocation>(command: Command<TSubcommandOwnInvocation, TSubcommandContext, TSubcommandInvocation>): Command<TOwnInvocation, TContext & TSubcommandContext, TInvocation | TSubcommandInvocation>;
    parse(argv: readonly string[]): CommandParseResult<TInvocation>;
    execute(argv: readonly string[], context: TContext): Promise<CommandExecutionResult<TInvocation>>;
    private select;
    private parseOwn;
    private parseOptions;
}
export {};
//# sourceMappingURL=command.d.ts.map