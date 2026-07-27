import { ThumbsDown, ThumbsUp } from "lucide-react";
import { Button } from "../common/Button";
import { useFeedback } from "../../hooks/useFeedback";
import { useAppStore } from "../../store/useAppStore";

export function FeedbackButtons() {
  const result = useAppStore((s) => s.result);
  const { vote, message, loading } = useFeedback();

  if (!result) return null;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-sm text-slate-400">결과 평가</span>
      <Button
        variant="secondary"
        disabled={loading}
        onClick={() => vote("like")}
      >
        <ThumbsUp className="h-4 w-4" /> 좋아요
      </Button>
      <Button
        variant="danger"
        disabled={loading}
        onClick={() => vote("dislike")}
      >
        <ThumbsDown className="h-4 w-4" /> 싫어요
      </Button>
      {message && <span className="text-xs text-slate-400">{message}</span>}
    </div>
  );
}
