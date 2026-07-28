/**
 * 단일 이미지 처리 훅.
 *
 * store 의 file + prompt 를 읽어 POST /api/v1/upload 를 호출하고
 * 응답을 ProcessResultState 형태로 store 에 넣는다.
 */
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
    // 클라이언트 측 사전 검증
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
      // multipart 업로드 → 백엔드 파이프라인 동기 실행
      const data = await uploadImage(file, prompt.trim());
      // snake_case API → camelCase UI 상태 매핑
      setResult({
        jobId: data.job_id,
        status: data.status,
        // 상대 URL 을 baseURL/프록시 기준으로 절대화
        beforeUrl: resolveAssetUrl(data.before_url),
        afterUrl: resolveAssetUrl(data.after_url),
        qualityScore: data.quality_score,
        parsedPrompt: data.parsed_prompt ?? null,
        message: data.message,
      });
    } catch (err: unknown) {
      // FastAPI detail 또는 일반 Error.message
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
