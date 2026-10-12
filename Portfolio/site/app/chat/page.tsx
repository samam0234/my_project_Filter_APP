import { Shell } from "@/components/Shell";
import { ChatPanel } from "./ChatPanel";

export default function ChatPage() {
  return (
    <Shell current="/chat">
      <header className="page-head">
        <div className="kicker">GUIDE · 기본 gemma4:e4b</div>
        <h1>안내 챗</h1>
        <p className="lede">
          Flask 안내가 LangGraph로 질문을 나누고, 포트폴리오 문서를 검색한 뒤 LangChain으로 답합니다.
          제품의 사진 처리나 제품 채팅과는 다른 프로세스입니다. 화면 기록은 이 브라우저에만 있고,
          학습에 쓸 질문과 답은 JSON 파일에 남습니다. 뇌 버튼을 선택한 뒤 보내면 깊이 추론이고, 일반 생성의 2.5배입니다.
          이 사이트 전체에서 하루 10번입니다. 횟수는 사이트 SQLite에 남고 한국 시간 오전 12시에 초기화됩니다.
          보내기 위 버튼의 기본 모델은 gemma4:e4b이고, 누르면 gemma4:12b입니다.
        </p>
      </header>
      <ChatPanel />
    </Shell>
  );
}
