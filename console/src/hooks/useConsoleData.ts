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
