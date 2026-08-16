/**
 * Pure text-diff utilities for the clinical document workspace.
 *
 * Line alignment uses LCS over lines with common prefix/suffix trimming so
 * typical OCR pages (mostly unchanged lines) stay fast. Modified line pairs
 * get a second LCS pass over word tokens to flag exactly which tokens
 * changed — lab values and drug names must be visible at a glance.
 */

export interface WordPart {
  value: string;
  changed: boolean;
}

export type DiffRow =
  | {
      type: "equal";
      leftNumber: number;
      rightNumber: number;
      left: string;
      right: string;
    }
  | {
      type: "modified";
      leftNumber: number;
      rightNumber: number;
      left: string;
      right: string;
      leftParts: WordPart[];
      rightParts: WordPart[];
    }
  | { type: "removed"; leftNumber: number; left: string }
  | { type: "added"; rightNumber: number; right: string };

export interface DiffStats {
  addedLines: number;
  removedLines: number;
  modifiedLines: number;
  /** 0..1 ratio of unchanged non-whitespace characters. */
  similarity: number;
}

interface LcsOp {
  op: "equal" | "delete" | "insert";
  aIndex: number;
  bIndex: number;
}

const MAX_LINE_CELLS = 4_000_000;
const MAX_WORD_CELLS = 250_000;

function lcsOps<T>(
  a: T[],
  b: T[],
  equals: (x: T, y: T) => boolean,
  maxCells: number,
): LcsOp[] | null {
  const n = a.length;
  const m = b.length;
  if (n * m > maxCells) return null;

  const width = m + 1;
  const dp = new Int32Array((n + 1) * width);
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i * width + j] = equals(a[i], b[j])
        ? dp[(i + 1) * width + j + 1] + 1
        : Math.max(dp[(i + 1) * width + j], dp[i * width + j + 1]);
    }
  }

  const ops: LcsOp[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (equals(a[i], b[j])) {
      ops.push({ op: "equal", aIndex: i, bIndex: j });
      i++;
      j++;
    } else if (dp[(i + 1) * width + j] >= dp[i * width + j + 1]) {
      ops.push({ op: "delete", aIndex: i, bIndex: j });
      i++;
    } else {
      ops.push({ op: "insert", aIndex: i, bIndex: j });
      j++;
    }
  }
  while (i < n) {
    ops.push({ op: "delete", aIndex: i, bIndex: j });
    i++;
  }
  while (j < m) {
    ops.push({ op: "insert", aIndex: i, bIndex: j });
    j++;
  }
  return ops;
}

function splitLines(text: string): string[] {
  return text.replace(/\r\n?/g, "\n").split("\n");
}

function diffLineOps(a: string[], b: string[]): LcsOp[] {
  let start = 0;
  while (start < a.length && start < b.length && a[start] === b[start]) start++;
  let endA = a.length;
  let endB = b.length;
  while (endA > start && endB > start && a[endA - 1] === b[endB - 1]) {
    endA--;
    endB--;
  }

  const ops: LcsOp[] = [];
  for (let k = 0; k < start; k++) {
    ops.push({ op: "equal", aIndex: k, bIndex: k });
  }

  const midOps = lcsOps(
    a.slice(start, endA),
    b.slice(start, endB),
    (x, y) => x === y,
    MAX_LINE_CELLS,
  );
  if (midOps) {
    for (const op of midOps) {
      ops.push({ op: op.op, aIndex: op.aIndex + start, bIndex: op.bIndex + start });
    }
  } else {
    // Pathological size: treat the middle as one full replace block.
    for (let k = start; k < endA; k++) {
      ops.push({ op: "delete", aIndex: k, bIndex: start });
    }
    for (let k = start; k < endB; k++) {
      ops.push({ op: "insert", aIndex: endA, bIndex: k });
    }
  }

  for (let k = endA; k < a.length; k++) {
    ops.push({ op: "equal", aIndex: k, bIndex: endB + (k - endA) });
  }
  return ops;
}

function tokenizeWords(text: string): string[] {
  // Commas and semicolons become their own tokens so "107.0," in a lab line
  // highlights as "107.0" while the punctuation stays unflagged on both sides.
  return text.split(/(\s+|,|;)/).filter((token) => token.length > 0);
}

function hasNonWhitespace(text: string): boolean {
  return /\S/.test(text);
}

function pushPart(parts: WordPart[], value: string, changed: boolean) {
  const last = parts[parts.length - 1];
  if (last && last.changed === changed) {
    last.value += value;
  } else {
    parts.push({ value, changed });
  }
}

