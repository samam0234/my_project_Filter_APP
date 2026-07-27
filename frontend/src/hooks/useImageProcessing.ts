import { useCallback } from "react";
import { resolveAssetUrl, uploadImage } from "../api/client";
import { useAppStore } from "../store/useAppStore";

export function useImageProcessing() {
  const file = useAppStore((s) => s.file);
  const prompt = useAppStore((s) => s.prompt);
  const isProcessing = useAppStore((s) => s.isProcessing);
  const setProcessing = useAppStore((s) => s.setProcessing);
  const setError = useAppStore((s) => s.setError);
  const setResult = useAppStore((s) => s.setResult);

  const process = useCallback(async () => {
    if (!file) {
      setError("이미지를 먼저 업로드하세요.");
      return;
    }
    if (!prompt.trim()) {
      setError("프롬프트를 입력하세요.");
      return;
    }

    setProcessing(true);
    setError(null);
    try {
      const data = await uploadImage(file, prompt.trim());
      setResult({
        jobId: data.job_id,
        status: data.status,
        beforeUrl: resolveAssetUrl(data.before_url),
        afterUrl: resolveAssetUrl(data.after_url),
        qualityScore: data.quality_score,
        parsedPrompt: data.parsed_prompt ?? null,
        message: data.message,
      });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } }; message?: string })
          ?.response?.data?.detail ||
        (err as { message?: string })?.message ||
        "처리 중 오류가 발생했습니다.";
      setError(String(message));
    } finally {
      setProcessing(false);
    }
  }, [file, prompt, setError, setProcessing, setResult]);

  return { process, isProcessing };
}
