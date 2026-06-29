"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Celebrate } from "@/components/ui/celebrate";
import { cn } from "@/lib/utils";
import type { EngineDataMap } from "@/types/engines";
import type { PlayProps } from "../types";
import { buildCrossword } from "./gridgen";

type CrosswordData = EngineDataMap["crossword"];

const keyOf = (r: number, c: number) => `${r},${c}`;
const norm = (s: string) => s.trim().toLocaleUpperCase("uz");

export function CrosswordPlay({ data, onFinish }: PlayProps<CrosswordData>) {
  const layout = useMemo(() => buildCrossword(data.words ?? []), [data.words]);
  const cellMap = useMemo(() => {
    const m = new Map<string, (typeof layout.cells)[number]>();
    layout.cells.forEach((cell) => m.set(keyOf(cell.row, cell.col), cell));
    return m;
  }, [layout]);

  const [entries, setEntries] = useState<Record<string, string>>({});
  const [checked, setChecked] = useState(false);

  if (layout.cells.length === 0) {
    return <p className="text-muted-foreground">So'zlar yo'q.</p>;
  }

  const isCorrect = (key: string, solution: string) =>
    norm(entries[key] ?? "") === solution;
  const allCorrect = layout.cells.every((c) =>
    isCorrect(keyOf(c.row, c.col), c.solution)
  );

  function setCell(key: string, value: string) {
    const ch = value.slice(-1);
    setEntries((prev) => ({ ...prev, [key]: ch }));
    setChecked(false);
  }

  function check() {
    setChecked(true);
    if (allCorrect) onFinish?.(layout.cells.length * 20);
  }

  return (
    <div className="space-y-5">
      <div className="overflow-x-auto">
        <div
          className="grid gap-0.5"
          style={{
            gridTemplateColumns: `repeat(${layout.cols}, minmax(0, 1fr))`,
            maxWidth: layout.cols * 42,
          }}
        >
          {Array.from({ length: layout.rows * layout.cols }).map((_, idx) => {
            const r = Math.floor(idx / layout.cols);
            const c = idx % layout.cols;
            const key = keyOf(r, c);
            const cell = cellMap.get(key);
            if (!cell) return <div key={key} className="h-10 w-10" />;
            const right = isCorrect(key, cell.solution);
            return (
              <div key={key} className="relative">
                {cell.number && (
                  <span className="pointer-events-none absolute left-0.5 top-0 z-10 text-[9px] font-bold text-muted-foreground">
                    {cell.number}
                  </span>
                )}
                <input
                  value={entries[key] ?? ""}
                  onChange={(e) => setCell(key, e.target.value)}
                  maxLength={1}
                  className={cn(
                    "h-10 w-10 rounded-md border border-border bg-card text-center text-base font-bold uppercase focus:border-primary focus:outline-none",
                    checked &&
                      (right
                        ? "border-success bg-success/10"
                        : "border-destructive bg-destructive/10")
                  )}
                />
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <ClueList title="Gorizontal" clues={layout.across} />
        <ClueList title="Vertikal" clues={layout.down} />
      </div>

      {allCorrect ? (
        <Celebrate title="Krossvord yechildi! 🎉" />
      ) : (
        <div className="flex justify-end">
          <Button onClick={check}>Tekshirish</Button>
        </div>
      )}
    </div>
  );
}

function ClueList({
  title,
  clues,
}: {
  title: string;
  clues: { number: number; clue: string }[];
}) {
  if (clues.length === 0) return null;
  return (
    <Card>
      <CardContent className="space-y-1.5 pt-4">
        <p className="font-display text-sm font-bold">{title}</p>
        <ul className="space-y-1 text-sm">
          {clues.map((cl) => (
            <li key={`${title}-${cl.number}`} className="flex gap-2">
              <span className="font-semibold text-primary">{cl.number}.</span>
              <span>{cl.clue}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
