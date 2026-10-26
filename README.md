# Dino: free/open-source 3D-style video pipeline

This replaces the earlier flat illustration generator with a Blender-rendered, brightly coloured, animated dinosaur scene. It generates original synthetic instrumental accompaniment and uses Piper for rhythmic spoken lines. **Piper is speech, not singing**; this free-only build does not claim to generate a genuine sung vocal. It uses no paid API and downloads no commercial music/artwork.

## What it creates
- A 36-second, 1280×720 animated scene with five distinct stylized 3D dinosaur silhouettes, shiny materials, lighting, bounce/sway motion, floating sparkles and a changing 1–10 count.
- Original synthesized bouncy accompaniment plus spoken rhyming action prompts (stomp, clap, wiggle, flap).
- `output/video.mp4`, `output/thumbnail.jpg`, `output/metadata.json` for the existing YouTube uploader.
- YouTube upload stays **private** in the workflow.

## Replace files in your existing GitHub repository
Keep your existing repository and the three GitHub secrets. Replace/add these files at the exact paths shown:

1. Replace `make_video.py` with this package's `make_video.py`.
2. Replace `requirements.txt`.
3. Replace `.github/workflows/daily-video.yml` with the version here.
4. Add `blender_scene.py` at the repository root.
5. Replace `upload_youtube.py` with the included copy only if you want to ensure it matches this package; otherwise your existing uploader can remain.

Do not upload the whole ZIP as a single file and expect GitHub to unpack it. Extract it on your computer first, then upload/replace each file in its matching location.

## Run a test
1. Open your GitHub repository → **Actions**.
2. Select **Dino 3D episode**.
3. Click **Run workflow**.
4. Wait for the job to finish. Open the run and check **Generate animated episode**.
5. Download the `dino-video-output` artifact from the completed run to preview the video and thumbnail. The upload step remains private.

## Important limits
- This pipeline uses a procedurally modelled, 3D-rendered cartoon scene, not studio-quality character animation. Dinosaur forms are assembled from Blender primitives, so the style is polished/stylized rather than a fully sculpted film character.
- The free Piper voice speaks the lyrics rhythmically; it does not sing. The accompaniment is algorithmically synthesized and is intentionally simple. True natural singing and high-end bespoke 3D character art generally require a more involved model/workflow or paid resources.
- First run may take several minutes because Blender renders hundreds of frames. The GitHub Actions job has a 120-minute limit.
