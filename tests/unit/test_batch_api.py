# -*- coding: utf-8 -*-
"""배치 · 영상: 단일 업로드와 같은 파이프라인(인스턴스 선택 포함)을 타고, 결과를 본인만 받는다.

가짜 세그 모델(왼쪽·오른쪽 사람 2명)을 공용 싱글톤 자리에 넣어 모델 파일 없이 검증한다.
"""

from __future__ import annotations

import io
import zipfile

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("cv2")

import cv2
import numpy as np

from app.core.config import get_settings
from app.services.image_processor import ImageProcessor
from app.services.segmentation import Instance, SegmentationResult, union_mask

PW = "cutkeep2026"
H = W = 64


class TwoPeople:
    """왼쪽(x 4~20)·오른쪽(x 40~56) 사람 2명을 항상 찾는다."""

    def __init__(self):
        self.calls = 0

    def predict(self, image, targets=None, min_confidence=None):
        self.calls += 1
        h, w = image.shape[:2]
        left, right = np.zeros((h, w), np.uint8), np.zeros((h, w), np.uint8)
        left[8:56, 4:20] = 255
        right[8:56, 40:56] = 255
        insts = [Instance.from_mask(left, "person", 0.9), Instance.from_mask(right, "person", 0.9)]
        return SegmentationResult(
            mask=union_mask(insts, (h, w)), confidences=[0.9, 0.9], labels=["person", "person"],
            backend="fake", detected=["person", "person"], instances=insts,
        )


def _jpeg(color=(40, 160, 80)) -> bytes:
    ok, buf = cv2.imencode(".jpg", np.full((H, W, 3), color, np.uint8))
    return buf.tobytes()


@pytest.fixture()
def env(api_env, monkeypatch, tmp_path):
    from app.workflows import nodes

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "llm_provider", "heuristic")  # 네트워크(Ollama) 없이 키워드 해석
    monkeypatch.setattr(settings, "console_allow_remote", True)
    seg = TwoPeople()
    monkeypatch.setattr(nodes, "_processor", ImageProcessor(settings, segmentor=seg))
    # 백그라운드 워커가 테스트용 메모리 DB 를 쓰도록 (운영에서는 같은 전역 DB)
    from functools import partial

    from app.routers import batch as batch_router
    from app.tasks import batch_tasks

    monkeypatch.setattr(batch_router, "run_batch_job", partial(batch_tasks.run_batch_job, session_factory=api_env["Session"]))
    api_env["seg"] = seg
    api_env["tmp"] = tmp_path
    return api_env


def _signup(client, name):
    r = client.post("/api/v1/auth/signup", json={"username": name, "email": f"{name}@example.com", "password": PW})
    assert r.status_code == 201, r.text


def _batch(client, prompt="왼쪽 사람만 남기고 배경 제거", n=2):
    files = [("files", (f"photo{i}.jpg", _jpeg(), "image/jpeg")) for i in range(n)]
    r = client.post("/api/v1/batch", files=files, data={"prompt": prompt})
    assert r.status_code == 200, r.text
    return r.json()["job_id"]


def test_batch_honors_selector_like_single_upload(env):
    c = env["client"]
    _signup(c, "batch_01")
    job = _batch(c)  # TestClient 는 BackgroundTasks 를 응답 직후 끝까지 실행
    st = c.get(f"/api/v1/batch/{job}").json()
    assert (st["status"], st["completed"], st["total"]) == ("done", 2, 2)
    assert st["download_url"] and st["prompt"].startswith("왼쪽")
    item = st["item_results"][0]
    assert item["status"] == "ok" and item["backend"] == "fake" and item["output"].endswith(".png")
    out = c.get(item["after_url"])
    assert out.status_code == 200
    img = cv2.imdecode(np.frombuffer(out.content, np.uint8), cv2.IMREAD_UNCHANGED)
    alpha = img[:, :, 3]
    assert alpha[:, 4:20].max() == 255 and alpha[:, 40:56].max() == 0  # 왼쪽 사람만 남음 (배경 투명)
    # 문장은 한 번만 해석해 모든 장에 쓰고, 세그는 장마다 한 번 (재시도 없음)
    assert env["seg"].calls == 2


