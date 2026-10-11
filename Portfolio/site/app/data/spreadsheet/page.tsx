import fs from "fs";
import path from "path";
import { Shell } from "@/components/Shell";
import { SheetView } from "./SheetView";

type Book = {
  title: string;
  source_file: string;
  as_of: string;
  baseline_commit: string;
  later_note: string;
  sheets: { name: string; rows: string[][] }[];
};

export default function SpreadsheetPage() {
  const file = path.join(process.cwd(), "..", "assets", "spreadsheet.json");
  const book = JSON.parse(fs.readFileSync(file, "utf8")) as Book;

  return (
    <Shell current="/data/spreadsheet">
      <header className="page-head">
        <div className="kicker">DATA · {book.as_of}</div>
        <h1>스프레드시트</h1>
        <p className="lede">
          Scribble의 통합 시트를 열 단위로 옮겼습니다. 원본 xlsx는 Git에 없고, 이 표는 Portfolio/assets/spreadsheet.json 입니다.
          기준 커밋은 {book.baseline_commit} 입니다.
        </p>
      </header>
      <section className="section">
        <SheetView book={book} />
      </section>
    </Shell>
  );
}
