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
          학습에 쓸 질문과 답은 JSON 파일에 남습니다. 뇌 버튼을 선택한 뒤 보내면 깊이 추론이고, 일반 생성의 2.5배입니다.
          이 사이트 전체에서 하루 10번입니다. 횟수는 안내 서비스 파일에 남고, 한국 시간 오전 12시 전에는 다시 채워지지 않습니다.
        </p>
      </header>
      <ChatPanel />
    </Shell>
  );
}
