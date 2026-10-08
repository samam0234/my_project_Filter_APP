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
