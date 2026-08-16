import { describe, it, expect } from "vitest";
import { computeTextDiff } from "./text-diff";

const LAB_PAGE = [
  "Ho Dinh Dat, Glucose, 107.0, mg/dL",
  "Ho Dinh Dat, HbA1c, 6.5, %",
  "Ho Dinh Dat, Potassium, 4.4, mmol/L",
].join("\n");

describe("computeTextDiff", () => {
  it("detects a changed numeric value within a lab line", () => {
    const corrected = LAB_PAGE.replace("107.0", "104.0");
    const { rows, stats } = computeTextDiff(LAB_PAGE, corrected);

    expect(stats.modifiedLines).toBe(1);
    expect(stats.addedLines).toBe(0);
    expect(stats.removedLines).toBe(0);

    const modifiedRow = rows.find((row) => row.type === "modified");
    expect(modifiedRow).toBeDefined();
    if (modifiedRow?.type !== "modified") return;

    const changedLeft = modifiedRow.leftParts.filter((part) => part.changed);
    const changedRight = modifiedRow.rightParts.filter((part) => part.changed);
    expect(changedLeft.map((part) => part.value).join("")).toBe("107.0");
    expect(changedRight.map((part) => part.value).join("")).toBe("104.0");
  });

  it("keeps unchanged lines as equal rows with stable line numbers", () => {
    const corrected = LAB_PAGE.replace("6.5", "6.3");
    const { rows } = computeTextDiff(LAB_PAGE, corrected);

    const equalRows = rows.filter((row) => row.type === "equal");
    expect(equalRows).toHaveLength(2);
    for (const row of equalRows) {
      if (row.type !== "equal") continue;
      expect(row.left).toBe(row.right);
      expect(row.leftNumber).toBe(row.rightNumber);
    }
  });

  it("classifies added and removed lines separately from modified ones", () => {
    const original = ["line one", "line two", "line three", "extra", "anchor"].join("\n");
    const corrected = ["line one", "line 2 changed", "line three", "anchor", "tail"].join("\n");

    const { rows, stats } = computeTextDiff(original, corrected);
    expect(stats.modifiedLines).toBe(1);
    expect(stats.removedLines).toBe(1);
    expect(stats.addedLines).toBe(1);
    expect(rows.filter((row) => row.type === "removed")[0]).toMatchObject({
      left: "extra",
      leftNumber: 4,
    });
    expect(rows.filter((row) => row.type === "added")[0]).toMatchObject({
      right: "tail",
      rightNumber: 5,
    });
    expect(rows.filter((row) => row.type === "modified")[0]).toMatchObject({
      left: "line two",
      right: "line 2 changed",
    });
  });

  it("returns all equal rows and full similarity for identical texts", () => {
    const { rows, stats } = computeTextDiff(LAB_PAGE, LAB_PAGE);
    expect(rows).toHaveLength(3);
    expect(rows.every((row) => row.type === "equal")).toBe(true);
    expect(stats.similarity).toBe(1);
    expect(stats.addedLines + stats.removedLines + stats.modifiedLines).toBe(0);
  });

  it("normalizes carriage returns before comparing", () => {
    const original = "alpha\r\nbeta\r\n";
    const corrected = "alpha\nbeta\n";
    const { stats } = computeTextDiff(original, corrected);
    expect(stats.addedLines + stats.removedLines + stats.modifiedLines).toBe(0);
  });

  it("does not flag whitespace-only differences inside a modified line", () => {
    const { rows } = computeTextDiff("Glucose 107.0", "Glucose  107.0");
    const modifiedRow = rows.find((row) => row.type === "modified");
    if (modifiedRow?.type !== "modified") throw new Error("expected a modified row");
    expect(modifiedRow.leftParts.some((part) => part.changed)).toBe(false);
    expect(modifiedRow.rightParts.some((part) => part.changed)).toBe(false);
  });

  it("computes a char-level similarity ratio", () => {
    const corrected = LAB_PAGE.replace("107.0", "104.0");
    const { stats } = computeTextDiff(LAB_PAGE, corrected);
    expect(stats.similarity).toBeGreaterThan(0.85);
    expect(stats.similarity).toBeLessThan(1);
  });

  it("handles empty original text as a full addition", () => {
    const { rows, stats } = computeTextDiff("", "new line");
    expect(stats.addedLines).toBeGreaterThanOrEqual(1);
    expect(rows.some((row) => row.type === "added")).toBe(true);
  });

  it("falls back to whole-line emphasis when a line exceeds the word-diff budget", () => {
    const token = "word ";
    const hugeLeft = token.repeat(600).trim();
    const hugeRight = (token + "changed ").repeat(600).trim();
    const { rows } = computeTextDiff(hugeLeft, hugeRight);

    const modifiedRow = rows.find((row) => row.type === "modified");
    if (modifiedRow?.type !== "modified") throw new Error("expected a modified row");
    expect(modifiedRow.leftParts).toEqual([{ value: hugeLeft, changed: true }]);
    expect(modifiedRow.rightParts).toEqual([{ value: hugeRight, changed: true }]);
  });
});
