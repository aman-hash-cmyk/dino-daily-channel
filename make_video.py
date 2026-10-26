#!/usr/bin/env python3
"""Create a short, original dinosaur counting video and thumbnail."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = ROOT / "work"
AUDIO = WORK / "audio"
FRAMES = WORK / "frames"
CLIPS = WORK / "clips"
VOICE = os.getenv("PIPER_VOICE", str(ROOT / "voices" / "en_US-lessac-medium.onnx"))
VOICE_CONFIG = os.getenv("PIPER_CONFIG", VOICE + ".json")
PIPER_BIN = os.getenv("PIPER_BIN", "piper")
FFMPEG = os.getenv("FFMPEG", "ffmpeg")
W, H = 1280, 720

DINOS = [
    ("Stegosaurus", (87, 181, 116)),
    ("Triceratops", (255, 190, 83)),
    ("Pterodactyl", (161, 127, 220)),
    ("Brontosaurus", (64, 183, 190)),
    ("Tyrannosaurus Rex", (239, 132, 103)),
]
NUMBER_WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


def require_tools() -> None:
    if not shutil.which(PIPER_BIN):
        raise RuntimeError("Piper is not installed. Check requirements.txt and the workflow install step.")
    if not shutil.which(FFMPEG):
        raise RuntimeError("ffmpeg was not found on PATH.")
    if not Path(VOICE).is_file():
        raise RuntimeError(f"Piper model is missing: {VOICE}")
    if not Path(VOICE_CONFIG).is_file():
        raise RuntimeError(f"Piper config is missing: {VOICE_CONFIG}")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap_words(draw: ImageDraw.ImageDraw, text: str, use_font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=use_font)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_dino(draw: ImageDraw.ImageDraw, name: str, color: tuple[int, int, int], cx: int, cy: int, scale: float = 1.0) -> None:
    # Friendly, simple vector dinosaur made from shapes (no external artwork needed).
    def box(x1, y1, x2, y2):
        return (int(x1), int(y1), int(x2), int(y2))
    body = box(cx - 160*scale, cy - 20*scale, cx + 95*scale, cy + 105*scale)
    draw.ellipse(body, fill=color, outline=(44, 85, 78), width=max(2, int(4*scale)))
    # Neck and head
    draw.rounded_rectangle(box(cx + 35*scale, cy - 95*scale, cx + 105*scale, cy + 40*scale), radius=int(25*scale), fill=color, outline=(44, 85, 78), width=max(2, int(4*scale)))
    draw.ellipse(box(cx + 55*scale, cy - 145*scale, cx + 170*scale, cy - 55*scale), fill=color, outline=(44, 85, 78), width=max(2, int(4*scale)))
    # Tail
    draw.polygon([box(cx-145*scale, cy+15*scale, cx-140*scale, cy+20*scale)[:2], (int(cx-245*scale), int(cy-15*scale)), (int(cx-145*scale), int(cy+65*scale))], fill=color)
    # Legs
    for lx in (cx-95*scale, cx+35*scale):
        draw.rounded_rectangle(box(lx, cy+70*scale, lx+34*scale, cy+145*scale), radius=int(12*scale), fill=color, outline=(44,85,78), width=max(2,int(3*scale)))
    # Eye and smile
    ex, ey = int(cx+130*scale), int(cy-110*scale)
    draw.ellipse((ex-10, ey-10, ex+10, ey+10), fill="white")
    draw.ellipse((ex-3, ey-5, ex+5, ey+5), fill=(35,48,58))
    draw.arc(box(cx+100*scale, cy-95*scale, cx+153*scale, cy-65*scale), start=5, end=150, fill=(44,65,65), width=max(2,int(3*scale)))
    # Back spikes on the stegosaurus; tiny decorative triangles on others.
    spike_xs = [cx-100*scale, cx-45*scale, cx+10*scale, cx+60*scale]
    for i, sx in enumerate(spike_xs):
        top = cy - (85 if i % 2 == 0 else 65)*scale
        draw.polygon([(int(sx), int(top)), (int(sx-23*scale), int(top+45*scale)), (int(sx+23*scale), int(top+45*scale))], fill=(255, 224, 120), outline=(44,85,78))
    # Cheek
    draw.ellipse(box(cx+105*scale, cy-82*scale, cx+130*scale, cy-62*scale), fill=(255,157,154))


def make_scene(path: Path, line: str, title: str, index: int, total: int, dino_name: str, color: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (W, H), (221, 245, 255))
    d = ImageDraw.Draw(img)
    # Sky bubbles and soft hills
    d.ellipse((-120, 470, 570, 900), fill=(177, 229, 177))
    d.ellipse((550, 450, 1450, 900), fill=(147, 216, 164))
    for x, y, r in [(105,100,25),(1080,110,32),(970,250,15),(245,230,12),(1160,330,19)]:
        d.ellipse((x-r,y-r,x+r,y+r), fill=(255,255,255), outline=(187,225,241), width=3)
    d.rounded_rectangle((45, 28, W-45, 120), radius=28, fill=(255,255,255), outline=(93,164,191), width=4)
    d.text((W//2, 74), title, font=font(39, True), fill=(42,82,111), anchor="mm")
    draw_dino(d, dino_name, color, 470, 380, 1.25)
    # Little eggs and stars
    for x, y in [(820,400),(900,440),(1010,385)]:
        d.ellipse((x-28,y-38,x+28,y+38), fill=(255,250,225), outline=(212,172,103), width=3)
        d.arc((x-12,y-18,x+12,y+18), 30, 140, fill=(212,172,103), width=3)
    # Caption card
    d.rounded_rectangle((70, 545, W-70, 675), radius=30, fill=(255,255,255), outline=(93,164,191), width=4)
    capfont = font(32, True)
    lines = wrap_words(d, line, capfont, W-180)
    line_h = 42
    start_y = 610 - (len(lines)-1)*line_h/2
    for j, txt in enumerate(lines[:2]):
        d.text((W//2, start_y+j*line_h), txt, font=capfont, fill=(42,82,111), anchor="mm")
    d.rounded_rectangle((W-150, 135, W-55, 185), radius=18, fill=(255,220,118))
    d.text((W-102,160), f"{index}/{total}", font=font(23,True), fill=(89,72,38), anchor="mm")
    img.save(path, quality=92)


def synthesize(text: str, output: Path) -> None:
    cmd = [PIPER_BIN, "--model", VOICE, "--config", VOICE_CONFIG, "--output_file", str(output)]
    subprocess.run(cmd, input=text + "\n", text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def join_audio(paths: list[Path], destination: Path) -> None:
    # Re-encode each line to identical PCM parameters before concatenating.
    normalized = []
    for i, path in enumerate(paths):
        norm = AUDIO / f"norm_{i:02d}.wav"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(path), "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(norm)], check=True)
        normalized.append(norm)
    listing = AUDIO / "audio.txt"
    listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in normalized), encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c:a", "pcm_s16le", str(destination)], check=True)
    for p in normalized:
        p.unlink(missing_ok=True)
    listing.unlink(missing_ok=True)


def create_thumbnail(title: str, dino_name: str, color: tuple[int,int,int]) -> None:
    img = Image.new("RGB", (1280, 720), (221,245,255))
    d = ImageDraw.Draw(img)
    d.ellipse((-100,420,650,980), fill=(177,229,177))
    d.ellipse((550,420,1450,900), fill=(147,216,164))
    draw_dino(d, dino_name, color, 430, 390, 1.5)
    d.rounded_rectangle((640,150,1190,550), radius=38, fill=(255,255,255), outline=(93,164,191), width=5)
    d.text((915,245), "LET'S COUNT!", font=font(48,True), fill=(42,82,111), anchor="mm")
    d.text((915,325), "10 LITTLE", font=font(47,True), fill=(239,132,103), anchor="mm")
    d.text((915,390), "DINOSAURS", font=font(48,True), fill=(42,82,111), anchor="mm")
    d.text((915,465), "Count • Learn • Smile", font=font(25,True), fill=(66,130,118), anchor="mm")
    img.save(OUT / "thumbnail.jpg", quality=92)


def main() -> None:
    require_tools()
    for folder in (OUT, WORK, AUDIO, FRAMES, CLIPS):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    title = "10 Little Dinosaurs | Counting for Kids"
    segments: list[tuple[str, str, tuple[int,int,int]]] = []
    segments.append(("Hello, little explorers! Let's count ten friendly dinosaurs together!", "Stegosaurus", DINOS[0][1]))
    for i, number in enumerate(NUMBER_WORDS):
        name, color = DINOS[i % len(DINOS)]
        line = f"{number}, little dinosaur! {name} stomps and smiles. Can you count with me?"
        segments.append((line, name, color))
    segments.append(("Great counting, everyone! Wave goodbye to our dinosaur friends. See you next time!", "Triceratops", DINOS[1][1]))

    wavs: list[Path] = []
    frame_durations: list[float] = []
    for idx, (line, name, color) in enumerate(segments, start=1):
        wav = AUDIO / f"line_{idx:02d}.wav"
        synthesize(line, wav)
        wavs.append(wav)
        frame = FRAMES / f"scene_{idx:02d}.jpg"
        make_scene(frame, line, title, idx, len(segments), name, color)
        frame_durations.append(duration(wav))
        print(f"Rendered scene {idx}/{len(segments)} ({frame_durations[-1]:.1f}s): {line}", flush=True)

    narration = OUT / "narration.wav"
    join_audio(wavs, narration)

    # Each image/audio pair becomes one clip; concatenate clips without transcoding.
    clip_paths: list[Path] = []
    for idx, secs in enumerate(frame_durations, start=1):
        frame = FRAMES / f"scene_{idx:02d}.jpg"
        wav = AUDIO / f"line_{idx:02d}.wav"
        clip = CLIPS / f"clip_{idx:02d}.mp4"
        subprocess.run([
            FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "24", "-i", str(frame),
            "-i", str(wav), "-t", f"{secs:.3f}", "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-r", "24",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(clip)
        ], check=True)
        clip_paths.append(clip)

    concat_file = WORK / "clips.txt"
    concat_file.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in clip_paths), encoding="utf-8")
    video = OUT / "video.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", "-movflags", "+faststart", str(video)], check=True)
    create_thumbnail(title, segments[1][1], segments[1][2])
    metadata = {
        "title": title,
        "description": "Count from one to ten with friendly dinosaurs! A cheerful early-learning video for little explorers.\n\nMade with original visuals and text-to-speech.",
        "tags": ["dinosaurs for kids", "counting for kids", "learn to count", "preschool learning", "toddler learning"],
        "video": "video.mp4",
        "thumbnail": "thumbnail.jpg",
        "duration_seconds": round(sum(frame_durations), 2),
    }
    (OUT / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"\nCreated: {video}")
    print(f"Created: {OUT / 'thumbnail.jpg'}")
    print(f"Approximate duration: {sum(frame_durations):.1f} seconds")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
