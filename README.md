# Dino Friends Storytime — free/open-source rebuild

This changes the channel from counting videos to short original moral-story episodes. It creates a different story on different UTC calendar days, renders four recurring stylized 3D characters in Blender, synthesizes narration with Piper, generates an original plucked-melody accompaniment in Python, assembles an MP4, creates a thumbnail, and uploads privately to YouTube.

## Character cast
- **Moss** — mint-green gentle longneck; thoughtful and calm.
- **Tilly** — coral-orange triceratops; brave and caring.
- **Rexi** — violet T-Rex; curious and learning from mistakes.
- **Pip** — sky-blue pterosaur; helpful and observant.

## Replace these repository files
1. `make_video.py`
2. `blender_scene.py`
3. `requirements.txt`
4. `.github/workflows/daily-video.yml`

Keep the existing `upload_youtube.py` and the GitHub secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, and `YT_REFRESH_TOKEN`. The workflow uses `UPLOAD_PRIVACY: private` so you can inspect videos before publishing.

## Run
GitHub → Actions → **Dino Friends Storytime** → Run workflow. After the run, download the `dino-storytime-output` artifact to review `video.mp4`, `thumbnail.jpg`, and `metadata.json`.

## Important limitations
- Narration is Piper text-to-speech, not genuine singing or character-specific voice acting.
- The accompaniment is original code-generated instrumental music, not a professionally recorded song.
- Characters are procedurally modelled 3D cartoon shapes, not studio-quality sculpted assets.
- The included stories rotate by UTC day among six original scripts. This is a starter story system, not an unlimited story-writing model. Expand the `STORIES` list in `make_video.py` to add more original episodes.
- No system can guarantee a video will go viral. Review each episode for quality, age appropriateness, pacing, and factual claims before making it public.

## Testing note
The scripts are designed for Blender 4.0's `BLENDER_EEVEE` engine. The complete render should still be tested in your GitHub runner because installed Blender packages, runner availability, and render performance can vary.
