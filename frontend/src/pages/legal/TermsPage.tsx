/**
 * 이용약관 (/terms). 법률 검토 전 초안 — 공개 전에 운영자 정보(src/data/legal.ts)를 채우고 검토를 받는다.
 */
import { PageHeader } from "../../components/common/PageHeader";
import { Link } from "../../router";
import { OPERATOR, RETENTION } from "../../data/legal";
import { LegalSection } from "./PrivacyPage";

export function TermsPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-8">
      <PageHeader
        eyebrow="이용약관"
        title="컷앤킵 이용약관"
        description={`${OPERATOR.name}(이하 "운영자")가 제공하는 컷앤킵 서비스의 이용 조건입니다. 시행일 ${OPERATOR.policyDate}`}
      />

      <LegalSection n={1} title="서비스">
        <p>
          컷앤킵은 이용자가 올린 사진 · 움직이는 GIF · 짧은 영상에서, 이용자가 문장으로 요청한 대상을 찾아 배경 제거 · 블러 · 크롭 · 대상 지우기를
          자동으로 처리해 주는 서비스입니다. 로그인하지 않아도 처리하고 바로 내려받을 수 있으며, 회원은 작업 기록 · 배치 · 평가 기능을 쓸 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection n={2} title="계정">
        <ul className="list-disc space-y-1 pl-5">
          <li>회원은 정확한 이메일로 가입하고, 아이디와 비밀번호를 스스로 관리합니다.</li>
          <li>남의 정보로 가입하거나 계정을 다른 사람과 공유하면 안 됩니다.</li>
          <li>계정 삭제를 원하면 개인정보 처리방침의 문의처로 요청합니다.</li>
        </ul>
      </LegalSection>

      <LegalSection n={3} title="이용자가 지켜야 할 것">
        <p>다음 콘텐츠를 올리거나 다음 목적으로 서비스를 쓰면 안 됩니다.</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>이용자에게 권리가 없는 사진 · 영상, 또는 다른 사람의 얼굴 · 모습을 그 사람의 동의 없이 담은 콘텐츠</li>
          <li>불법 촬영물, 아동 · 청소년 성착취물, 그 밖에 법으로 금지된 콘텐츠</li>
          <li>결과물을 이용한 사칭 · 명예훼손 · 사기 · 허위 정보 유포</li>
          <li>자동화된 대량 요청 등 서비스 운영을 방해하는 행위 (처리 횟수 제한을 우회하려는 시도 포함)</li>
        </ul>
        <p>운영자는 위반을 확인하면 해당 결과를 지우고 이용을 제한하거나 계정을 삭제할 수 있으며, 법령에 따라 관계 기관에 알릴 수 있습니다.</p>
      </LegalSection>

      <LegalSection n={4} title="콘텐츠와 결과물의 권리">
        <ul className="list-disc space-y-1 pl-5">
          <li>이용자가 올린 콘텐츠와 그 결과물의 권리는 이용자(또는 원래 권리자)에게 있습니다.</li>
          <li>
            운영자는 요청한 처리를 하고 결과를 보여 주는 데 필요한 범위에서만 콘텐츠를 다루며, 회원 파일은 {RETENTION.fileHours}시간 뒤 자동으로
            지웁니다.
          </li>
          <li>요청 문장과 그 해석은 운영자가 검수한 뒤 서비스 품질 개선(문장 이해 학습)에 쓸 수 있습니다. 자세한 내용은 개인정보 처리방침을 따릅니다.</li>
        </ul>
      </LegalSection>

      <LegalSection n={5} title="결과의 한계">
        <p>
          처리는 인공지능이 자동으로 합니다. 지정하지 않은 대상이 일부 섞이거나, 원하지 않은 대상을 고르거나, 지운 자리가 어색할 수 있습니다.
          운영자는 결과가 특정 목적에 맞는다는 것을 보증하지 않으며, 중요한 용도라면 결과를 직접 확인한 뒤 쓰기 바랍니다.
        </p>
      </LegalSection>

      <LegalSection n={6} title="서비스의 변경 · 중단">
        <p>
          운영자는 기능을 바꾸거나 점검 · 장애 · 운영상 이유로 서비스를 잠시 또는 영구히 멈출 수 있습니다. 미리 알 수 있는 중요한 변경 · 종료는 이
          화면이나 공지로 알립니다. 보관 기간이 지난 결과는 복구할 수 없으니 필요한 결과는 바로 내려받기 바랍니다.
        </p>
      </LegalSection>

      <LegalSection n={7} title="책임의 제한">
        <p>
          운영자는 고의 또는 중대한 과실이 없는 한, 무료로 제공되는 서비스의 이용 · 결과물로 생긴 손해에 책임을 지지 않습니다. 이용자가 이 약관이나
          법령을 어겨 생긴 문제는 이용자가 책임집니다.
        </p>
      </LegalSection>

      <LegalSection n={8} title="약관의 변경 · 준거법">
        <p>
          약관을 바꾸면 시행 7일 전(이용자에게 불리하면 30일 전)부터 이 화면에 알립니다. 이 약관은 대한민국 법을 따르며, 분쟁은 민사소송법상 관할
          법원에서 해결합니다.
        </p>
        <p>
          문의: {OPERATOR.email} ·{" "}
          <Link to="/privacy" className="text-brand-400 hover:text-brand-200">
            개인정보 처리방침 보기
          </Link>
        </p>
      </LegalSection>
    </article>
  );
}
