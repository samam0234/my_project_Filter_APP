/**
 * 조회용 API 훅.
 *
 * - useAsync   : 비동기 함수 결과 + loading/error + reload (언마운트·재요청 경합 무시)
 * - useJobs    : 최근 작업 목록
 * - useJob     : 작업 단건
 * - useHealth  : 백엔드 상태 (30초 간격 재확인)
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage, getJob, healthCheck, listJobs } from "../api/client";
import type { HealthResponse, JobResponse } from "../types";

interface AsyncState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const seq = useRef(0);

  useEffect(() => {
    const id = ++seq.current;
    setLoading(true);
    setError(null);
    fn()
      .then((value) => {
        if (id === seq.current) setData(value);
      })
      .catch((err: unknown) => {
        if (id === seq.current) setError(errorMessage(err));
      })
      .finally(() => {
        if (id === seq.current) setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  useEffect(
    () => () => {
      seq.current += 1; // 언마운트 후 도착한 응답 무시
    },
    [],
  );

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload };
}

export function useJobs(limit = 50) {
  return useAsync<JobResponse[]>(() => listJobs(limit), [limit]);
}

export function useJob(jobId: string) {
  return useAsync<JobResponse>(() => getJob(jobId), [jobId]);
}

/** 백엔드 연결 상태. online: null=확인 중 */
export function useHealth(intervalMs = 30_000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    const check = () =>
      healthCheck()
        .then((h) => {
          if (!alive) return;
          setHealth(h);
          setOnline(h.status === "ok");
        })
        .catch(() => alive && setOnline(false));
    void check();
    const t = window.setInterval(check, intervalMs);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [intervalMs]);

  return { health, online };
}
