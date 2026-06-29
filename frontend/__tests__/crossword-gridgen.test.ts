import { describe, expect, it } from "vitest";

import { buildCrossword } from "@/components/engines/Crossword/gridgen";

const SCIENCE = [
  { word: "ATOM", clue: "Moddaning eng kichik bo'lagi" },
  { word: "MOLEKULA", clue: "Atomlar birikmasi" },
  { word: "ION", clue: "Zaryadlangan zarra" },
];

describe("buildCrossword", () => {
  it("places every word and interlocks (some go down)", () => {
    const layout = buildCrossword(SCIENCE);
    expect(layout.placedCount).toBe(3);
    expect(layout.across.length + layout.down.length).toBe(3);
    // Kamida bitta so'z vertikal joylashgan bo'lishi kerak (kesishuv bor).
    expect(layout.down.length).toBeGreaterThan(0);
  });

  it("normalizes coordinates to non-negative", () => {
    const layout = buildCrossword(SCIENCE);
    for (const cell of layout.cells) {
      expect(cell.row).toBeGreaterThanOrEqual(0);
      expect(cell.col).toBeGreaterThanOrEqual(0);
    }
    expect(layout.rows).toBeGreaterThan(0);
    expect(layout.cols).toBeGreaterThan(0);
  });

  it("never assigns conflicting letters to the same cell", () => {
    const layout = buildCrossword(SCIENCE);
    const seen = new Map<string, string>();
    for (const cell of layout.cells) {
      const k = `${cell.row},${cell.col}`;
      if (seen.has(k)) expect(seen.get(k)).toBe(cell.solution);
      seen.set(k, cell.solution);
    }
  });

  it("every clue number maps to a numbered start cell", () => {
    const layout = buildCrossword(SCIENCE);
    const numbered = new Set(
      layout.cells.filter((c) => c.number).map((c) => c.number)
    );
    for (const cl of [...layout.across, ...layout.down]) {
      expect(numbered.has(cl.number)).toBe(true);
    }
  });

  it("handles empty / blank input gracefully", () => {
    expect(buildCrossword([]).cells).toHaveLength(0);
    expect(buildCrossword([{ word: "  ", clue: "x" }]).cells).toHaveLength(0);
  });
});