def test_batch_original_and_zip_download(env):
    c = env["client"]
    _signup(c, "batch_02")
    job = _batch(c, n=3)
    st = c.get(f"/api/v1/batch/{job}").json()
    before = c.get(st["item_results"][1]["before_url"])
    assert before.status_code == 200 and before.content[:2] == b"\xff\xd8"  # 업로드한 JPEG 그대로
    z = c.get(st["download_url"])
    assert z.status_code == 200 and z.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert sorted(names) == ["photo0_result.png", "photo1_result.png", "photo2_result.png"]


def test_batch_list_is_mine_and_images_are_private(env):
    c = env["client"]
    _signup(c, "owner_b")
    job = _batch(c)
    assert [b["job_id"] for b in c.get("/api/v1/batch").json()] == [job]
    c.post("/api/v1/auth/logout")
    _signup(c, "other_b")
    assert c.get("/api/v1/batch").json() == []
    assert c.get(f"/api/v1/batch/{job}/items/0/after").status_code == 404
    assert c.get(f"/api/v1/batch/{job}/items/0/before").status_code == 404
    assert c.get(f"/api/v1/batch/{job}/download").status_code == 404
    c.post("/api/v1/auth/logout")
    assert c.get(f"/api/v1/batch/{job}/download").status_code == 401  # 비로그인


def test_batch_image_route_rejects_bad_input(env):
    c = env["client"]
    _signup(c, "batch_03")
    job = _batch(c, n=1)
    assert c.get(f"/api/v1/batch/{job}/items/9/after").status_code == 404  # 없는 항목
    assert c.get(f"/api/v1/batch/{job}/items/0/secret").status_code == 422  # before|after 만
    assert c.get(f"/api/v1/batch/{job}/items/-1/before").status_code == 404


def test_batch_failed_item_does_not_stop_others(env):
    c = env["client"]
    _signup(c, "batch_04")
    # JPEG 시그니처는 맞아 업로드 검증을 통과하지만 디코딩할 수 없는 파일 (중간 실패의 현실적인 경우)
    files = [
        ("files", ("good.jpg", _jpeg(), "image/jpeg")),
        ("files", ("broken.jpg", bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b" truncated", "image/jpeg")),
        ("files", ("good2.jpg", _jpeg(), "image/jpeg")),
    ]
    r = c.post("/api/v1/batch", files=files, data={"prompt": "왼쪽 사람만 남기고 배경 제거"})
    assert r.status_code == 200, r.text
    st = c.get(f"/api/v1/batch/{r.json()['job_id']}").json()
    assert (st["status"], st["completed"], st["total"]) == ("done", 3, 3)
    assert "실패 1/3" in st["message"]
    assert [i["status"] for i in st["item_results"]] == ["ok", "failed", "ok"]  # 가운데 실패가 뒤를 막지 않음
    bad = st["item_results"][1]
    assert bad["output"] is None and bad["after_url"] is None and bad["filename"] == "broken.jpg"


def test_batch_rejects_non_image_content(env):
    """확장자·MIME 만 이미지인 파일은 등록 단계에서 거절 (배치 중간에 터지지 않게)."""
    c = env["client"]
    _signup(c, "batch_05")
    r = c.post("/api/v1/batch", files=[("files", ("fake.jpg", b"plain text, not an image", "image/jpeg"))],
               data={"prompt": "사람만"})
    assert r.status_code == 400 and "이미지 파일이 아닙니다" in r.text
    assert c.get("/api/v1/batch").json() == []  # 배치 행도 남기지 않음


def test_video_applies_selector_per_frame(tmp_path):
    from app.schemas.request import ParsedPrompt, InstanceSelector
    from app.services.video_processor import process_video

    src = tmp_path / "in.avi"
    w = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (W, H))
    for _ in range(3):
        w.write(np.full((H, W, 3), 120, np.uint8))
    w.release()

    class Spy(TwoPeople):
        pass

    parsed = ParsedPrompt(target=["person"], effect="blur", intensity=50,
                          selector=InstanceSelector(position="left", count=1))
    info = process_video(src, tmp_path / "out", parsed, Spy(), max_frames=10, max_seconds=5)
    assert info["frames"] == 3 and info["held"] == 0
    assert info["format"] == "webm" and info["path"].endswith(".webm")
    out = cv2.VideoCapture(info["path"])
    ok, frame = out.read()
    out.release()
    assert ok and frame.shape[:2] == (H, W)


