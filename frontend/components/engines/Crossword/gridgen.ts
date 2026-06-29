// DarsPro — krossvord uchun haqiqiy o'zaro kesishuvchi (interlocking) panjara generatori.
// Kirish: {word, clue} ro'yxati. Chiqish: 2D panjara + across/down savollar.
// Backend sxemasi o'zgarmaydi — panjara render paytida hisoblanadi.

export interface CrosswordWord {
  word: string;
  clue: string;
}

export interface CrosswordCell {
  row: number;
  col: number;
  solution: string;
  number?: number; // so'z boshlanadigan katak raqami
}

export interface CrosswordClue {
  number: number;
  clue: string;
  row: number;
  col: number;
  len: number;
  dir: "across" | "down";
}

export interface CrosswordLayout {
  rows: number;
  cols: number;
  cells: CrosswordCell[];
  across: CrosswordClue[];
  down: CrosswordClue[];
  placedCount: number;
  total: number;
}

type Dir = "across" | "down";

interface Placed {
  word: string;
  clue: string;
  row: number;
  col: number;
  dir: Dir;
}

function normalize(w: string): string {
  return w.trim().toLocaleUpperCase("uz");
}

const keyOf = (r: number, c: number) => `${r},${c}`;

export function buildCrossword(input: CrosswordWord[]): CrosswordLayout {
  const words = input
    .map((w) => ({ word: normalize(w.word), clue: w.clue }))
    .filter((w) => w.word.length > 0)
    // Uzunroq so'zlar avval — ko'proq kesishuv imkoniyati.
    .sort((a, b) => b.word.length - a.word.length);

  const grid = new Map<string, string>();
  const placed: Placed[] = [];

  function canPlace(word: string, row: number, col: number, dir: Dir): boolean {
    const dr = dir === "down" ? 1 : 0;
    const dc = dir === "across" ? 1 : 0;
    // So'z boshidan oldingi va oxiridan keyingi katak bo'sh bo'lishi shart.
    if (grid.has(keyOf(row - dr, col - dc))) return false;
    if (grid.has(keyOf(row + dr * word.length, col + dc * word.length)))
      return false;

    let overlaps = 0;
    for (let i = 0; i < word.length; i++) {
      const r = row + dr * i;
      const c = col + dc * i;
      const existing = grid.get(keyOf(r, c));
      if (existing) {
        if (existing !== word[i]) return false;
        overlaps++;
      } else {
        // Kesishmaydigan kataklarda perpendikulyar qo'shnilar bo'sh bo'lsin
        // (parallel so'zlar yopishib qolmasligi uchun).
        if (dir === "across") {
          if (grid.has(keyOf(r - 1, c)) || grid.has(keyOf(r + 1, c)))
            return false;
        } else {
          if (grid.has(keyOf(r, c - 1)) || grid.has(keyOf(r, c + 1)))
            return false;
        }
      }
    }
    return overlaps > 0; // kamida bitta mavjud harf bilan kesishishi kerak
  }

  function place(p: Placed) {
    const dr = p.dir === "down" ? 1 : 0;
    const dc = p.dir === "across" ? 1 : 0;
    for (let i = 0; i < p.word.length; i++) {
      grid.set(keyOf(p.row + dr * i, p.col + dc * i), p.word[i]);
    }
    placed.push(p);
  }

  if (words.length > 0) {
    place({ ...words[0], row: 0, col: 0, dir: "across" });
  }

  for (let wi = 1; wi < words.length; wi++) {
    const { word, clue } = words[wi];
    let done = false;

    for (const p of placed) {
      const pdr = p.dir === "down" ? 1 : 0;
      const pdc = p.dir === "across" ? 1 : 0;
      for (let pi = 0; pi < p.word.length && !done; pi++) {
        const pr = p.row + pdr * pi;
        const pc = p.col + pdc * pi;
        for (let i = 0; i < word.length; i++) {
          if (word[i] !== p.word[pi]) continue;
          const dir: Dir = p.dir === "across" ? "down" : "across";
          const dr = dir === "down" ? 1 : 0;
          const dc = dir === "across" ? 1 : 0;
          const row = pr - dr * i;
          const col = pc - dc * i;
          if (canPlace(word, row, col, dir)) {
            place({ word, clue, row, col, dir });
            done = true;
            break;
          }
        }
      }
      if (done) break;
    }

    // Joylab bo'lmasa — panjara ostiga alohida qatorda qo'shamiz (fallback).
    if (!done) {
      let maxRow = 0;
      for (const k of grid.keys()) {
        const r = Number(k.split(",")[0]);
        if (r > maxRow) maxRow = r;
      }
      place({ word, clue, row: maxRow + 2, col: 0, dir: "across" });
    }
  }

  // Koordinatalarni 0 dan boshlanadigan qilib normallashtiramiz.
  let minR = Infinity,
    minC = Infinity,
    maxR = -Infinity,
    maxC = -Infinity;
  for (const k of grid.keys()) {
    const [r, c] = k.split(",").map(Number);
    minR = Math.min(minR, r);
    minC = Math.min(minC, c);
    maxR = Math.max(maxR, r);
    maxC = Math.max(maxC, c);
  }
  if (!isFinite(minR)) {
    return { rows: 0, cols: 0, cells: [], across: [], down: [], placedCount: 0, total: 0 };
  }

  const filled = new Map<string, string>();
  for (const [k, v] of grid.entries()) {
    const [r, c] = k.split(",").map(Number);
    filled.set(keyOf(r - minR, c - minC), v);
  }
  const rows = maxR - minR + 1;
  const cols = maxC - minC + 1;

  // Raqamlash: row-major skan; across yoki down so'z boshi → keyingi raqam.
  const numberAt = new Map<string, number>();
  let counter = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (!filled.has(keyOf(r, c))) continue;
      const startAcross =
        !filled.has(keyOf(r, c - 1)) && filled.has(keyOf(r, c + 1));
      const startDown =
        !filled.has(keyOf(r - 1, c)) && filled.has(keyOf(r + 1, c));
      if (startAcross || startDown) {
        counter += 1;
        numberAt.set(keyOf(r, c), counter);
      }
    }
  }

  const cells: CrosswordCell[] = [];
  for (const [k, v] of filled.entries()) {
    const [r, c] = k.split(",").map(Number);
    cells.push({ row: r, col: c, solution: v, number: numberAt.get(k) });
  }

  const across: CrosswordClue[] = [];
  const down: CrosswordClue[] = [];
  for (const p of placed) {
    const r = p.row - minR;
    const c = p.col - minC;
    const number = numberAt.get(keyOf(r, c)) ?? 0;
    const entry: CrosswordClue = {
      number,
      clue: p.clue,
      row: r,
      col: c,
      len: p.word.length,
      dir: p.dir,
    };
    (p.dir === "across" ? across : down).push(entry);
  }
  across.sort((a, b) => a.number - b.number);
  down.sort((a, b) => a.number - b.number);

  return {
    rows,
    cols,
    cells,
    across,
    down,
    placedCount: placed.length,
    total: words.length,
  };
}
