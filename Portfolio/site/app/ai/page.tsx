import Link from "next/link";
import { Shell, Shot } from "@/components/Shell";

export default function AiPage() {
  return (
    <Shell current="/ai">
      <header className="page-head">
        <div className="kicker">AI · 제품 추론과 이 사이트의 안내</div>
        <h1>AI 서비스</h1>
        <p className="lede">
          제품 안의 추론은 FastAPI가 합니다. 이 폴더의 Flask는 그 제품을 문서로 설명해 주는 별도 프로그램입니다. 사진을 처리하지 않습니다.
        </p>
      </header>

      <section className="section">
        <h2>개요</h2>
        <p>
          한 요청은 문장 해석, YOLO 마스크, 선택자 규칙, 효과 순입니다.
          기본 해석은 Ollama <code>gemma4:e4b</code>입니다. 작업실에서 12b와 27b를 고를 수 있지만, 이 PC에서는 12b가 이후에도 약 29초, 27b는 메모리에 다 올라가지 않습니다.
          큰 모델이 이 과제에서 더 정확하다는 평가는 하지 않았습니다.
        </p>
      </section>

      <section className="section">
        <h2>엔진</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>역할</th><th>구현</th></tr></thead>
            <tbody>
              <tr><td>비전</td><td>YOLO26m-seg .pt 또는 .onnx</td></tr>
              <tr><td>배경 덩어리</td><td>SegFormer ADE20K. 14종</td></tr>
              <tr><td>지우기</td><td>LaMa ONNX, 없으면 Telea. 영상은 배경판</td></tr>
              <tr><td>열린 어휘</td><td>Grounding DINO + SAM2. 기본 꺼짐, 가중치 없음</td></tr>
              <tr><td>문장</td><td>ollama, lora, openai, gemini, heuristic</td></tr>
              <tr><td>규격</td><td>prompt_spec.py. 서빙과 LoRA가 공유. 바꾸면 재학습</td></tr>
              <tr><td>흐름</td><td>LangGraph 1.2, LangChain 다수결, n-gram RAG</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>상세 기능</h2>
        <ul className="clean">
          <li>키워드 파서는 남길 것, 뺄 것, 지울 것을 구분합니다. 대상 정확도가 56.6%에서 평가 문장 100% 근처로 올랐습니다.</li>
          <li>RAG는 콘솔이 승인한 교정·좋아요·요청만 예시로 붙입니다. 학습 시드 800건을 넣으면 오히려 내려가 기본에서 뺐습니다.</li>
          <li>LoRA Qwen2.5-1.5B는 GPU에서 283문장 94.7%, 약 1초입니다. 운영 기본은 그래도 Ollama입니다. ARM 서버에 GPU가 없습니다.</li>
          <li>영상 추적은 첫 프레임의 대상을 유지합니다. 실제 DAVIS에서 72.8%에서 92.1%로 올랐습니다.</li>
          <li>detect 전용 가중치를 세그 경로에 두지 않습니다. 모델이 없으면 실패를 알리고, 깨진 경우에만 데모 타원을 씁니다.</li>
        </ul>
      </section>

      <section className="section">
        <h2>학습으로 이어지는 연결</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>경로</th><th>의미</th></tr></thead>
            <tbody>
              <tr><td>POST /api/v1/feedback</td><td>좋아요, 싫어요, 정답 JSON</td></tr>
              <tr><td>회원 업로드</td><td>문장과 해석이 검수 후보가 될 수 있음</td></tr>
              <tr><td>POST /api/v1/chat</td><td>학습에 넣지 않음. 대화 비저장</td></tr>
              <tr><td>콘솔 검수</td><td>승인본만 RAG와 재학습 입력</td></tr>
              <tr><td>scripts/retrain_lora.py</td><td>증강, 학습, 평가, 배포</td></tr>
              <tr><td>scripts/retrain_yolo.py</td><td>실패 사진으로 이어 학습. COCO만으로는 채택되지 않은 기록</td></tr>
              <tr><td>scripts/seg_labeling.py</td><td>Label Studio용 내보내기. 외부 라벨 서비스에는 올리지 않음</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>내부 화면</h2>
        <div className="shots">
          <Shot src="/shots/studio-design.jpg" alt="해석 칩이 있는 작업실" caption="이렇게 이해했어요. 대상, 위치, 색, 남기기와 지우기를 문장과 비교합니다." />
          <Shot src="/shots/console-learning.png" alt="검수 화면" caption="틀린 해석은 여기서 고친 뒤 승인해야 다음 요청의 예시가 됩니다." />
          <Shot src="/shots/inpaint.jpg" alt="지우기 결과" caption="지우기 품질 실험. 사진 한 장은 LaMa가 메웁니다." />
          <Shot src="/shots/stuff.jpg" alt="배경 덩어리 비교" caption="배경 덩어리 비교. 사물이 아닌 영역입니다." />
        </div>
      </section>

      <section className="section">
        <h2>고급 기술</h2>
        <p>
          제품의 LangChain은 도구를 여러 번 부르는 에이전트가 아니라 해석 다수결입니다.
          LangGraph는 업로드 한 건의 상태 기계입니다. RAG는 메모리에서 다시 색인합니다.
        </p>
        <p>
          이 사이트의 Flask 안내는 같은 이름을 설명용으로 씁니다. LangGraph가 분류와 검색과 답변을 나누고,
          LangChain이 Ollama <code>gemma4:12b</code>를 호출하고, 이 폴더의 마크다운을 검색합니다.
          화면의 대화 목록은 브라우저 localStorage가 들고, 요청마다 최근 대화를 다시 보냅니다.
          데이터베이스는 쓰지 않습니다. 배운 질문과 답은 JSON에 남아 비슷한 다음 질문을 보완합니다.
          12b가 없으면 안내만 멈추고, 제품 해석 기본값 e4b는 바꾸지 않습니다.
        </p>
        <p><Link href="/chat">안내 챗 열기</Link></p>
      </section>

      <section className="section">
        <h2>문제와 개선</h2>
        <ul className="clean">
          <li>PC가 꺼지면 운영 해석이 키워드 파서입니다.</li>
          <li>12b와 27b는 느리고 Worker 제한에 걸립니다.</li>
          <li>오픈 보캐브는 측정만 되어 있습니다.</li>
          <li>움직이는 카메라 지우기와 닮은 사람 추적은 가이드에 한계로 적혀 있습니다.</li>
        </ul>
        <div className="future">
          추가하려는 추론 서버는 GPU 오버레이가 있는 다른 기계입니다. 파일은 docker-compose.gpu.yml로 이미 있습니다. 가중치가 없는 모델은 자동으로 받지 않습니다.
          예정 기능은 학습 형식 내보내기, 브라우저 로컬 추론, 추출 대상을 다른 배경에 붙이는 편집기입니다.
        </div>
      </section>

      <section className="section">
        <h2>이후</h2>
        <p>
          해석은 로컬을 기본으로 둡니다. 정확도는 모델 교체보다 검수된 문장과 실패 사진에서 더 오릅니다.
          안내 챗은 문서에 있는 것만 말합니다.
        </p>
      </section>
    </Shell>
  );
}
