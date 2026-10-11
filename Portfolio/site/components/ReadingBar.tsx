"use client";

import { useEffect, useState } from "react";

export function ReadingBar() {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const update = () => {
      const root = document.documentElement;
      const max = root.scrollHeight - root.clientHeight;
      setWidth(max > 0 ? (root.scrollTop / max) * 100 : 0);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  return <div className="reading" style={{ width: `${width}%` }} aria-hidden="true" />;
}
