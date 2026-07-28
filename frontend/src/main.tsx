/**
 * 사용자 앱 엔트리 (Vite).
 * #root 에 App 을 StrictMode 로 마운트하고 전역 CSS 를 로드한다.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
