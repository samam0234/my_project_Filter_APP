/**
 * 결과 이미지 — 투명 PNG 가 보이도록 체크무늬 배경(index.css .bg-checker)을 깐다.
 * src 가 없으면 자리표시.
 */
interface Props {
  src?: string | null;
  alt: string;
  checker?: boolean;
  className?: string;
}

export function ResultImage({ src, alt, checker = false, className = "" }: Props) {
  if (!src) {
    return (
      <div
        className={`flex aspect-[4/3] items-center justify-center rounded-xl bg-slate-800/60 text-xs text-slate-500 ${className}`}
      >
        이미지 없음
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={`w-full rounded-xl border border-slate-800 object-contain ${
        checker ? "bg-checker" : "bg-slate-900"
      } ${className}`}
    />
  );
}