def test_video_route_uses_shared_segmentor(env, monkeypatch, tmp_path):
    """요청마다 Segmentor 를 새로 만들지 않고 프로세스 공용 모델을 쓴다."""
    from app.routers import video as video_router
    from app.services.segmentation import Segmentor

    def boom(*a, **k):
        raise AssertionError("영상 요청이 세그 모델을 새로 로드했다")

    monkeypatch.setattr(Segmentor, "__init__", boom)
    c = env["client"]
    path = tmp_path / "v.avi"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (W, H))
    for _ in range(2):
        w.write(np.full((H, W, 3), 90, np.uint8))
    w.release()
    r = c.post("/api/v1/video", files={"file": ("v.avi", path.read_bytes(), "video/x-msvideo")},
               data={"prompt": "왼쪽 사람만 남기고 배경 블러"})
    assert r.status_code == 200, r.text
    assert r.headers["X-Cutnkeep-Frames"] == "2"
    assert env["seg"].calls == 2
    assert video_router  # import 확인


def test_video_guest_gets_browser_playable_webm(env):
    """비로그인 응답은 브라우저 <video> 로 바로 재생되는 webm."""
    r = env["client"].post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")},
                           data={"prompt": "사람만 남기고 배경 블러"})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "video/webm"
    assert r.headers["X-Cutnkeep-Format"] == "webm"
    assert "result.webm" in r.headers["content-disposition"]
    assert r.content[:4] == bytes([0x1A, 0x45, 0xDF, 0xA3])  # EBML (webm)


def test_video_member_result_is_webm(env):
    c = env["client"]
    _signup(c, "vid_webm")
    r = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")},
               data={"prompt": "사람만 남기고 배경 블러"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "webm"
    got = c.get(body["url"])
    assert got.status_code == 200 and got.headers["content-type"] == "video/webm"


def test_video_falls_back_to_avi_without_vp8(tmp_path, monkeypatch):
    """VP8 인코더가 없는 OpenCV 빌드면 MJPG avi 로 내려간다."""
    from app.schemas.request import ParsedPrompt
    from app.services import video_processor

    monkeypatch.setitem(video_processor._FORMATS, "webm", (".webm", "ZZZZ", "video/webm"))
    src = tmp_path / "in.avi"
    src.write_bytes(_avi_bytes(tmp_path))
    info = video_processor.process_video(src, tmp_path / "out", ParsedPrompt(target=["person"], effect="blur"),
                                         TwoPeople(), max_frames=5, max_seconds=5)
    assert info["format"] == "avi" and info["media_type"] == "video/x-msvideo"
    assert not (tmp_path / "out.webm").exists()


def _avi_bytes(tmp_path) -> bytes:
    path = tmp_path / "t.avi"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (W, H))
    for _ in range(2):
        w.write(np.full((H, W, 3), 90, np.uint8))
    w.release()
    return path.read_bytes()


@pytest.mark.parametrize("mime", ["video/x-msvideo", "video/avi", "video/msvideo", "application/octet-stream"])
def test_video_accepts_the_mime_types_browsers_actually_send(env, mime):
    """.avi 는 브라우저·OS 마다 MIME 이 다르다 — 실제 브라우저가 video/avi 를 보내 모든 avi 가 거절되던 문제 (UI 확인에서 발견)."""
    r = env["client"].post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), mime)},
                           data={"prompt": "왼쪽 사람만 남기고 배경 블러"})
    assert r.status_code == 200, r.text


def test_video_rejects_non_video_content_and_mime(env):
    c = env["client"]
    fake = c.post("/api/v1/video", files={"file": ("clip.mp4", b"this is not a video at all", "video/mp4")},
                  data={"prompt": "사람만"})
    assert fake.status_code == 400 and "영상 파일이 아닙니다" in fake.text
    wrong_mime = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "image/jpeg")},
                        data={"prompt": "사람만"})
    assert wrong_mime.status_code == 400
    wrong_ext = c.post("/api/v1/video", files={"file": ("clip.gif", _avi_bytes(env["tmp"]), "video/avi")},
                       data={"prompt": "사람만"})
    assert wrong_ext.status_code == 400


