import type { Component, Focusable } from "./tui.ts";
export interface AltScreenSearchSegment {
    row: number;
    startCol: number;
    endCol: number;
}
export interface AltScreenSearchMatch {
    segments: AltScreenSearchSegment[];
}
export declare function findAltScreenSearchMatches(lines: readonly string[], query: string): AltScreenSearchMatch[];
export declare function getAltScreenSearchMatchKey(match: AltScreenSearchMatch): string;
export declare class AltScreenSearchComponent implements Component, Focusable {
    private readonly input;
    private readonly onQueryChange;
    private resultCount;
    private resultIndex;
    private _focused;
    constructor(onQueryChange: (query: string) => void);
    get focused(): boolean;
    set focused(value: boolean);
    setResult(index: number, count: number): void;
    handleInput(data: string): void;
    invalidate(): void;
    render(width: number): string[];
}
//# sourceMappingURL=alt-screen-search.d.ts.map