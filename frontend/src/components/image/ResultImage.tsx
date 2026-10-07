/**
 * 결과 이미지 — 투명 PNG 가 보이도록 체크무늬 배경(index.css .bg-checker)을 깐다.
 * src 가 없거나 불러오지 못하면(보관 기간 24시간 경과 등) 자리표시.
 */
import { useEffect, useState } from "react";

interface Props {
  src?: string | null;
  alt: string;
  checker?: boolean;
  className?: string;
}

export function ResultImage({ src, alt, checker = false, className = "" }: Props) {
  const [broken, setBroken] = useState(false);
  useEffect(() => setBroken(false), [src]);
  if (!src || broken) {
    return (
      <div
        className={`flex aspect-[4/3] items-center justify-center rounded-xl bg-slate-800/60 px-2 text-center text-xs text-slate-500 ${className}`}
      >
        {src ? "이미지를 불러오지 못했어요 (보관 기간이 지났을 수 있어요)" : "이미지 없음"}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setBroken(true)}
      className={`w-full rounded-xl border border-slate-800 object-contain ${
        checker ? "bg-checker" : "bg-slate-900"
      } ${className}`}
    />
  );
}
