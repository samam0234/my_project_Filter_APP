/**
 * 개인정보 처리방침 (/privacy).
 *
 * 내용은 실제 동작과 같아야 한다 — 보관 기간 · 수집 항목을 바꾸면 여기와 docs/guidance/legal.md 를 함께 고친다.
 * 법률 검토 전 초안이다. 공개 전에 운영자 정보(src/data/legal.ts)를 채우고 검토를 받는다.
 */
import type { ReactNode } from "react";
import { PageHeader } from "../../components/common/PageHeader";
import { Link } from "../../router";
import { OPERATOR, RETENTION } from "../../data/legal";

export function LegalSection({ n, title, children }: { n: number; title: string; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-white">
        제{n}조 {title}
      </h2>
      <div className="space-y-2 text-sm leading-relaxed text-slate-300">{children}</div>
    </section>
  );
}

export function LegalTable({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full min-w-[520px] text-left text-sm">
        <thead className="bg-slate-900/80 text-xs text-slate-400">
          <tr>
            {head.map((h) => (
              <th key={h} className="px-3 py-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j} className="px-3 py-2 align-top text-slate-300">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PrivacyPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-8">
      <PageHeader
        eyebrow="개인정보 처리방침"
        title="개인정보를 이렇게 다룹니다"
        description={`${OPERATOR.name}(이하 "운영자")는 컷앤킵 서비스에서 이용자의 개인정보를 아래와 같이 처리합니다. 시행일 ${OPERATOR.policyDate}`}
      />

      <div className="card space-y-1.5 p-4 text-sm text-slate-300">
        <p className="font-medium text-white">한눈에 보기</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>로그인하지 않고 처리한 사진 · 영상 · GIF 는 서버에 남기지 않습니다 (처리 직후 삭제).</li>
          <li>회원이 올린 파일과 결과는 {RETENTION.fileHours}시간 보관한 뒤 자동으로 지웁니다.</li>
          <li>요청 문장과 그 해석은 운영자가 검수한 뒤 문장 이해 품질을 높이는 학습에 쓸 수 있습니다.</li>
          <li>
            처리에 실패했거나 대상 인식이 불확실했던 요청의 사진은 원인을 찾고 대상 인식을 고치는 데 쓰려고 {RETENTION.feedbackImageDays}일
            보관한 뒤 지웁니다. 계정을 삭제하면 바로 지웁니다.
          </li>
          <li>개인정보를 다른 회사에 팔거나 제공하지 않습니다.</li>
        </ul>
      </div>

      <LegalSection n={1} title="수집하는 항목">
        <LegalTable
          head={["언제", "항목", "필수 여부"]}
          rows={[
            ["회원가입", "아이디, 이메일, 비밀번호(복원할 수 없는 해시로만 저장), 이름", "이름만 선택"],
            ["서비스 이용 (회원)", "올린 사진 · 영상 · GIF 와 결과, 요청 문장, 처리 기록(해석 · 상태 · 시각), 평가 · 정답 알려주기 내용", "이용 시 자동"],
            ["처리 실패 · 인식이 불확실한 요청 (회원)", "그 요청의 원본 사진 (운영자만 봅니다)", "이용 시 자동"],
            ["서비스 이용 (비로그인)", "올린 파일은 처리하는 동안만 메모리 · 임시 폴더에 두고 바로 지웁니다", "저장하지 않음"],
            ["자동으로 생기는 정보", "접속 IP · 시각 · 요청 경로(서버 로그), 로그인 세션 쿠키", "자동"],
          ]}
        />
      </LegalSection>

      <LegalSection n={2} title="이용 목적">
        <ul className="list-disc space-y-1 pl-5">
          <li>요청한 처리(배경 제거 · 블러 · 지우기 등) 수행과 결과 제공, 작업 기록 보기</li>
          <li>회원 관리 — 로그인, 아이디 찾기 · 비밀번호 재설정 메일 발송, 연속 로그인 실패 잠금</li>
          <li>남용 방지 — 접속 IP · 계정별 처리 횟수 제한 (IP 는 처리 횟수를 세는 데만 1분간 메모리에서 쓰고 저장하지 않습니다)</li>
          <li>품질 개선 — 운영자가 검수한 요청 문장 · 해석을 문장 이해 모델 학습에 사용</li>
          <li>품질 개선 — 처리에 실패했거나 인식이 불확실했던 요청의 사진으로 원인을 찾고, 운영자가 대상 경계를 직접 표시해 대상 인식 모델을 다시 학습 (사진은 외부로 보내지 않습니다)</li>
        </ul>
      </LegalSection>

      <LegalSection n={3} title="보관 기간과 파기">
        <LegalTable
          head={["항목", "보관 기간"]}
          rows={[
            ["올린 파일 · 결과 파일 (회원)", `${RETENTION.fileHours}시간 뒤 자동 삭제`],
            ["올린 파일 (비로그인)", "저장하지 않음 (처리 직후 삭제)"],
            ["처리 실패 · 인식이 불확실한 요청의 사진 (회원)", `${RETENTION.feedbackImageDays}일 뒤 자동 삭제 · 계정 삭제 시 바로 삭제`],
            ["계정 정보 · 작업 기록(문장 · 해석 · 상태)", "계정 삭제 시까지 — 삭제하면 작업 기록과 남은 파일을 함께 지웁니다"],
            ["학습용 요청 문장 · 평가 내용", "계정 삭제 시 계정과의 연결을 끊고(누구의 것인지 알 수 없게) 학습 자료로 보관"],
            ["서버 로그 (접속 IP 포함)", `${RETENTION.logDays}일`],
            ["데이터베이스 백업", `최근 ${RETENTION.backupDays}일분`],
          ]}
        />
        <p>파기는 복구할 수 없는 방법(파일 삭제 · 데이터베이스 행 삭제)으로 합니다.</p>
      </LegalSection>

      <LegalSection n={4} title="제3자 제공과 처리 위탁">
        <p>운영자는 이용자의 개인정보를 제3자에게 제공하지 않습니다. 다만 아래 경우에는 해당 범위에서만 외부 서비스를 씁니다.</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>메일 발송: 아이디 찾기 · 비밀번호 재설정 메일은 운영자가 정한 메일 발송 서비스를 통해 보냅니다 (받는 주소 · 본문).</li>
          <li>
            외부 AI: 기본 설정은 운영자 서버 안의 모델로 문장을 해석합니다. 운영자가 외부 AI(OpenAI · Google Gemini)를 쓰도록 바꾸면
            <b> 요청 문장만</b> 해당 회사로 전송되며, 이 경우 이 방침을 개정해 알립니다. 사진 · 영상은 외부로 보내지 않습니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection n={5} title="쿠키와 브라우저 저장소">
        <ul className="list-disc space-y-1 pl-5">
          <li>로그인 세션 쿠키 — 로그인 상태 유지용. 자바스크립트가 읽을 수 없게(HttpOnly) 설정합니다. 로그아웃하면 지워집니다.</li>
          <li>
            영상 화면의 마지막 결과 1개는 <b>이용자 브라우저(IndexedDB)</b>에만 보관됩니다. 서버로 보내지 않으며, 화면의 "보관된 결과 지우기"나 브라우저
            데이터 삭제로 지울 수 있습니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection n={6} title="이용자의 권리">
        <p>
          이용자는 언제든지 자신의 개인정보 열람 · 정정 · 삭제 · 처리 정지를 요청할 수 있습니다. 계정 삭제는 아래 문의처로 아이디와 함께 요청하면
          지체 없이 처리하고 결과를 알려 드립니다. 작업 기록은 화면에서 직접 볼 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection n={7} title="안전성 확보 조치">
        <ul className="list-disc space-y-1 pl-5">
          <li>비밀번호는 복원할 수 없는 해시(scrypt)로만 저장</li>
          <li>전송 구간 암호화(HTTPS)와 로그인 세션 쿠키 보호(HttpOnly · Secure)</li>
          <li>결과 파일 · 작업 기록은 본인만 볼 수 있게 접근 제한, 운영 화면은 관리자 로그인으로만</li>
          <li>보관 기간이 지난 파일 자동 삭제, 데이터베이스 정기 백업</li>
        </ul>
      </LegalSection>

      <LegalSection n={8} title="개인정보 보호 책임자 · 문의">
        <p>
          운영자: {OPERATOR.name}
          <br />
          문의 · 삭제 요청: {OPERATOR.email}
        </p>
        <p className="text-xs text-slate-500">
          개인정보 침해 신고 · 상담: 개인정보침해신고센터(privacy.kisa.or.kr, 국번 없이 118), 개인정보 분쟁조정위원회(www.kopico.go.kr, 1833-6972)
        </p>
      </LegalSection>

      <LegalSection n={9} title="방침의 변경">
        <p>이 방침을 바꾸면 시행 7일 전부터 이 화면에 알립니다. 이용자에게 불리한 중요한 변경은 30일 전에 알립니다.</p>
        <p>
          시행일: {OPERATOR.policyDate} ·{" "}
          <Link to="/terms" className="text-brand-400 hover:text-brand-200">
            이용약관 보기
          </Link>
        </p>
      </LegalSection>
    </article>
  );
}