def test_video_signature_formats():
    from app.core.security import validate_video_signature
    from app.exceptions import FileValidationError

    assert validate_video_signature(b"RIFF\x00\x00\x00\x00AVI LIST") == "AVI"
    assert validate_video_signature(b"\x00\x00\x00\x18ftypmp42") == "MP4"
    assert validate_video_signature(b"\x00\x00\x00\x08moov....") == "MP4"
    assert validate_video_signature(bytes([0x1A, 0x45, 0xDF, 0xA3]) + b"webm") == "WEBM"
    for bad in (b"", b"RIFF\x00\x00\x00\x00WAVEfmt ", b"GIF89a", b"plain text file"):
        with pytest.raises(FileValidationError):
            validate_video_signature(bad)


def test_cors_exposes_video_headers(env):
    r = env["client"].options(
        "/api/v1/video",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    r2 = env["client"].get("/health", headers={"Origin": "http://localhost:5173"})
    exposed = r2.headers.get("access-control-expose-headers", "")
    assert "X-Cutnkeep-Frames" in exposed and "Content-Disposition" in exposed and "X-Cutnkeep-Format" in exposed
    assert r.status_code in {200, 204}


def test_console_lists_all_batches_without_images(env):
    c = env["client"]
    _signup(c, "cons_a")
    job = _batch(c)
    c.post("/api/v1/auth/logout")
    _signup(c, "cons_b")
    _batch(c, n=1)
    rows = c.get("/api/v1/console/batches").json()  # 콘솔은 소유자 무관 전체
    assert len(rows) == 2 and {r["status"] for r in rows} == {"done"}
    mine = next(r for r in rows if r["job_id"] == job)
    assert (mine["total"], mine["completed"], mine["failed"]) == (2, 2, 0)
    assert mine["user_id"] and mine["prompt"].startswith("왼쪽")
    assert "item_results" not in mine and not any("url" in k for k in mine)  # 이미지 주소는 내려주지 않음


def test_console_batches_is_local_only(env, monkeypatch):
    monkeypatch.setattr(get_settings(), "console_allow_remote", False)
    assert env["client"].get("/api/v1/console/batches").status_code == 403


def test_enqueue_falls_back_in_process_when_redis_is_down(monkeypatch):
    """Redis 가 꺼져 .delay() 가 예외를 내도 요청이 500 이 되거나 배치가 queued 로 남지 않는다."""
    from app.tasks import batch_tasks

    class Down:
        def delay(self, job_id):
            raise ConnectionError("Error 111 connecting to redis:6379")

    monkeypatch.setattr(get_settings(), "batch_use_celery", True)
    monkeypatch.setattr(batch_tasks, "celery", object())
    monkeypatch.setattr(batch_tasks, "run_batch_job_task", Down())
    assert batch_tasks.enqueue_batch("job1") is False  # 호출측이 BackgroundTasks 로 직접 처리


def test_enqueue_uses_celery_when_available(monkeypatch):
    from app.tasks import batch_tasks

    sent = []

    class Queue:
        def delay(self, job_id):
            sent.append(job_id)

    monkeypatch.setattr(get_settings(), "batch_use_celery", True)
    monkeypatch.setattr(batch_tasks, "celery", object())
    monkeypatch.setattr(batch_tasks, "run_batch_job_task", Queue())
    assert batch_tasks.enqueue_batch("job2") is True and sent == ["job2"]


def test_worker_session_is_bound_without_app_startup(monkeypatch):
    """Celery 워커는 lifespan(init_db)을 거치지 않는다 — 기본 세션이 스스로 엔진에 연결돼야 한다."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.tasks import batch_tasks

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    unbound = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False)  # 연결 전 상태
    monkeypatch.setattr(batch_tasks, "SessionLocal", unbound)
    monkeypatch.setattr(batch_tasks, "get_engine", lambda: engine)
    session = batch_tasks._default_session()
    try:
        assert session.get_bind() is engine
    finally:
        session.close()
