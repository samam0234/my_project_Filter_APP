/**
 * 드래그앤드롭 이미지 선택 컴포넌트.
 *
 * react-dropzone 으로 JPEG/PNG/WebP · 최대 20MB · 1파일만 허용.
 * 선택 시 useAppStore.setFile → Object URL 미리보기.
 */
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { ImagePlus, RefreshCw } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";
import { formatFileSize } from "../../utils/formatters";

export function ImageUploader() {
  const setFile = useAppStore((s) => s.setFile);
  const file = useAppStore((s) => s.file);
  const previewUrl = useAppStore((s) => s.previewUrl);

  const onDrop = useCallback(
    (accepted: File[]) => {
      // 첫 번째 수락 파일만 사용
      if (accepted[0]) setFile(accepted[0]);
    },
    [setFile],
  );

  // -------------------------------------------------------------------------
  // 【수동】 클라이언트 업로드 제한 — 백엔드와 반드시 동기화
  // 조건:
  //   accept  ↔ Settings.allowed_mime_types + ALLOWED_EXTENSIONS
  //   maxSize ↔ MAX_UPLOAD_SIZE_MB (기본 20) * 1024^2
  //   maxFiles: Phase1=1, 배치 UI 는 BatchUploader(Phase2)
  // 기능: 잘못된 파일 조기 거부. 여기만 바꾸면 서버에서 또 400 날 수 있음
  // -------------------------------------------------------------------------
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
  });
  const rejected = fileRejections[0]?.errors[0]?.code;

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`group relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed transition ${
          isDragActive
            ? "border-brand-400 bg-brand-500/10"
            : previewUrl
              ? "border-slate-700 bg-slate-950/60 hover:border-slate-500"
              : "border-slate-700 bg-slate-900/40 hover:border-brand-500/60 hover:bg-slate-900/70"
        }`}
      >
        <input {...getInputProps()} />
        {previewUrl ? (
          <div className="relative">
            <img src={previewUrl} alt="preview" className="mx-auto max-h-72 w-full object-contain" />
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 opacity-0 transition group-hover:opacity-100">
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-xs text-slate-100 ring-1 ring-slate-700">
                <RefreshCw className="h-3.5 w-3.5" /> 다른 사진으로 바꾸기
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 px-6 py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 ring-1 ring-inset ring-brand-500/25 transition group-hover:scale-105">
              <ImagePlus className="h-6 w-6 text-brand-400" />
            </span>
            <div>
              <p className="font-medium text-slate-100">
                {isDragActive ? "여기에 놓으세요" : "이미지 드래그 또는 클릭"}
              </p>
              <p className="mt-1 text-xs text-slate-400">JPEG / PNG / WebP · 최대 20MB</p>
            </div>
          </div>
        )}
      </div>
      {file && (
        <p className="truncate text-xs text-slate-400">
          <span className="text-brand-300">{file.name}</span> · {formatFileSize(file.size)}
        </p>
      )}
      {rejected && (
        <p className="text-xs text-rose-300" role="alert">
          {rejected === "file-too-large"
            ? "20MB 보다 큰 사진은 올릴 수 없어요."
            : rejected === "file-invalid-type"
              ? "JPEG · PNG · WebP 사진만 올릴 수 있어요."
              : "사진은 한 장만 올릴 수 있어요."}
        </p>
      )}
    </div>
  );
}
