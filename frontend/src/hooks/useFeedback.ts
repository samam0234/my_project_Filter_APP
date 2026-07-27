import { useCallback, useState } from "react";
import { sendFeedback } from "../api/client";
import { useAppStore } from "../store/useAppStore";

export function useFeedback() {
  const result = useAppStore((s) => s.result);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const vote = useCallback(
    async (value: "like" | "dislike") => {
      if (!result?.jobId) {
        setMessage("결과가 없습니다.");
        return;
      }
      setLoading(true);
      try {
        const res = await sendFeedback({ job_id: result.jobId, vote: value });
        setMessage(res.message);
      } catch {
        setMessage("피드백 전송에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    },
    [result?.jobId],
  );

  return { vote, message, loading };
}
