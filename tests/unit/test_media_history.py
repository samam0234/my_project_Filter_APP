# -*- coding: utf-8 -*-
"""영상 · GIF 작업 기록과 GIF 처리.

- 회원 영상은 작업 기록(jobs, kind=video)에 남고 원본·결과·첫 프레임 썸네일을 본인만 받는다
- GIF: 프레임 수·간격·반복을 지키고, 배경 제거는 투명 GIF, 비로그인은 저장하지 않는다(data URL)
가짜 세그 모델(왼쪽·오른쪽 사람 2명)은 test_batch_api 와 같다.
"""

from __future__ import annotations

import base64
import io

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("cv2")
pytest.importorskip("PIL")

import cv2
import numpy as np
from PIL import Image

from test_batch_api import PW, TwoPeople, _avi_bytes, _signup, env  # noqa: F401 — fixture 재사용

H = W = 64


def _gif_bytes(n=4, duration=80, loop=0) -> bytes:
    frames = [Image.fromarray(np.full((H, W, 3), (30 + i * 40, 120, 200), np.uint8)) for i in range(n)]
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=duration, loop=loop)
    return buf.getvalue()


def _open_gif(data: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(data))
    assert im.format == "GIF"
    return im


# ---------- 서비스: GIF 처리 ----------


def test_process_gif_keeps_timing_and_makes_background_transparent():
    from app.schemas.request import ParsedPrompt
    from app.services.gif_processor import process_gif

    parsed = ParsedPrompt(target=["person"], effect="remove_bg")
    info = process_gif(_gif_bytes(n=4, duration=80, loop=0), parsed, TwoPeople(), smoothing="off")
    assert (info["frames"], info["total"], info["transparent"]) == (4, 4, True)
    im = _open_gif(info["data"])
    assert im.n_frames == 4
    assert im.info.get("duration") == 80 and im.info.get("loop") == 0
    rgba = np.array(im.convert("RGBA"))
    assert rgba[32, 30, 3] == 0  # 두 사람 사이(배경)는 투명
    assert rgba[32, 10, 3] == 255  # 사람은 남는다


def test_process_gif_selector_and_blur_is_opaque():
    from app.schemas.request import InstanceSelector, ParsedPrompt
    from app.services.gif_processor import process_gif

    left = ParsedPrompt(target=["person"], effect="remove_bg", selector=InstanceSelector(position="left", count=1))
    rgba = np.array(_open_gif(process_gif(_gif_bytes(n=2), left, TwoPeople(), smoothing="off")["data"]).convert("RGBA"))
    assert rgba[32, 10, 3] == 255 and rgba[32, 48, 3] == 0  # 왼쪽 사람만

    blur = ParsedPrompt(target=["person"], effect="blur", intensity=15)
    info = process_gif(_gif_bytes(n=2), blur, TwoPeople(), smoothing="off")
    assert info["transparent"] is False
    assert np.array(_open_gif(info["data"]).convert("RGBA"))[:, :, 3].min() == 255


def test_process_gif_frame_limit():
    from app.schemas.request import ParsedPrompt
    from app.services.gif_processor import process_gif

    info = process_gif(_gif_bytes(n=6), ParsedPrompt(target=["person"]), TwoPeople(), max_frames=3, smoothing="off")
    assert (info["frames"], info["total"]) == (3, 6)
    assert _open_gif(info["data"]).n_frames == 3


def test_read_gif_rejects_non_gif():
    from app.services.gif_processor import is_gif, read_gif

    ok, png = cv2.imencode(".png", np.zeros((8, 8, 3), np.uint8))
    assert not is_gif(png.tobytes())
    with pytest.raises(ValueError):
        read_gif(png.tobytes(), 10)


# ---------- API: GIF ----------


