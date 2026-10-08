/**
 * 사용자 앱 엔트리 (Vite).
 * #root 에 App 을 StrictMode 로 마운트하고 전역 CSS 를 로드한다.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// 한국어 글꼴 — 동적 서브셋이라 화면에 쓰인 글자 묶음만 내려받는다 (외부 CDN 없이 빌드에 포함)
import "pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
