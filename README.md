# Dino Daily Video — simple GitHub Actions starter

This repository creates an original, short dinosaur counting video, a custom thumbnail, and uploads the video to your YouTube channel. It runs every day at **4:00 PM India time** and can also be started manually.

## What this version does

- Uses a built-in original counting script (no Gemini API calls, so Gemini outages/quotas won't stop generation).
- Generates spoken narration with Piper text-to-speech.
- Draws simple dinosaur scenes and a thumbnail locally; no stock images or external art are needed.
- Builds `output/video.mp4`, `output/thumbnail.jpg`, and `output/metadata.json`.
- Uploads the video to YouTube and declares it made for kids.
- Defaults to **private** so you can review each video before publishing.

> This starter makes a narrated slideshow with illustrated dinosaur scenes, not a full 3D animation or sung song. Review videos before making them public. YouTube API access and thumbnail eligibility depend on your Google/YouTube account and project setup.

## 1. Create the GitHub repository

1. Create a new repository on GitHub, for example `dino-daily-channel`.
2. Choose **Public** or **Private**. Private is fine.
3. Upload all files and folders from this starter ZIP, preserving `.github/workflows/daily-video.yml`.
4. Commit the files to the default branch (usually `main`).

## 2. Add YouTube credentials as GitHub Actions secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret**. Add these three secrets exactly:

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Use the OAuth client ID, client secret, and refresh token from the Google Cloud project / YouTube OAuth setup you already prepared. The refresh token must authorize the YouTube channel you want to upload to and include the YouTube upload scope. Never put credentials directly in code or commit them to GitHub.

`GEMINI_API_KEY` is not required for this simplified version.

## 3. Choose upload privacy

The workflow defaults to `private`, which is safest while testing. To change it, open **Settings → Secrets and variables → Actions → Variables → New repository variable** and create:

- Name: `UPLOAD_PRIVACY`
- Value: `private`, `unlisted`, or `public`

Keep it `private` for the first successful test. Change to `public` only after you have reviewed the generated video and are happy for scheduled videos to publish automatically.

## 4. Run a test

1. Open the repository's **Actions** tab.
2. Select **Create and upload Dino video**.
3. Click **Run workflow**.
4. Open the running job and review the logs.
5. When it completes, check YouTube Studio → Content. With the default setting, the video should be private.

The first run downloads the Piper voice model and may take longer. GitHub Actions caches the model for later runs.

## 5. Daily schedule

The workflow schedule is `30 10 * * *` UTC, which is 4:00 PM India time. GitHub may delay scheduled runs during heavy load. You can always start a run manually from Actions.

## Files

```text
.github/workflows/daily-video.yml  # Daily/manual GitHub Actions workflow
make_video.py                       # Narration, illustrated scenes, video, thumbnail
upload_youtube.py                   # YouTube upload
requirements.txt                    # Python dependencies
.gitignore
README.md
```

## Troubleshooting

- **Missing secrets:** confirm all three secret names are spelled exactly as above.
- **OAuth / invalid_grant:** the refresh token may be expired, revoked, issued for a different OAuth client, or missing the YouTube upload scope; create a new valid refresh token for the same client.
- **YouTube API not enabled:** enable **YouTube Data API v3** in the Google Cloud project associated with the OAuth client.
- **Upload rejected:** check YouTube API quota, channel restrictions, and account verification. A video may upload even if custom thumbnail setting fails; the log will say so.
- **Voice download fails:** rerun the workflow; the download step retries automatically. If the model host is unavailable, the workflow will stop before upload rather than upload an empty video.

## Important

This project uploads content to YouTube. Start with `UPLOAD_PRIVACY=private`, inspect the output and metadata, and only then consider automated public uploads. Make sure the channel's audience settings, content labels, and any legal requirements are correct for your actual content.
