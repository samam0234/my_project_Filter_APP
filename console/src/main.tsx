/**
 * 운영 콘솔 엔트리 (Vite :5174).
 * #root 에 App 을 StrictMode 로 마운트.
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