function diffWords(left: string, right: string): { left: WordPart[]; right: WordPart[] } | null {
  const leftTokens = tokenizeWords(left);
  const rightTokens = tokenizeWords(right);
  const ops = lcsOps(leftTokens, rightTokens, (x, y) => x === y, MAX_WORD_CELLS);
  if (!ops) return null;

  const leftParts: WordPart[] = [];
  const rightParts: WordPart[] = [];
  for (const op of ops) {
    if (op.op === "equal") {
      pushPart(leftParts, leftTokens[op.aIndex], false);
      pushPart(rightParts, rightTokens[op.bIndex], false);
    } else if (op.op === "delete") {
      // Whitespace-only changes stay unflagged to keep the highlight on words.
      pushPart(leftParts, leftTokens[op.aIndex], hasNonWhitespace(leftTokens[op.aIndex]));
    } else {
      pushPart(rightParts, rightTokens[op.bIndex], hasNonWhitespace(rightTokens[op.bIndex]));
    }
  }
  return { left: leftParts, right: rightParts };
}

function nonWhitespaceChars(text: string): number {
  let count = 0;
  for (const token of text.split(/\s+/)) {
    if (token.length > 0) count += token.length;
  }
  return count;
}

function similarityRatio(original: string, corrected: string): number {
  if (original === corrected) return 1;
  const originalTokens = tokenizeWords(original);
  const correctedTokens = tokenizeWords(corrected);
  const ops = lcsOps(originalTokens, correctedTokens, (x, y) => x === y, 1_000_000);
  if (!ops) return 0;

  let equalChars = 0;
  for (const op of ops) {
    if (op.op === "equal") equalChars += nonWhitespaceChars(originalTokens[op.aIndex]);
  }
  const total = Math.max(nonWhitespaceChars(original), nonWhitespaceChars(corrected));
  if (total === 0) return 1;
  return equalChars / total;
}

export function computeTextDiff(
  original: string,
  corrected: string,
): {
  rows: DiffRow[];
  stats: DiffStats;
} {
  const originalLines = splitLines(original);
  const correctedLines = splitLines(corrected);
  const ops = diffLineOps(originalLines, correctedLines);

  const rows: DiffRow[] = [];
  let leftNumber = 0;
  let rightNumber = 0;
  let addedLines = 0;
  let removedLines = 0;
  let modifiedLines = 0;

  let i = 0;
  while (i < ops.length) {
    if (ops[i].op === "equal") {
      leftNumber++;
      rightNumber++;
      rows.push({
        type: "equal",
        leftNumber,
        rightNumber,
        left: originalLines[ops[i].aIndex],
        right: correctedLines[ops[i].bIndex],
      });
      i++;
      continue;
    }

    const deletes: number[] = [];
    const inserts: number[] = [];
    while (i < ops.length && ops[i].op !== "equal") {
      if (ops[i].op === "delete") deletes.push(ops[i].aIndex);
      else inserts.push(ops[i].bIndex);
      i++;
    }

    const pairCount = Math.min(deletes.length, inserts.length);
    let paired = 0;
    // Blank lines (e.g. the artifact of an empty side) never pair — they stay
    // pure additions/removals instead of pretending to be modifications.
    while (
      paired < pairCount &&
      originalLines[deletes[paired]].trim() !== "" &&
      correctedLines[inserts[paired]].trim() !== ""
    ) {
      paired++;
    }
    for (let k = 0; k < paired; k++) {
      leftNumber++;
      rightNumber++;
      const left = originalLines[deletes[k]];
      const right = correctedLines[inserts[k]];
      const words = diffWords(left, right);
      rows.push({
        type: "modified",
        leftNumber,
        rightNumber,
        left,
        right,
        leftParts: words ? words.left : [{ value: left, changed: true }],
        rightParts: words ? words.right : [{ value: right, changed: true }],
      });
      modifiedLines++;
    }
    for (let k = paired; k < deletes.length; k++) {
      leftNumber++;
      rows.push({ type: "removed", leftNumber, left: originalLines[deletes[k]] });
      removedLines++;
    }
    for (let k = paired; k < inserts.length; k++) {
      rightNumber++;
      rows.push({ type: "added", rightNumber, right: correctedLines[inserts[k]] });
      addedLines++;
    }
  }

  return {
    rows,
    stats: {
      addedLines,
      removedLines,
      modifiedLines,
      similarity: similarityRatio(original, corrected),
    },
  };
}
