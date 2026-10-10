/**
 * 회원 관리 — `GET /api/v1/console/users`.
 *
 * 검색(아이디·이메일) · 잠금 해제 · 모든 기기 로그아웃 · 계정 삭제.
 * 삭제는 되돌릴 수 없어 아이디를 다시 입력해야 한다. 회원의 작업·배치·영상과 파일이 함께 지워지고,
 * 학습 데이터(검수 문장)는 계정 연결만 끊긴다. 관리자 계정은 지울 수 없다.
 */
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Lock, LogOut, Search, Shield, Trash2, Unlock } from "lucide-react";
import { deleteUser, errorMessage, fetchUsers, revokeUserSessions, unlockUser } from "../api/client";
import { StatCard } from "../components/StatCard";
import type { ConsoleUser } from "../types";

const PAGE = 50;

const when = (iso: string | null) => (iso ? new Date(iso).toLocaleString("ko-KR") : "-");

export function UsersPage() {
  const [rows, setRows] = useState<ConsoleUser[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [applied, setApplied] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  // 삭제 확인 중인 회원 + 다시 입력한 아이디
  const [deleting, setDeleting] = useState<ConsoleUser | null>(null);
  const [confirm, setConfirm] = useState("");

  const load = useCallback(async () => {
    try {
      const body = await fetchUsers(applied, PAGE, offset);
      setRows(body.items);
      setTotal(body.total);
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoaded(true);
    }
  }, [applied, offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const search = (e: FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setApplied(query.trim());
  };

  const act = async (id: string, fn: () => Promise<string>) => {
    setBusy(id);
    setError(null);
    try {
      setNotice(await fn());
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  };

  const remove = async (e: FormEvent) => {
    e.preventDefault();
    if (!deleting) return;
    const target = deleting;
    await act(target.id, async () => {
      const r = await deleteUser(target.id, confirm);
      setDeleting(null);
      setConfirm("");
      return `${r.username} 삭제 — 작업 ${r.jobs} · 배치 ${r.batches} · 영상 ${r.videos} · 학습 데이터 연결 해제 ${r.learning_unlinked}`;
    });
  };

  const locked = rows.filter((r) => r.locked).length;
  const online = rows.filter((r) => r.active_sessions > 0).length;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">회원 관리</h2>
        <p className="mt-1 text-sm text-console-muted">
          `GET /api/v1/console/users` — 계정·작업 수·로그인 상태. 비밀번호는 서버에도 해시로만 있어 볼 수 없습니다.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard label="전체 회원" value={total} />
        <StatCard label="로그인 중 (이 페이지)" value={online} tone="ok" />
        <StatCard label="잠김 (이 페이지)" value={locked} tone={locked ? "warn" : "default"} hint="로그인 실패가 많아 잠긴 계정" />
      </div>

      <form onSubmit={search} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="아이디 · 이메일 검색"
          aria-label="회원 검색"
          className="w-full max-w-sm rounded-lg border border-console-border bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-console-accent"
        />
        <button
          type="submit"
          className="inline-flex items-center gap-1 rounded-lg border border-console-border px-3 py-2 text-sm text-slate-200 hover:border-console-accent"
        >
          <Search className="h-4 w-4" /> 검색
        </button>
      </form>

      {notice && (
        <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-100">{notice}</div>
      )}
      {error && (
        <div role="alert" className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {deleting && (
        <form
          onSubmit={(e) => void remove(e)}
          className="space-y-3 rounded-xl border border-rose-800/60 bg-rose-950/30 p-4 text-sm text-rose-100"
        >
          <p className="font-semibold">{deleting.username} 계정을 삭제할까요? 되돌릴 수 없습니다.</p>
          <p className="text-xs text-rose-200/80">
            작업 {deleting.job_count}개 · 배치 {deleting.batch_count}개 · 영상 보관본과 결과 파일이 함께 지워집니다.
            검수한 학습 문장은 남고 계정 연결만 끊깁니다.
          </p>
          <label className="block space-y-1">
            <span className="text-xs">확인을 위해 아이디 <b>{deleting.username}</b> 를 입력</span>
            <input
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              aria-label="삭제 확인 아이디"
              className="w-full max-w-xs rounded-lg border border-rose-800/60 bg-slate-950 px-3 py-2 text-slate-100 outline-none"
            />
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={confirm.trim().toLowerCase() !== deleting.username || busy === deleting.id}
              className="rounded-lg bg-rose-600/80 px-3 py-2 text-white disabled:opacity-40"
            >
              영구 삭제
            </button>
            <button
              type="button"
              onClick={() => {
                setDeleting(null);
                setConfirm("");
              }}
              className="rounded-lg border border-console-border px-3 py-2 text-slate-200"
            >
              취소
            </button>
          </div>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-console-border bg-console-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-xs uppercase text-console-muted">
              <tr>
                <th className="px-3 py-3">아이디</th>
                <th className="px-3 py-3">이메일</th>
                <th className="px-3 py-3">작업 · 배치</th>
                <th className="px-3 py-3">상태</th>
                <th className="px-3 py-3">마지막 로그인</th>
                <th className="px-3 py-3">가입</th>
                <th className="px-3 py-3">관리</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((u) => (
                <tr key={u.id} className="border-t border-console-border align-top">
                  <td className="px-3 py-3">
                    <span className="inline-flex items-center gap-1 font-medium text-slate-100">
                      {u.is_admin && <Shield className="h-3.5 w-3.5 text-console-accent" aria-label="관리자" />}
                      {u.username}
                    </span>
                    {u.display_name && <p className="text-xs text-console-muted">{u.display_name}</p>}
                  </td>
                  <td className="px-3 py-3 text-xs text-slate-300">{u.email}</td>
                  <td className="px-3 py-3 text-xs">
                    {u.job_count} · {u.batch_count}
                  </td>
                  <td className="px-3 py-3 text-xs">
                    {u.locked ? (
                      <span className="inline-flex items-center gap-1 text-amber-300">
                        <Lock className="h-3.5 w-3.5" /> 잠김
                      </span>
                    ) : u.active_sessions > 0 ? (
                      <span className="text-emerald-300">로그인 {u.active_sessions}</span>
                    ) : (
                      <span className="text-console-muted">-</span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-xs text-console-muted">{when(u.last_login_at)}</td>
                  <td className="px-3 py-3 text-xs text-console-muted">{when(u.created_at)}</td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {u.locked && (
                        <button
                          type="button"
                          disabled={busy === u.id}
                          onClick={() =>
                            void act(u.id, async () => {
                              await unlockUser(u.id);
                              return `${u.username} 잠금 해제`;
                            })
                          }
                          className="inline-flex items-center gap-1 rounded border border-console-border px-2 py-1 text-xs text-slate-200 hover:border-console-accent"
                        >
                          <Unlock className="h-3.5 w-3.5" /> 잠금 해제
                        </button>
                      )}
                      {u.active_sessions > 0 && (
                        <button
                          type="button"
                          disabled={busy === u.id}
                          onClick={() =>
                            void act(u.id, async () => {
                              const n = await revokeUserSessions(u.id);
                              return `${u.username} 로그인 세션 ${n}개 종료`;
                            })
                          }
                          className="inline-flex items-center gap-1 rounded border border-console-border px-2 py-1 text-xs text-slate-200 hover:border-console-accent"
                        >
                          <LogOut className="h-3.5 w-3.5" /> 로그아웃
                        </button>
                      )}
                      {!u.is_admin && (
                        <button
                          type="button"
                          disabled={busy === u.id}
                          onClick={() => {
                            setDeleting(u);
                            setConfirm("");
                            setNotice(null);
                          }}
                          className="inline-flex items-center gap-1 rounded border border-rose-900/60 px-2 py-1 text-xs text-rose-300 hover:border-rose-600"
                        >
                          <Trash2 className="h-3.5 w-3.5" /> 삭제
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {loaded && rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-10 text-center text-console-muted">
                    {applied ? "검색 결과가 없습니다." : "아직 가입한 회원이 없습니다."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {total > PAGE && (
        <div className="flex items-center justify-end gap-2 text-xs text-console-muted">
          <span>
            {offset + 1}–{Math.min(offset + PAGE, total)} / {total}
          </span>
          <button
            type="button"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE))}
            className="rounded border border-console-border px-2 py-1 disabled:opacity-40"
          >
            이전
          </button>
          <button
            type="button"
            disabled={offset + PAGE >= total}
            onClick={() => setOffset(offset + PAGE)}
            className="rounded border border-console-border px-2 py-1 disabled:opacity-40"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}
