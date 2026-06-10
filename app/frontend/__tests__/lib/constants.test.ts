import { describe, it, expect } from "vitest";
import { NAV_ITEMS, PRODUCT_NAME, ENVIRONMENTS } from "@/lib/constants";

describe("constants", () => {
  it("NAV_ITEMS has expected entries", () => {
    expect(NAV_ITEMS.length).toBeGreaterThanOrEqual(8);
    expect(NAV_ITEMS[0].label).toBe("Dashboard");
    expect(NAV_ITEMS[0].href).toBe("/dashboard");
  });

  it("PRODUCT_NAME is defined", () => {
    expect(PRODUCT_NAME).toBeTruthy();
    expect(typeof PRODUCT_NAME).toBe("string");
  });

  it("ENVIRONMENTS has 4 options", () => {
    expect(ENVIRONMENTS).toHaveLength(4);
    expect(ENVIRONMENTS[0].id).toBe("synthetic");
    expect(ENVIRONMENTS[3].id).toBe("production");
  });
});
