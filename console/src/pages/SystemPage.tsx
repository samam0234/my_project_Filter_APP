/**
 * 시스템 — `GET /api/v1/console/system` + `/health`.
 *
 * - 배포 설정 점검(preflight) 결과: production 에서 기동을 막는 항목(error) · 경고(warn)
 * - 런타임: 세그 모델 · 오픈보캐브 · LLM/RAG · 배치 큐(Redis) · 영상 출력 · 콘솔 접근 설정
 * - 저장 공간: 단일 작업 · 배치 · 영상 별 용량과 보관 기간이 지난 파일 수 → "지금 정리" (먼저 미리 보기)
 * 이 화면은 모델을 새로 로드하지 않는다 (아직 첫 요청 전이면 "로드 전").
 */
import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Trash2 } from "lucide-react";
import { errorMessage, fetchSystem, runCleanup } from "../api/client";
import { StatCard } from "../components/StatCard";
import { useConsoleStore } from "../store/useConsoleStore";
import type { CleanupResult, SystemSnapshot } from "../types";

const AREA_LABEL: Record<string, string> = { jobs: "단일 작업", batches: "배치", videos: "영상" };
const RUNTIME_LABEL: Record<string, string> = {
  not_loaded: "로드 전 (첫 요청 때 로드)",
  ultralytics: "Ultralytics (.pt)",
  onnx: "ONNX Runtime",
  stub: "stub — 가중치 없음",
};

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = n / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(v >= 100 ? 0 : 1)} ${units[i]}`;
}

function Rows({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="divide-y divide-console-border">
      {rows.map(([k, v]) => (
        <div key={k} className="flex flex-col gap-1 px-4 py-2.5 sm:flex-row sm:items-center sm:justify-between">
          <dt className="text-xs text-console-muted">{k}</dt>
          <dd className="font-mono text-sm text-slate-200">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-console-border bg-console-panel">
      <h3 className="border-b border-console-border px-4 py-2.5 text-sm font-medium text-slate-100">{title}</h3>
      {children}
    </section>
  );
}

export function SystemPage() {
  const health = useConsoleStore((s) => s.health);
  const [snap, setSnap] = useState<SystemSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<CleanupResult | null>(null);
  const [done, setDone] = useState<CleanupResult | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setSnap(await fetchSystem());
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const cleanup = async (dryRun: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const r = await runCleanup(dryRun);
      if (dryRun) {
        setPreview(r);
        setDone(null);
      } else {
        setDone(r);
        setPreview(null);
        await load();
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const errors = snap?.preflight.filter((i) => i.level === "error") ?? [];
  const warns = snap?.preflight.filter((i) => i.level === "warn") ?? [];
  const expired = snap?.storage.areas.reduce((n, a) => n + a.expired_files, 0) ?? 0;
  const yesNo = (v: boolean) => (v ? "켜짐" : "꺼짐");

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">시스템</h2>
        <p className="mt-1 text-sm text-console-muted">
          런타임 · 저장 공간 · 배포 설정 점검 (API {health?.status === "ok" ? "online" : "offline"} · v{snap?.version ?? health?.version ?? "-"} ·{" "}
          {snap?.app_env ?? "-"})
        </p>
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {snap && (
        <>
          <Panel title={`배포 설정 점검 — ${snap.production ? "production: error 가 있으면 기동 거부" : "development: 경고만"}`}>
            {snap.preflight.length === 0 ? (
              <p className="flex items-center gap-2 px-4 py-3 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" /> 문제 없음
              </p>
            ) : (
              <ul className="divide-y divide-console-border text-sm">
                {[...errors, ...warns].map((i) => (
                  <li key={i.key} className="flex gap-3 px-4 py-2.5">
                    <span
                      className={`mt-0.5 shrink-0 rounded px-1.5 text-[11px] uppercase ${
                        i.level === "error" ? "bg-rose-900/60 text-rose-200" : "bg-amber-900/50 text-amber-200"
                      }`}
                    >
                      {i.level}
                    </span>
                    <span>
                      <b className="font-mono text-slate-100">{i.key}</b>{" "}
                      <span className="text-console-muted">{i.message}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title="세그멘테이션 · 오픈 보캐브">
              <Rows
                rows={[
                  ["세그 런타임", RUNTIME_LABEL[snap.segmentation.runtime] ?? snap.segmentation.runtime],
                  ["가중치", `${snap.segmentation.model_file}${snap.segmentation.model_exists ? "" : " (없음!)"}`],
                  ["신뢰도 기준", String(snap.segmentation.min_confidence)],
                  [
                    "배경 덩어리 (건물·하늘·도로…)",
                    !snap.stuff_seg.enabled
                      ? "꺼짐"
                      : !snap.stuff_seg.model_exists
                        ? `모델 파일 없음 (${snap.stuff_seg.model_file})`
                        : `${snap.stuff_seg.model_file} · ${snap.stuff_seg.loaded ? "로드됨" : "로드 전"}`,
                  ],
                  ["오픈 보캐브 (DINO+SAM2)", yesNo(snap.open_vocab.enabled)],
                  ["DINO 임계값 (박스/문구)", `${snap.open_vocab.box_threshold} / ${snap.open_vocab.text_threshold}`],
                  ["오픈 보캐브 로드됨", snap.open_vocab.loaded.length ? snap.open_vocab.loaded.join(", ") : "-"],
                ]}
              />
            </Panel>
            <Panel title="프롬프트 해석 · 배치 · 영상">
              <Rows
                rows={[
                  ["LLM", `${snap.llm.provider} · ${snap.llm.model || "-"} (폴백 ${snap.llm.fallback})`],
                  ["LoRA 어댑터", snap.llm.lora_adapter ? "사용" : "미사용"],
                  ["RAG 예시", snap.llm.rag_enabled ? `켜짐 (${snap.llm.rag_sources})` : "꺼짐"],
                  [
                    "배치 큐",
                    snap.batch.use_celery
                      ? `Celery · Redis ${snap.batch.redis_ok === null ? "확인 불가" : snap.batch.redis_ok ? "연결됨" : "연결 안 됨 (API 프로세스로 처리)"}`
                      : "API 프로세스 (BackgroundTasks)",
                  ],
                  ["영상 출력", `${snap.video.output_format} · 최대 ${snap.video.max_seconds}초 / ${snap.video.max_frames}프레임`],
                  [
                    "콘솔 접근",
                    `${snap.console.require_login ? "로그인 필수" : "서버 PC 는 로그인 없이"} · 관리자 ${snap.console.admins}명${
                      snap.console.allow_remote ? " · 원격 허용(주의)" : ""
                    }`,
                  ],
                ]}
              />
            </Panel>
          </div>

          <Panel title={`저장 공간 — 보관 기간 ${snap.storage.retention_hours}시간`}>
            <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
              {snap.storage.areas.map((a) => (
                <StatCard
                  key={a.name}
                  label={AREA_LABEL[a.name] ?? a.name}
                  value={formatBytes(a.bytes)}
                  hint={`파일 ${a.files}개 · 기간 지남 ${a.expired_files}개${a.oldest_hours !== null ? ` · 가장 오래된 ${a.oldest_hours}시간` : ""}`}
                  tone={a.expired_files ? "warn" : "default"}
                />
              ))}
              {snap.storage.disk && (
                <StatCard
                  label="디스크 남은 공간"
                  value={formatBytes(snap.storage.disk.free)}
                  hint={`전체 ${formatBytes(snap.storage.disk.total)}`}
                  tone={snap.storage.disk.free / snap.storage.disk.total < 0.1 ? "bad" : "ok"}
                />
              )}
            </div>
            <div className="space-y-3 border-t border-console-border px-4 py-3 text-sm">
              <p className="text-xs text-console-muted">
                보관 기간이 지난 업로드 파일(원본·결과·배치·영상)을 지웁니다. 작업 기록(DB)은 남고 사용자 화면에는 이미지 대신 안내가
                보입니다. 정기 실행은 <code>scripts/cleanup.py</code>.
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void cleanup(true)}
                  className="rounded-lg border border-console-border px-3 py-2 text-slate-200 hover:border-console-accent disabled:opacity-50"
                >
                  정리 미리 보기
                </button>
                <button
                  type="button"
                  disabled={busy || !preview || preview.removed_files === 0}
                  onClick={() => void cleanup(false)}
                  className="inline-flex items-center gap-1 rounded-lg bg-rose-600/70 px-3 py-2 text-white disabled:opacity-40"
                >
                  <Trash2 className="h-4 w-4" /> 지금 정리
                </button>
                {!preview && !done && expired > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-300">
                    <AlertTriangle className="h-3.5 w-3.5" /> 기간 지난 파일 {expired}개
                  </span>
                )}
              </div>
              {preview && (
                <p className="text-xs text-slate-300">
                  지울 대상: 파일 {preview.removed_files}개 · {formatBytes(preview.freed_bytes)} — 확인했으면 "지금 정리"
                </p>
              )}
              {done && (
                <p className="text-xs text-emerald-300">
                  정리 완료: 파일 {done.removed_files}개 · {formatBytes(done.freed_bytes)} · 빈 폴더 {done.removed_dirs}개
                </p>
              )}
            </div>
          </Panel>
        </>
      )}

      <div className="rounded-xl border border-console-border bg-console-panel p-4 text-sm text-console-muted">
        <p className="font-medium text-slate-200">운영 메모</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            Docker 스택 프로젝트명: <code>cut_and_keep</code> · MariaDB 3306 / Redis 6380 · DB {health?.db_dialect ?? "-"} · 학습 DB{" "}
            {health?.learning_db ?? "-"}
          </li>
          <li>
            배포 전 점검: <code>cd backend && APP_ENV=production python -m app.core.preflight</code>
          </li>
          <li>
            상세 트러블슈팅: <code>docs/repeater/</code>
          </li>
        </ul>
      </div>
    </div>
  );
}
