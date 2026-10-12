import fs from "fs";
import path from "path";
import { DatabaseSync } from "node:sqlite";

export const DEEP_LIMIT = 10;

type CountRow = { n: number };
type IdRow = { id: number };

let database: DatabaseSync | null = null;

function databasePath() {
  return process.env.PORTFOLIO_DEEP_DB || path.join(process.cwd(), "data", "deep_quota.sqlite");
}

function open() {
  if (database) return database;
  const file = databasePath();
  fs.mkdirSync(path.dirname(file), { recursive: true });
  database = new DatabaseSync(file);
  database.exec(`
    CREATE TABLE IF NOT EXISTS deep_uses (
      id INTEGER PRIMARY KEY,
      used_at TEXT NOT NULL,
      kst_date TEXT NOT NULL,
      status TEXT NOT NULL
    )
  `);
  return database;
}

/** 한국 시간 날짜. 오전 12시(00:00)에 날짜가 바뀌면 횟수가 초기화된다. */
export function kstDate(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

function usedOn(date: string) {
  const row = open()
    .prepare(
      "SELECT COUNT(*) AS n FROM deep_uses WHERE kst_date = ? AND status != 'refunded'",
    )
    .get(date) as CountRow;
  return Number(row?.n || 0);
}

export function deepStatus(now = new Date()) {
  const used = usedOn(kstDate(now));
  return {
    limit: DEEP_LIMIT,
    used,
    remaining: Math.max(0, DEEP_LIMIT - used),
    resets: "한국 시간 오전 12시",
  };
}

export function reserveDeep(now = new Date()) {
  const date = kstDate(now);
  const db = open();
  db.exec("BEGIN IMMEDIATE");
  try {
    const used = usedOn(date);
    if (used >= DEEP_LIMIT) {
      db.exec("ROLLBACK");
      return {
        ok: false as const,
        id: 0,
        ...deepStatus(now),
        detail: "깊이 추론은 하루에 10번까지입니다. 한국 시간 오전 12시에 초기화됩니다.",
      };
    }
    const inserted = db
      .prepare("INSERT INTO deep_uses (used_at, kst_date, status) VALUES (?, ?, 'reserved')")
      .run(now.toISOString(), date);
    db.exec("COMMIT");
    const id = Number(inserted.lastInsertRowid);
    return { ok: true as const, id, ...deepStatus(now), detail: "" };
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
}

export function finishDeep(id: number) {
  open().prepare("UPDATE deep_uses SET status = 'done' WHERE id = ? AND status = 'reserved'").run(id);
}

export function resetDeepQuotaForTests() {
  if (database) {
    database.close();
    database = null;
  }
}
