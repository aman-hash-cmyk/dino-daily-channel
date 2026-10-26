#!/usr/bin/env python3
"""Upload output/video.mp4 and its thumbnail to the authenticated YouTube channel."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> None:
    client_id = os.getenv("YT_CLIENT_ID", "").strip()
    client_secret = os.getenv("YT_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YT_REFRESH_TOKEN", "").strip()
    if not all((client_id, client_secret, refresh_token)):
        raise RuntimeError("Missing YouTube credentials. Add YT_CLIENT_ID, YT_CLIENT_SECRET, and YT_REFRESH_TOKEN as GitHub Actions secrets.")

    video_path = OUT / "video.mp4"
    thumb_path = OUT / "thumbnail.jpg"
    metadata_path = OUT / "metadata.json"
    for p in (video_path, thumb_path, metadata_path):
        if not p.is_file() or p.stat().st_size == 0:
            raise FileNotFoundError(f"Required generated file is missing or empty: {p}")

    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    privacy = os.getenv("UPLOAD_PRIVACY", "private").strip().lower()
    if privacy not in {"private", "unlisted", "public"}:
        raise ValueError("UPLOAD_PRIVACY must be private, unlisted, or public.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"][:5000],
            "tags": meta.get("tags", [])[:500],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": True,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%", flush=True)

    video_id = response.get("id")
    if not video_id:
        raise RuntimeError(f"YouTube did not return a video ID: {response}")
    print(f"Uploaded video: https://www.youtube.com/watch?v={video_id}", flush=True)

    try:
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb_path), mimetype="image/jpeg")).execute()
        print("Custom thumbnail uploaded.", flush=True)
    except Exception as exc:
        # Keep a successful video upload even if thumbnail upload is rejected (for example, channel eligibility).
        print(f"WARNING: Video uploaded, but custom thumbnail failed: {exc}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
