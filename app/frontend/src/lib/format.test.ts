import { describe, expect, it } from "vitest";
import { formatDate, formatDateTime, formatNumber, formatRelative, formatTime } from "./format";

describe("format helpers", () => {
  it("formats UTC dates and times without locale drift", () => {
    const iso = "2026-06-18T07:05:00.000Z";

    expect(formatDate(iso)).toBe("Jun 18, 2026");
    expect(formatTime(iso)).toBe("07:05 UTC");
    expect(formatDateTime(iso)).toBe("Jun 18, 2026 \u00b7 07:05 UTC");
  });

  it("formats relative times from a stable reference instant", () => {
    const now = Date.UTC(2026, 5, 18, 8, 0, 0);

    expect(formatRelative(Date.UTC(2026, 5, 18, 7, 59, 30), now)).toBe("just now");
    expect(formatRelative(Date.UTC(2026, 5, 18, 7, 45, 0), now)).toBe("15m ago");
    expect(formatRelative(Date.UTC(2026, 5, 18, 5, 0, 0), now)).toBe("3h ago");
    expect(formatRelative(Date.UTC(2026, 5, 16, 8, 0, 0), now)).toBe("2d ago");
  });

  it("formats numbers with US grouping", () => {
    expect(formatNumber(1234567)).toBe("1,234,567");
  });
});
