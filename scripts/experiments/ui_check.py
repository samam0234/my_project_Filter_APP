#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브라우저 직접 확인 — 사용자 앱 · 운영 콘솔 실제 클릭 흐름 (Playwright).

비로그인: 홈 · 회원 전용 잠금 · 작업실 처리/다운로드 안내
회원:     가입 → 작업실 처리 → 좋아요 → 기록 → 상세 → 배치(진행률·결과·zip) → 영상 → 로그아웃
비로그인: 영상 처리 → 결과 저장(서버에 저장되지 않음)
콘솔:     배치 현황에서 방금 배치 확인 → 학습 데이터에서 방금 요청 찾기 → 잘못된 JSON 안내 → 정답 고쳐 승인 → 삭제(확인 창)
모바일:   홈 · 작업실 레이아웃
콘솔 오류 · 페이지 예외 · 5xx 응답을 모은다 (비로그인 /auth/me 401 은 정상이라 제외).
끝나면 이번 실행이 만든 테스트 계정·작업·피드백·학습 샘플·파일을 지운다.

준비: 백엔드(:8000) · frontend · console dev 서버, `pip install playwright` (+ 필요 시 `playwright install chromium`)
실행: python scripts/experiments/ui_check.py --app http://localhost:5173 --console http://localhost:5174
결과: docs/vaildates/ui-check-20261006.md
"""
import argparse
import glob
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
ap = argparse.ArgumentParser()
ap.add_argument("--app", default="http://localhost:5173", help="사용자 앱 주소")
ap.add_argument("--console", default="http://localhost:5174", help="운영 콘솔 주소")
ap.add_argument("--out", type=Path, default=ROOT / "logs" / "ui_check", help="화면 캡처 폴더")
args = ap.parse_args()
SHOT = args.out
SHOT.mkdir(parents=True, exist_ok=True)
IMG = sorted(glob.glob(str(ROOT / "training/datasets/cutnkeep_seg_5k/images/val/*.jpg")))[3]
APP, CONSOLE = args.app.rstrip("/"), args.console.rstrip("/")
NAME = "ui" + uuid.uuid4().hex[:8]
PROMPT = f"가운데 사람만 남기고 배경 블러 강도 33 ({NAME[-4:]})"
problems: list[str] = []
steps: list[str] = []


def make_video(path: Path, frames: int = 12) -> Path:
    """검증 이미지 한 장을 살짝 이동시키며 짧은 avi 를 만든다 (ffmpeg 불필요)."""
    import cv2
    import numpy as np

    base = cv2.imread(IMG)
    base = cv2.resize(base, (320, int(base.shape[0] * 320 / base.shape[1])))
    h, w = base.shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (w, h))
    for i in range(frames):
        shift = np.float32([[1, 0, i * 2], [0, 1, 0]])
        writer.write(cv2.warpAffine(base, shift, (w, h), borderMode=cv2.BORDER_REPLICATE))
    writer.release()
    return path


def watch(page, tag):
    page.on("console", lambda m: m.type == "error" and "401" not in m.text and problems.append(f"[{tag} console] {m.text[:200]}"))
    page.on("response", lambda r: r.status == 401 and "/auth/me" not in r.url and problems.append(f"[{tag} 401] {r.url}"))
    page.on("pageerror", lambda e: problems.append(f"[{tag} pageerror] {e}"))
    page.on("response", lambda r: r.status >= 500 and problems.append(f"[{tag} {r.status}] {r.url}"))


def step(name, fn):
    t = time.time()
    try:
        fn()
        steps.append(f"OK   {name} ({time.time() - t:.1f}s)")
    except Exception as exc:  # 계속 진행해 전체 그림을 본다
        steps.append(f"FAIL {name}: {str(exc).splitlines()[0][:220]}")
        for pg_ in list(globals().get("_pages", [])):
            try:
                pg_.screenshot(path=SHOT / f"fail_{len(steps):02d}_{pg_.url.split('/')[-1] or 'root'}.png")
            except Exception:
                pass


def cleanup(username: str) -> None:
    """이번 실행이 만든 테스트 계정과 그 작업·피드백·학습 샘플·파일을 지운다."""
    from app.core.config import get_settings
    from app.db.learning import learning_session
    from app.db.session import SessionLocal, get_engine
    from app.models.feedback import Feedback
    from app.models.batch_job import BatchJob
    from app.models.job import Job
    from app.models.learning_sample import LearningSample
    from app.models.user import AuthCode, AuthSession, User

    settings = get_settings()
    SessionLocal.configure(bind=get_engine())
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return
        job_ids = [j.id for j in db.query(Job).filter(Job.user_id == user.id).all()]
        for job_id in job_ids:
            shutil.rmtree(settings.upload_path / job_id, ignore_errors=True)
        db.query(Job).filter(Job.id.in_(job_ids)).delete(synchronize_session=False)
        # 배치(DB 행 + uploads/batches/{id}) · 영상(uploads/videos/{id}/owner.json 이 이 계정인 것)
        batch_ids = [b.id for b in db.query(BatchJob).filter(BatchJob.user_id == user.id).all()]
        for batch_id in batch_ids:
            shutil.rmtree(settings.upload_path / "batches" / batch_id, ignore_errors=True)
        db.query(BatchJob).filter(BatchJob.id.in_(batch_ids)).delete(synchronize_session=False)
        videos = settings.upload_path / "videos"
        for owner in videos.glob("*/owner.json") if videos.is_dir() else []:
            if f'"{user.id}"' in owner.read_text(encoding="utf-8"):
                shutil.rmtree(owner.parent, ignore_errors=True)
        for model in (AuthSession, AuthCode):
            db.query(model).filter(model.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
    if not job_ids:
        print(f"정리: 계정 {username} (작업 없음)")
        return
    with learning_session() as ldb:
        for fb in ldb.query(Feedback).filter(Feedback.job_id.in_(job_ids)).all():
            for suffix in (".json", ".jpg"):
                (settings.feedback_path / f"{fb.id}{suffix}").unlink(missing_ok=True)
            ldb.delete(fb)
        ldb.query(LearningSample).filter(LearningSample.job_id.in_(job_ids)).delete(synchronize_session=False)
        ldb.commit()
    print(f"정리: 계정 {username} · 작업 {len(job_ids)}건 · 배치 {len(batch_ids)}건")


with sync_playwright() as p:
    try:
        browser = p.chromium.launch()
    except Exception:
        browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 1280, "height": 860}, accept_downloads=True)
    page = ctx.new_page()
    watch(page, "app")
    _pages = [page]

    # ---------------- 비로그인
    def home():
        page.goto(APP + "/")
        expect(page.get_by_text("컷앤킵").first).to_be_visible()
        page.screenshot(path=SHOT / "01_home.png", full_page=True)
    step("비로그인 홈", home)

    def batch_locked():
        page.goto(APP + "/batch")
        expect(page.get_by_role("link", name="로그인").last).to_be_visible()
        page.screenshot(path=SHOT / "02_batch_locked.png")
    step("비로그인 배치 잠금", batch_locked)

    def guest_studio():
        page.goto(APP + "/studio")
        page.locator("input[type=file]").set_input_files(IMG)
        page.get_by_role("textbox").first.fill("사람만 남기고 배경 제거")
        page.get_by_role("button", name="처리 시작").click()
        expect(page.get_by_text("결과 저장").first).to_be_visible(timeout=180_000)
        expect(page.get_by_text("로그인하지 않은 작업은 서버에 남기지 않습니다", exact=False)).to_be_visible()
        with page.expect_download() as d:
            page.get_by_text("결과 저장").first.click()
        assert d.value.suggested_filename.startswith("cutnkeep_"), d.value.suggested_filename
        page.screenshot(path=SHOT / "03_guest_result.png", full_page=True)
    step("비로그인 작업실 처리 → 다운로드", guest_studio)

    # ---------------- 회원
    def signup():
        page.goto(APP + "/signup")
        inputs = page.locator("form input")  # 아이디 · 이메일 · 이름 · 비밀번호 · 확인 순
        expect(inputs).to_have_count(5, timeout=10_000)
        inputs.nth(0).fill(NAME)
        inputs.nth(1).fill(f"{NAME}@example.com")
        inputs.nth(3).fill("Passw0rd!ui")
        inputs.nth(4).fill("Passw0rd!ui")
        page.get_by_role("button", name="가입하기").click()
        expect(page.get_by_role("button", name="로그아웃")).to_be_visible(timeout=15_000)
        page.screenshot(path=SHOT / "04_after_signup.png")
    step("회원가입 → 로그인 상태", signup)

    def member_studio():
        page.goto(APP + "/studio")
        page.get_by_role("button", name="초기화").click()
        page.locator("input[type=file]").set_input_files(IMG)
        page.get_by_role("textbox").first.fill(PROMPT)
        page.get_by_role("button", name="처리 시작").click()
        expect(page.get_by_text("결과 저장").first).to_be_visible(timeout=180_000)
        page.get_by_role("button", name="좋아요").click()
        page.wait_for_timeout(1500)
        page.screenshot(path=SHOT / "05_member_result.png", full_page=True)
    step("회원 작업실 처리 → 좋아요", member_studio)

    def history():
        page.goto(APP + "/history")
        item = page.get_by_text(PROMPT).first
        expect(item).to_be_visible(timeout=15_000)
        page.screenshot(path=SHOT / "06_history.png", full_page=True)
        item.click()
        page.wait_for_url("**/jobs/**", timeout=10_000)
        expect(page.get_by_text(PROMPT).first).to_be_visible()
        page.screenshot(path=SHOT / "07_job_detail.png", full_page=True)
    step("작업 기록 → 상세", history)

    def member_batch():
        page.goto(APP + "/batch")
        second = sorted(glob.glob(str(ROOT / "training/datasets/cutnkeep_seg_5k/images/val/*.jpg")))[5]
        page.locator("input[type=file]").set_input_files([IMG, second])
        page.get_by_role("textbox").fill("사람만 남기고 배경 제거")
        page.get_by_role("button", name="2장 처리 시작").click()
        expect(page.get_by_text("결과 모두 받기 (zip)")).to_be_visible(timeout=240_000)
        expect(page.get_by_text("2 / 2 장")).to_be_visible()
        expect(page.get_by_text("24시간").first).to_be_visible()
        expect(page.get_by_text("준비 중인 기능")).to_have_count(0)
        # 결과 썸네일(원본 2 + 결과 2) 이 실제로 로드됐는지
        page.wait_for_function("document.querySelectorAll('li img').length >= 4")
        loaded = page.evaluate("[...document.querySelectorAll('li img')].filter(i => i.complete && i.naturalWidth > 0).length")
        assert loaded >= 4, f"썸네일 로드 {loaded}/4"
        page.screenshot(path=SHOT / "batch_done.png", full_page=True)
        with page.expect_download() as d:
            page.get_by_text("결과 모두 받기 (zip)").click()
        assert d.value.suggested_filename.endswith(".zip"), d.value.suggested_filename
        # 내 배치 목록에서 다시 열기
        page.goto(APP + "/batch")
        page.get_by_text("사람만 남기고 배경 제거").first.click()
        expect(page.get_by_text("결과 모두 받기 (zip)")).to_be_visible(timeout=15_000)
    step("회원 배치: 2장 처리 → 진행률 → 결과 썸네일 → zip → 내 배치 다시 열기", member_batch)

    def member_video():
        clip = make_video(SHOT / "clip.avi")
        page.goto(APP + "/video")
        expect(page.get_by_text("24시간 보관돼")).to_be_visible()
        page.locator("input[type=file]").set_input_files(str(clip))
        page.get_by_role("button", name="영상 처리 시작").click()
        expect(page.get_by_text("처리가 끝났어요")).to_be_visible(timeout=300_000)
        expect(page.get_by_text("서버에 보관됨")).to_be_visible()
        with page.expect_download() as d:
            page.get_by_text("결과 저장 (avi)").click()
        assert d.value.suggested_filename.endswith(".avi")
        page.screenshot(path=SHOT / "video_member.png", full_page=True)
    step("회원 영상: 처리 → 보관본 받기", member_video)

    def logout():
        page.get_by_role("button", name="로그아웃").click()
        expect(page.get_by_role("link", name="로그인").first).to_be_visible(timeout=10_000)
    step("로그아웃", logout)

    def guest_video():
        clip = SHOT / "clip.avi"
        page.goto(APP + "/video")
        expect(page.get_by_text("아무것도 남기지 않아요")).to_be_visible()
        page.locator("input[type=file]").set_input_files(str(clip))
        page.get_by_role("button", name="영상 처리 시작").click()
        expect(page.get_by_text("처리가 끝났어요")).to_be_visible(timeout=300_000)
        expect(page.get_by_text("서버에 저장되지 않았어요")).to_be_visible()
        with page.expect_download() as d:
            page.get_by_text("결과 저장 (avi)").click()
        assert d.value.suggested_filename == "cutnkeep_video.avi"
        import os
        saved = SHOT / "guest_result.avi"
        d.value.save_as(str(saved))
        assert os.path.getsize(saved) > 1000
    step("비로그인 영상: 처리 → 저장 안 됨 안내 → 파일 받기", guest_video)

    # ---------------- 콘솔
    con = ctx.new_page()
    watch(con, "console")
    _pages.append(con)

    def console_batches():
        con.goto(CONSOLE + "/")
        con.get_by_role("button", name="배치 현황").click()
        expect(con.get_by_text("사람만 남기고 배경 제거").first).to_be_visible(timeout=15_000)
        expect(con.get_by_text("2/2 · 100%").first).to_be_visible()
        assert con.locator("img").count() == 0  # 회원 사진은 운영 화면에 나오지 않음
        con.screenshot(path=SHOT / "console_batches.png", full_page=True)
    step("콘솔 배치 현황: 방금 배치 · 이미지 비노출", console_batches)

    def console_learning():
        con.goto(CONSOLE + "/")
        con.get_by_role("button", name="학습 데이터").click()
        expect(con.get_by_text("학습 데이터 검수")).to_be_visible()
        con.get_by_placeholder("예: 왼쪽 두 번째").fill(PROMPT[-6:])
        con.get_by_placeholder("예: 왼쪽 두 번째").press("Enter")
        # 요청 후보 + 좋아요가 1건으로 합쳐져야 한다 (출처 = 좋아요)
        expect(con.get_by_text(PROMPT)).to_have_count(1, timeout=10_000)
        expect(con.locator("tbody tr").filter(has_text=PROMPT).get_by_text("좋아요")).to_be_visible()
        con.screenshot(path=SHOT / "08_console_learning.png", full_page=True)
        con.get_by_title("정답 고쳐서 승인").first.click()
        editor = con.locator("textarea").first
        editor.fill("{not json")
        con.get_by_role("button", name="고쳐서 승인", exact=True).click()
        expect(con.get_by_text("정답이 올바른 JSON 이 아닙니다.")).to_be_visible()
        fixed = {"target": ["person"], "effect": "blur", "intensity": 33,
                 "selector": {"position": "center", "count": 1}}
        editor.fill(json.dumps(fixed))
        con.get_by_role("button", name="고쳐서 승인", exact=True).click()
        expect(con.get_by_text("정답을 고쳐 승인했습니다.")).to_be_visible(timeout=10_000)
        con.get_by_role("combobox").first.select_option("approved")
        expect(con.get_by_text(PROMPT)).to_have_count(1, timeout=10_000)
        con.screenshot(path=SHOT / "09_console_approved.png", full_page=True)
        con.once("dialog", lambda d: d.accept())
        con.get_by_title("삭제 (원본 파일 포함)").first.click()
        expect(con.get_by_text("삭제했습니다.")).to_be_visible(timeout=10_000)
        expect(con.get_by_text(PROMPT)).to_have_count(0)
    step("콘솔 학습 데이터: 검색 → JSON 오류 안내 → 고쳐 승인 → 삭제", console_learning)

    # ---------------- 모바일
    mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    mp = mobile.new_page()
    watch(mp, "mobile")

    def mobile_pages():
        for path, name in (("/", "10_mobile_home"), ("/studio", "11_mobile_studio")):
            mp.goto(APP + path)
            mp.wait_for_load_state("networkidle")
            overflow = mp.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            if overflow > 2:
                problems.append(f"[mobile] {path} 가로 넘침 {overflow}px")
            mp.screenshot(path=SHOT / f"{name}.png", full_page=True)
    step("모바일 홈·작업실 레이아웃", mobile_pages)
    browser.close()

print("\n".join(steps))
print(f"\n문제 {len(problems)}건")
for x in problems:
    print(" ", x)
cleanup(NAME)
sys.exit(1 if any(x.startswith("FAIL") for x in steps) or problems else 0)
