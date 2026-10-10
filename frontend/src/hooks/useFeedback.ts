/**
 * 결과 like/dislike 전송 훅.
 *
 * jobId 를 인자로 받아 작업실·작업 상세 어디서든 쓴다.
 * dislike 에 comment(정답 ParsedPrompt JSON)를 실으면 LoRA 학습 정답으로 쓰인다.
 */
import { useCallback, useState } from "react";
import { errorMessage, sendFeedback } from "../api/client";

export function useFeedback(jobId?: string | null) {
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState<"like" | "dislike" | null>(null);

  const vote = useCallback(
    async (value: "like" | "dislike", comment?: string) => {
      if (!jobId) {
        setMessage("결과가 없습니다.");
        return false;
      }
      setLoading(true);
      try {
        const res = await sendFeedback({ job_id: jobId, vote: value, comment });
        setMessage(res.message);
        setSent(value);
        return true;
      } catch (err) {
        setMessage(errorMessage(err, "피드백 전송에 실패했습니다."));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [jobId],
  );

  return { vote, message, loading, sent };
}
