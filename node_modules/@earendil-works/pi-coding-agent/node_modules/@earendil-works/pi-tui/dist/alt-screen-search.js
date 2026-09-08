import { Input } from "./components/input.js";
import { getGraphemeSegmenter, stripTerminalSequences, truncateToWidth, visibleWidth } from "./utils.js";
const segmenter = getGraphemeSegmenter();
function appendMappedText(text, span, corpus) {
    corpus.text += text;
    for (let index = 0; index < text.length; index++)
        corpus.source.push(span);
}
function buildSearchCorpus(lines) {
    const corpus = { text: "", source: [] };
    let pendingSeparator = false;
    for (let row = 0; row < lines.length; row++) {
        const line = stripTerminalSequences(lines[row] ?? "");
        let column = 0;
        for (const grapheme of segmenter.segment(line)) {
            const text = grapheme.segment;
            const width = visibleWidth(text);
            if (/^\s+$/u.test(text)) {
                if (corpus.text.length > 0)
                    pendingSeparator = true;
                column += width;
                continue;
            }
            if (pendingSeparator) {
                appendMappedText(" ", undefined, corpus);
                pendingSeparator = false;
            }
            appendMappedText(text, { row, startCol: column, endCol: column + width }, corpus);
            column += width;
        }
        if (corpus.text.length > 0)
            pendingSeparator = true;
    }
    return corpus;
}
function normalizeQuery(query) {
    return query.replace(/\s+/gu, " ").trim();
}
function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
export function findAltScreenSearchMatches(lines, query) {
    const normalizedQuery = normalizeQuery(query);
    if (!normalizedQuery)
        return [];
    const corpus = buildSearchCorpus(lines);
    const expression = new RegExp(escapeRegExp(normalizedQuery), "giu");
    const matches = [];
    for (const match of corpus.text.matchAll(expression)) {
        const start = match.index;
        const end = start + match[0].length;
        const segments = [];
        for (let index = start; index < end; index++) {
            const span = corpus.source[index];
            if (!span)
                continue;
            const previous = segments[segments.length - 1];
            if (previous && previous.row === span.row && span.startCol <= previous.endCol) {
                previous.endCol = Math.max(previous.endCol, span.endCol);
            }
            else {
                segments.push({ ...span });
            }
        }
        if (segments.length > 0)
            matches.push({ segments });
    }
    return matches;
}
export function getAltScreenSearchMatchKey(match) {
    const first = match.segments[0];
    const last = match.segments[match.segments.length - 1];
    return first && last ? `${first.row}:${first.startCol}:${last.row}:${last.endCol}` : "";
}
export class AltScreenSearchComponent {
    input = new Input();
    onQueryChange;
    resultCount = 0;
    resultIndex = -1;
    _focused = false;
    constructor(onQueryChange) {
        this.onQueryChange = onQueryChange;
    }
    get focused() {
        return this._focused;
    }
    set focused(value) {
        this._focused = value;
        this.input.focused = value;
    }
    setResult(index, count) {
        this.resultIndex = index;
        this.resultCount = count;
    }
    handleInput(data) {
        const previous = this.input.getValue();
        this.input.handleInput(data);
        const query = this.input.getValue();
        if (query !== previous)
            this.onQueryChange(query);
    }
    invalidate() {
        this.input.invalidate();
    }
    render(width) {
        const safeWidth = Math.max(1, width);
        const label = " Find transcript";
        const query = this.input.getValue();
        const status = !query
            ? ""
            : this.resultCount === 0
                ? "No matches "
                : `${this.resultIndex + 1}/${this.resultCount} `;
        const labelWidth = visibleWidth(label);
        const statusWidth = visibleWidth(status);
        const gap = " ".repeat(Math.max(1, safeWidth - labelWidth - statusWidth));
        const title = truncateToWidth(`${label}${gap}${status}`, safeWidth, "");
        const padding = " ".repeat(Math.max(0, safeWidth - visibleWidth(title)));
        return [`\x1b[7m${title}${padding}\x1b[27m`, ...this.input.render(safeWidth)];
    }
}
//# sourceMappingURL=alt-screen-search.js.map