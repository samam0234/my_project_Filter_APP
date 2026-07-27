import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";
import { formatFileSize } from "../../utils/formatters";

export function ImageUploader() {
  const setFile = useAppStore((s) => s.setFile);
  const file = useAppStore((s) => s.file);
  const previewUrl = useAppStore((s) => s.previewUrl);

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) setFile(accepted[0]);
    },
    [setFile],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed p-6 transition ${
        isDragActive
          ? "border-brand-500 bg-brand-500/10"
          : "border-slate-700 bg-slate-900/60 hover:border-slate-500"
      }`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3 text-center">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt="preview"
            className="max-h-48 rounded-xl object-contain"
          />
        ) : (
          <Upload className="h-10 w-10 text-slate-400" />
        )}
        <div>
          <p className="font-medium text-slate-100">
            {isDragActive ? "여기에 놓으세요" : "이미지 드래그 또는 클릭"}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            JPEG / PNG / WebP · 최대 20MB
          </p>
          {file && (
            <p className="mt-2 text-xs text-brand-500">
              {file.name} · {formatFileSize(file.size)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
