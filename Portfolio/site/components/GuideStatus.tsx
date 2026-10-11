"use client";

import { useEffect, useState } from "react";

export function GuideStatus() {
  const [ready, setReady] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/chat")
      .then((res) => res.json())
      .then((data: { ready?: boolean }) => setReady(!!data.ready))
      .catch(() => setReady(false));
  }, []);

  const label = ready === null ? "안내 챗 확인 중" : ready ? "안내 챗 준비됨" : "안내 챗이 꺼져 있음";
  return (
    <p className={`live ${ready ? "on" : ready === false ? "off" : ""}`}>
      <i />
      {label}
    </p>
  );
}
