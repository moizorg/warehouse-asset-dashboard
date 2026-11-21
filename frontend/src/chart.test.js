import { describe, expect, it } from "vitest";
import { buildDistribution } from "./chart";

describe("buildDistribution", () => {
  it("counts categories and returns the most common categories first", () => {
    expect(buildDistribution([
      { category: "Tools" },
      { category: "Machinery" },
      { category: "Tools" },
    ])).toEqual([
      { category: "Tools", count: 2 },
      { category: "Machinery", count: 1 },
    ]);
  });
});
