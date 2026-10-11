"use client";

import { useMemo, useState } from "react";

type Sheet = { name: string; rows: string[][] };
type Book = {
  as_of: string;
  later_note: string;
  sheets: Sheet[];
};

export function SheetView({ book }: { book: Book }) {
  const [index, setIndex] = useState(0);
  const sheet = book.sheets[index];
  const width = useMemo(
    () => Math.max(...sheet.rows.map((row) => row.length), 1),
    [sheet],
  );

  return (
    <>
      <p>{book.later_note}</p>
      <div className="sheet-tabs" role="tablist" aria-label="시트">
        {book.sheets.map((item, i) => (
          <button key={item.name} type="button" aria-pressed={i === index} onClick={() => setIndex(i)}>
            {item.name}
          </button>
        ))}
      </div>
      <p>
        {sheet.name} · {sheet.rows.length}행 · 기준 {book.as_of}
      </p>
      <div className="table-wrap sheet-scroll">
        <table>
          <tbody>
            {sheet.rows.map((row, r) => (
              <tr key={`${sheet.name}-${r}`}>
                {Array.from({ length: width }, (_, c) => {
                  const value = row[c] ?? "";
                  if (r === 0) return <th key={c}>{value}</th>;
                  return <td key={c}>{value}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