def test_gif_guest_gets_data_url_and_nothing_saved(env):
    r = env["client"].post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")},
                           data={"prompt": "사람만 남기고 배경 제거"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["saved"] is False and body["before_url"] is None
    assert body["after_url"].startswith("data:image/gif;base64,")
    assert _open_gif(base64.b64decode(body["after_url"].split(",", 1)[1])).n_frames == 4
    assert not (env["tmp"] / "uploads" / body["job_id"]).exists()


def test_gif_member_saved_in_history_and_private(env):
    c = env["client"]
    _signup(c, "gif_owner")
    r = c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")},
               data={"prompt": "왼쪽 사람만 남기고 배경 제거"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["saved"] is True and body["parsed_prompt"]["selector"]["position"] == "left"
    jobs = c.get("/api/v1/jobs").json()
    assert [(j["job_id"], j["kind"]) for j in jobs] == [(body["job_id"], "gif")]
    after = c.get(body["after_url"])
    assert after.status_code == 200 and after.headers["content-type"] == "image/gif"
    assert c.get(body["before_url"]).content[:6] in (b"GIF87a", b"GIF89a")
    assert c.get(jobs[0]["thumb_url"]).headers["content-type"] == "image/gif"  # 움직이는 썸네일

    c.post("/api/v1/auth/logout")
    _signup(c, "gif_other")
    assert c.get(body["after_url"]).status_code == 404
    assert c.get(f"/api/v1/jobs/{body['job_id']}").status_code == 404


def test_gif_rejects_bad_input(env):
    c = env["client"]
    png = cv2.imencode(".png", np.zeros((8, 8, 3), np.uint8))[1].tobytes()
    cases = [
        (("a.png", png, "image/png"), "GIF 파일"),
        (("a.gif", png, "image/gif"), "GIF 형식"),  # 확장자만 바꾼 파일
        (("a.gif", b"", "image/gif"), "빈 파일"),
    ]
    for file, expected in cases:
        r = c.post("/api/v1/gif", files={"file": file}, data={"prompt": "사람만 남기고 배경 제거"})
        assert r.status_code == 400 and expected in r.json()["detail"], (file[0], r.text)


# ---------- API: 영상 작업 기록 ----------


def test_member_video_appears_in_history_with_thumb(env):
    c = env["client"]
    _signup(c, "vid_hist")
    r = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")},
               data={"prompt": "사람만 남기고 배경 블러"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["parsed_prompt"]["effect"] == "blur"
    jobs = c.get("/api/v1/jobs").json()
    assert len(jobs) == 1
    job = jobs[0]
    assert (job["job_id"], job["kind"], job["status"]) == (body["job_id"], "video", "ok")
    assert c.get(job["after_url"]).headers["content-type"] == "video/mp4"
    assert c.get(job["before_url"]).status_code == 200  # 원본 영상
    thumb = c.get(job["thumb_url"])
    assert thumb.status_code == 200 and thumb.headers["content-type"] == "image/jpeg"
    assert c.get(f"/api/v1/jobs/{job['job_id']}").json()["kind"] == "video"


def test_guest_video_not_in_history(env):
    c = env["client"]
    r = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")},
               data={"prompt": "사람만 남기고 배경 블러"})
    assert r.status_code == 200
    _signup(c, "vid_after_guest")
    assert c.get("/api/v1/jobs").json() == []


def test_image_jobs_report_kind_image(env):
    c = env["client"]
    _signup(c, "img_kind")
    ok, jpg = cv2.imencode(".jpg", np.full((H, W, 3), 90, np.uint8))
    r = c.post("/api/v1/upload", files={"file": ("p.jpg", jpg.tobytes(), "image/jpeg")}, data={"prompt": "사람만 남기고 배경 제거"})
    assert r.status_code == 200, r.text
    job = c.get("/api/v1/jobs").json()[0]
    assert job["kind"] == "image" and job["thumb_url"].endswith("/thumb")
    assert c.get(job["thumb_url"]).status_code == 200


def test_deleting_member_removes_video_and_gif_jobs(env):
    from app.models.job import Job

    c = env["client"]
    _signup(c, "media_del")
    c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")}, data={"prompt": "사람 블러"})
    c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")}, data={"prompt": "사람만 남기고 배경 제거"})
    with env["Session"]() as db:
        rows = db.query(Job).all()
        user_id = rows[0].user_id
        assert sorted(r.kind for r in rows) == ["gif", "video"]
    r = c.request("DELETE", f"/api/v1/console/users/{user_id}", json={"confirm": "media_del"})
    assert r.status_code == 200, r.text
    with env["Session"]() as db:
        assert db.query(Job).count() == 0
    uploads = env["tmp"] / "uploads"
    assert list((uploads / "videos").glob("*")) == []  # 영상 폴더(owner.json 기준)
    assert [p.name for p in uploads.iterdir() if p.is_dir() and p.name not in {"videos", "batches"}] == []  # GIF 폴더


def test_console_serves_video_and_gif_files(env):
    """운영 콘솔(소유자 무관)도 영상·GIF 작업의 원본·결과·썸네일을 보여 준다."""
    c = env["client"]
    _signup(c, "media_console")
    gif = c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")}, data={"prompt": "사람만 남기고 배경 제거"}).json()
    vid = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")}, data={"prompt": "사람 블러"}).json()
    jobs = {j["job_id"]: j for j in c.get("/api/v1/console/jobs").json()}
    assert jobs[gif["job_id"]]["thumb_url"] == f"/api/v1/console/files/{gif['job_id']}/thumb"
    assert c.get(jobs[gif["job_id"]]["after_url"]).headers["content-type"] == "image/gif"
    assert c.get(jobs[vid["job_id"]]["after_url"]).headers["content-type"] == "video/mp4"
    assert c.get(jobs[vid["job_id"]]["thumb_url"]).headers["content-type"] == "image/jpeg"
    assert c.get("/api/v1/console/files/nope/after").status_code == 404
    assert c.get(f"/api/v1/console/files/{gif['job_id']}/secret").status_code == 404


# ---------- 품질: GIF 배경 제거의 WebP · 영상 원본 미리 보기 ----------


def test_transparent_gif_also_makes_webp_with_soft_edges():
    """GIF 는 1비트 투명이라 경계가 0/255 뿐 — 같은 프레임의 WebP 는 반투명 경계를 담는다."""
    from app.schemas.request import ParsedPrompt
    from app.services.gif_processor import process_gif

    info = process_gif(_gif_bytes(n=3, duration=70), ParsedPrompt(target=["person"], effect="remove_bg"), TwoPeople(), smoothing="off")
    gif_alpha = np.unique(np.array(_open_gif(info["data"]).convert("RGBA"))[:, :, 3])
    assert set(gif_alpha.tolist()) <= {0, 255}
    webp = Image.open(io.BytesIO(info["webp"]))
    assert webp.format == "WEBP" and webp.n_frames == 3
    alpha = np.array(webp.convert("RGBA"))[:, :, 3]
    assert alpha[32, 30] == 0 and alpha[32, 10] > 200  # 배경 투명 · 사람 남음
    assert ((alpha > 0) & (alpha < 255)).any()  # 반투명 경계가 남아 있다

    blur = process_gif(_gif_bytes(n=2), ParsedPrompt(target=["person"], effect="blur"), TwoPeople(), smoothing="off")
    assert blur["webp"] is None  # 불투명 결과는 GIF 로 충분


def test_gif_api_returns_webp_for_guest_and_member(env):
    c = env["client"]
    guest = c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")}, data={"prompt": "사람만 남기고 배경 제거"}).json()
    assert guest["webp_url"].startswith("data:image/webp;base64,")
    _signup(c, "gif_webp")
    body = c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")}, data={"prompt": "사람만 남기고 배경 제거"}).json()
    assert body["webp_url"] == f"/api/v1/files/{body['job_id']}/webp"
    got = c.get(body["webp_url"])
    assert got.status_code == 200 and got.headers["content-type"] == "image/webp"
    assert c.get("/api/v1/jobs").json()[0]["webp_url"] == body["webp_url"]
    blur = c.post("/api/v1/gif", files={"file": ("a.gif", _gif_bytes(), "image/gif")}, data={"prompt": "사람만 남기고 배경 블러"}).json()
    assert blur["webp_url"] is None
    assert c.get(f"/api/v1/files/{blur['job_id']}/webp").status_code == 404


def test_member_avi_original_gets_playable_mp4_preview(env):
    """avi 원본은 브라우저가 못 연다 — 작업 기록의 원본은 mp4 미리 보기로 (원본 파일은 남긴다)."""
    c = env["client"]
    _signup(c, "vid_preview")
    body = c.post("/api/v1/video", files={"file": ("clip.avi", _avi_bytes(env["tmp"]), "video/avi")}, data={"prompt": "사람 블러"}).json()
    before = c.get(f"/api/v1/files/{body['job_id']}/before")
    assert before.status_code == 200 and before.headers["content-type"] == "video/mp4"
    assert before.content[4:8] == b"ftyp"
    root = env["tmp"] / "uploads" / "videos" / body["job_id"]
    assert (root / "in.avi").is_file() and (root / "original.mp4").is_file()


# ---------- 품질: 대상 지우기 빈자리 메우기 ----------


def test_remove_object_engine_choice_and_fallback(monkeypatch, tmp_path):
    """LaMa 모델이 없으면 Telea 로 내려가고, 영상·GIF 프레임은 항상 Telea (프레임마다 1초씩 걸리지 않게)."""
    from app.services import effects, inpaint
    from app.schemas.request import ParsedPrompt
    from app.services.video_processor import FrameRenderer

    img = np.full((64, 64, 3), 120, np.uint8)
    mask = np.zeros((64, 64), np.uint8)
    mask[20:40, 20:40] = 255
    calls = []
    monkeypatch.setattr(inpaint, "lama_inpaint", lambda i, m, settings=None: calls.append("lama") or None)  # 모델 없음 흉내
    out = effects.apply_remove_object(img, mask, engine="auto")
    assert calls == ["lama"] and out.shape == img.shape  # LaMa 를 시도했다가 Telea 로

    calls.clear()
    effects.apply_remove_object(img, mask, engine="telea")
    assert calls == []

    calls.clear()
    renderer = FrameRenderer(ParsedPrompt(target=["person"], effect="remove_object"), TwoPeople(), smoothing="off")
    renderer.render(np.full((H, W, 3), 90, np.uint8))
    assert calls == []  # 프레임은 Telea


def test_lama_inpaint_pastes_only_hole(monkeypatch):
    """LaMa 결과는 마스크 영역만 원본에 합성한다 (나머지 픽셀은 원본 그대로)."""
    from app.services import inpaint

    class FakeSession:
        def get_inputs(self):
            return [type("I", (), {"name": "image"})(), type("I", (), {"name": "mask"})()]

        def run(self, _out, feeds):
            return [np.full((1, 3, 512, 512), 200.0, np.float32)]  # 출력 0~255

    monkeypatch.setattr(inpaint, "_session", lambda settings: FakeSession())
    img = np.full((300, 400, 3), 50, np.uint8)
    mask = np.zeros((300, 400), np.uint8)
    mask[100:150, 150:200] = 255
    out = inpaint.lama_inpaint(img, mask)
    assert (out[mask > 0] == 200).all()
    assert (out[mask == 0] == 50).all()
