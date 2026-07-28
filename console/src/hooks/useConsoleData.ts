/**
 * 콘솔 데이터 새로고침 훅.
 *
 * health 와 jobs 를 병렬 요청 후 store 에 반영.
 * jobs 실패는 빈 배열로 흡수하고, health 실패만 에러로 표시.
 */
import { useCallback } from "react";
import { fetchHealth, fetchJobs } from "../api/client";
import { useConsoleStore } from "../store/useConsoleStore";

export function useConsoleData() {
  const setHealth = useConsoleStore((s) => s.setHealth);
  const setJobs = useConsoleStore((s) => s.setJobs);
  const setLoading = useConsoleStore((s) => s.setLoading);
  const setError = useConsoleStore((s) => s.setError);
  const markRefreshed = useConsoleStore((s) => s.markRefreshed);
  const loading = useConsoleStore((s) => s.loading);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // health 필수, jobs 는 실패 시 [] 로 폴백
      const [health, jobs] = await Promise.all([
        fetchHealth(),
        fetchJobs(100).catch(() => [] as Awaited<ReturnType<typeof fetchJobs>>),
      ]);
      setHealth(health);
      setJobs(jobs);
      markRefreshed();
    } catch (err: unknown) {
      const message =
        (err as { message?: string })?.message ||
        "백엔드에 연결할 수 없습니다. API(8000) 기동 여부를 확인하세요.";
      setError(String(message));
    } finally {
      setLoading(false);
    }
  }, [markRefreshed, setError, setHealth, setJobs, setLoading]);

  return { refresh, loading };
}
