import { describe, expect, it } from "vitest";

import { mapBackendRole } from "./session";

describe("mapBackendRole", () => {
  it("maps canonical backend non-clinical roles without clinical fallback", () => {
    expect(mapBackendRole("records_staff")).toBe("front_desk");
    expect(mapBackendRole("security")).toBe("security");
    expect(mapBackendRole("front_desk")).toBe("front_desk");
  });
});
