import { Shell } from "@/components/Shell";
import { ChatPanel } from "./ChatPanel";

export default function ChatPage() {
  return (
    <Shell current="/chat">
      <header className="page-head">
        <div className="kicker">GUIDE · Ollama gemma4:12b</div>
        <h1>안내 챗</h1>
        <p className="lede">
          Flask 안내가 LangGraph로 질문을 나누고, 포트폴리오 문서를 검색한 뒤 LangChain으로 답합니다.
          제품의 사진 처리나 제품 채팅과는 다른 프로세스입니다. 화면 기록은 이 브라우저에만 있고,
          학습에 쓸 질문과 답은 데이터베이스가 아니라 JSON 파일에 남습니다.
        </p>
      </header>
      <ChatPanel />
    </Shell>
  );
}
