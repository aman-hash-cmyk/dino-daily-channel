#!/usr/bin/env python3
"""Create an original, colorful, gently animated dinosaur counting video.

Requires ffmpeg, Piper TTS, a Piper .onnx voice model + matching .json config,
Pillow and NumPy. Writes output/video.mp4, output/thumbnail.jpg and
output/metadata.json for upload_youtube.py.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = ROOT / "work"
AUDIO = WORK / "audio"
FRAMES = WORK / "frames"
VOICE = os.getenv("PIPER_VOICE", str(ROOT / "voices" / "en_US-lessac-medium.onnx"))
VOICE_CONFIG = os.getenv("PIPER_CONFIG", VOICE + ".json")
PIPER_BIN = os.getenv("PIPER_BIN", "piper")
FFMPEG = os.getenv("FFMPEG", "ffmpeg")
W, H = 1280, 720
FPS = 12
SAMPLE_RATE = 22050
PAUSE_SECONDS = 0.58

# Friendly original vector characters; no downloaded artwork is required.
DINOS = [
    {"name": "Stegosaurus", "color": (70, 190, 125), "accent": (255, 218, 95)},
    {"name": "Triceratops", "color": (255, 177, 72), "accent": (255, 230, 130)},
    {"name": "Pterodactyl", "color": (158, 119, 224), "accent": (255, 198, 221)},
    {"name": "Brontosaurus", "color": (53, 183, 192), "accent": (255, 224, 112)},
    {"name": "Tyrannosaurus Rex", "color": (244, 119, 105), "accent": (255, 216, 125)},
]

# Spoken lines deliberately use rhyme, repetition, simple language and turn-taking.
# Each line is short enough for a child to echo or act out.
SEGMENTS = [
    {"text": "Hello, little explorers! Are your counting voices ready? Let's go!", "dino": 0, "action": "hello", "prompt": "READY, LITTLE EXPLORERS?", "speed": 0.94},
    {"text": "One tiny dino, having fun! Wiggle, wiggle, everyone!", "dino": 0, "count": 1, "action": "wiggle", "prompt": "SAY ONE!", "speed": 0.88},
    {"text": "Two dino feet go tap, tap, tap. Can you clap along in your lap?", "dino": 1, "count": 2, "action": "clap", "prompt": "CLAP, CLAP, CLAP!", "speed": 0.96},
    {"text": "Three dino friends dance by a tree. Point to three! Can you count with me?", "dino": 2, "count": 3, "action": "dance", "prompt": "POINT TO THREE!", "speed": 0.92},
    {"text": "Four little roars, soft as can be. Make a tiny roar with me! Roar!", "dino": 3, "count": 4, "action": "roar", "prompt": "TINY ROAR!", "speed": 1.02},
    {"text": "Five happy dinos, doing a jive. Wiggle your shoulders! Give me five!", "dino": 4, "count": 5, "action": "dance", "prompt": "GIVE ME FIVE!", "speed": 0.90},
    {"text": "Six little tails swish in a mix. Swish to the left, then swish for six!", "dino": 0, "count": 6, "action": "tail", "prompt": "SWISH, SWISH!", "speed": 0.96},
    {"text": "Seven bright dinos bounce up to heaven. Bounce one time! That's number seven!", "dino": 1, "count": 7, "action": "bounce", "prompt": "ONE BOUNCE!", "speed": 0.92},
    {"text": "Eight little wings flap in the sunlight. Stretch your arms and flap just right!", "dino": 2, "count": 8, "action": "flap", "prompt": "FLAP YOUR WINGS!", "speed": 0.96},
    {"text": "Nine leafy snacks, looking so fine. Pretend to nibble—you're doing fine!", "dino": 3, "count": 9, "action": "nibble", "prompt": "NIBBLE, NIBBLE!", "speed": 0.92},
    {"text": "Ten little dinos, ten smiles to show. Count them again? Ready, set, go!", "dino": 4, "count": 10, "action": "celebrate", "prompt": "TEN! HOORAY!", "speed": 0.88},
    {"text": "You counted to ten, what a wonderful crew! Clap for yourself—I'm proud of you!", "dino": 0, "action": "clap", "prompt": "GIVE YOURSELF A CLAP!", "speed": 0.96},
    {"text": "Wave bye-bye, friends, with a wiggle and cheer. More dino fun is coming soon, dear!", "dino": 1, "action": "goodbye", "prompt": "WAVE GOODBYE!", "speed": 0.94},
]

PALETTES = [
    ((220, 246, 255), (168, 229, 180), (125, 210, 166)),
    ((255, 235, 205), (255, 207, 142), (255, 180, 135)),
    ((237, 228, 255), (194, 183, 247), (159, 207, 231)),
    ((215, 250, 235), (142, 222, 189), (103, 196, 170)),
    ((255, 225, 236), (255, 183, 194), (250, 159, 176)),
]


def require_tools() -> None:
    for command in (PIPER_BIN, FFMPEG):
        if not shutil.which(command):
            raise RuntimeError(f"Required command '{command}' was not found on PATH.")
    if not Path(VOICE).is_file():
        raise RuntimeError(f"Piper voice model is missing: {VOICE}")
    if not Path(VOICE_CONFIG).is_file():
        raise RuntimeError(f"Piper voice configuration is missing: {VOICE_CONFIG}")


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, use_font, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=use_font)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_dino(draw: ImageDraw.ImageDraw, cx: float, cy: float, color, accent, scale: float, t: float, action: str) -> None:
    """Draw a friendly dinosaur whose body, tail, legs and wings move over time."""
    outline = (49, 91, 94)
    bounce = math.sin(t * 5.2) * 11
    cy += bounce
    s = scale
    # Body, neck, head and tail
    draw.ellipse((cx-165*s, cy-25*s, cx+92*s, cy+105*s), fill=color, outline=outline, width=max(2, int(4*s)))
    draw.rounded_rectangle((cx+30*s, cy-105*s, cx+98*s, cy+45*s), radius=int(24*s), fill=color, outline=outline, width=max(2, int(4*s)))
    draw.ellipse((cx+54*s, cy-155*s, cx+174*s, cy-60*s), fill=color, outline=outline, width=max(2, int(4*s)))
    tail_swing = math.sin(t*6.0) * 22
    draw.polygon([(cx-140*s,cy+8*s),(cx-250*s,cy-28*s+tail_swing),(cx-155*s,cy+70*s)], fill=color, outline=outline)
    # Legs kick gently in opposite directions.
    leg_swing = math.sin(t*5.2) * 13
    for j, lx in enumerate((cx-92*s, cx+32*s)):
        offset = leg_swing if j == 0 else -leg_swing
        draw.rounded_rectangle((lx,cy+72*s+offset,cx*0+lx+34*s,cy+150*s+offset), radius=int(12*s), fill=color, outline=outline, width=max(2,int(3*s)))
    # Back spikes / plates
    for i, sx in enumerate((cx-105*s,cx-52*s,cx+1*s,cx+53*s)):
        top = cy-(87 if i%2==0 else 65)*s
        draw.polygon([(sx,top),(sx-22*s,top+42*s),(sx+22*s,top+42*s)], fill=accent, outline=outline)
    # Wings flap on the flying dinosaur; other characters wave their little arms.
    arm = math.sin(t*7.0) * 20
    if action == "flap":
        draw.polygon([(cx-15*s,cy+10*s),(cx-110*s,cy-75*s-arm),(cx-82*s,cy+45*s)], fill=accent, outline=outline)
    else:
        draw.line((cx-5*s,cy+15*s,cx-62*s,cy+42*s+arm), fill=outline, width=max(4,int(12*s)))
        draw.ellipse((cx-72*s,cy+32*s+arm,cx-50*s,cy+54*s+arm), fill=color, outline=outline, width=max(2,int(3*s)))
    # Eye blink and cheek; smile is slightly open during a pretend roar.
    ex, ey = cx+139*s, cy-119*s
    blink = (int(t*2.1) % 7 == 0 and (t*2.1)%1 < 0.12)
    if blink:
        draw.line((ex-9*s,ey,ex+9*s,ey), fill=outline, width=max(2,int(4*s)))
    else:
        draw.ellipse((ex-10*s,ey-11*s,ex+10*s,ey+11*s), fill="white")
        draw.ellipse((ex-3*s,ey-5*s,ex+5*s,ey+5*s), fill=(36,48,60))
    draw.ellipse((cx+107*s,cy-88*s,cx+133*s,cy-66*s), fill=(255,143,159))
    if action == "roar" and math.sin(t*10) > 0.15:
        draw.ellipse((cx+112*s,cy-82*s,cx+145*s,cy-57*s), fill=(107,52,70), outline=outline, width=2)
    else:
        draw.arc((cx+105*s,cy-98*s,cx+153*s,cy-68*s), start=5, end=150, fill=outline, width=max(2,int(3*s)))


def draw_scene(path: Path, segment: dict, idx: int, total: int, t: float) -> None:
    dino = DINOS[segment["dino"]]
    sky, hill1, hill2 = PALETTES[segment["dino"]]
    img = Image.new("RGB", (W, H), sky)
    d = ImageDraw.Draw(img)
    # Rolling hills and slowly drifting bubbles/stars.
    d.ellipse((-140, 455, 650, 900), fill=hill1)
    d.ellipse((500, 430, 1450, 900), fill=hill2)
    for j, (x0, y0, r) in enumerate(((100,160,24),(1080,145,32),(980,275,15),(240,245,13),(1165,350,19),(720,180,12))):
        x = (x0 + math.sin(t*0.45+j)*17) % W
        y = y0 + math.cos(t*0.7+j)*9
        d.ellipse((x-r,y-r,x+r,y+r), fill=(255,255,255), outline=(185,222,238), width=3)
        if j % 2 == 0:
            star = [(x,y-r-12),(x+5,y-4),(x+r+12,y),(x+5,y+4),(x,y+r+12),(x-5,y+4),(x-r-12,y),(x-5,y-4)]
            d.polygon(star, fill=(255,220,105))
    # Header and scene count
    d.rounded_rectangle((38, 24, W-38, 112), radius=27, fill=(255,255,255), outline=(86,160,186), width=4)
    d.text((W//2, 68), "DINO COUNTING CLUB!", font=font(37, True), fill=(42,82,111), anchor="mm")
    d.rounded_rectangle((W-145, 127, W-42, 177), radius=18, fill=(255,222,119), outline=(219,174,68), width=2)
    d.text((W-94,152), f"{idx}/{total}", font=font(22,True), fill=(89,72,38), anchor="mm")
    # Number badge and matching dots encourage visual counting.
    if segment.get("count"):
        n = segment["count"]
        d.ellipse((850, 205, 1075, 430), fill=(255,255,255), outline=(255,177,72), width=7)
        d.text((962, 314), str(n), font=font(116,True), fill=dino["color"], anchor="mm", stroke_width=1, stroke_fill=(255,255,255))
        for k in range(min(n, 10)):
            x = 830 + (k % 5)*70
            y = 462 + (k // 5)*43
            d.ellipse((x-15,y-15,x+15,y+15), fill=DINOS[k%len(DINOS)]["color"], outline=(255,255,255), width=3)
    # Dino moves around the lower-left half without hiding the count badge.
    cx = 440 + math.sin(t*1.3)*27
    cy = 365 + (18 if segment.get("action")=="bounce" else 0)
    draw_dino(d, cx, cy, dino["color"], dino["accent"], 1.15, t, segment.get("action", "wiggle"))
    # Action prompt is a child-friendly call-and-response cue.
    prompt = segment.get("prompt", "YOUR TURN!")
    d.rounded_rectangle((690, 500, 1190, 568), radius=24, fill=(255,255,255), outline=(255,153,174), width=4)
    d.text((940, 534), prompt, font=font(25, True), fill=(91,72,126), anchor="mm")
    # Captions are large and high contrast; cap to 2 lines.
    d.rounded_rectangle((48, 588, W-48, 690), radius=24, fill=(255,255,255), outline=(86,160,186), width=4)
    cap_font = font(27, True)
    lines = wrap_text(d, segment["text"], cap_font, W-130)
    lines = lines[:2]
    y0 = 638 - (len(lines)-1)*17
    for j, line in enumerate(lines):
        d.text((W//2, y0+j*35), line, font=cap_font, fill=(42,82,111), anchor="mm")
    img.save(path, quality=91)


def synthesize(text: str, output: Path, speed: float) -> None:
    # Piper is a natural-sounding TTS engine, not a human singing/acting voice.
    # Sentence punctuation and small pacing changes create a more expressive rhythm.
    cmd = [PIPER_BIN, "--model", VOICE, "--config", VOICE_CONFIG, "--length_scale", str(speed), "--output_file", str(output)]
    subprocess.run(cmd, input=text + "\n", text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def normalize_wav(src: Path, dst: Path) -> None:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le", str(dst)], check=True)


def create_narration(normalized_paths: list[Path], destination: Path) -> list[float]:
    """Join voice clips with a real pause after each line; return segment durations."""
    durations = []
    pause_frames = int(SAMPLE_RATE * PAUSE_SECONDS)
    silence = b"\x00\x00" * pause_frames
    with wave.open(str(destination), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        for i, path in enumerate(normalized_paths):
            with wave.open(str(path), "rb") as src:
                raw = src.readframes(src.getnframes())
                durations.append(len(raw) / 2 / SAMPLE_RATE)
            out.writeframes(raw)
            out.writeframes(silence if i < len(normalized_paths)-1 else b"\x00\x00" * int(SAMPLE_RATE*0.35))
    return durations


def make_music(destination: Path, seconds: float) -> None:
    """Synthesize a gentle, original, royalty-free-style instrumental bed locally."""
    total = max(1, int(seconds * SAMPLE_RATE))
    audio = np.zeros(total, dtype=np.float64)
    # Bright, simple original melody in C major; short notes with soft attack/release.
    melody = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46, 783.99, 698.46,
              523.25, 587.33, 659.25, 523.25, 392.00, 493.88, 587.33, 493.88]
    note_len = 0.30
    for i, start in enumerate(np.arange(0.0, seconds, note_len)):
        a = int(start*SAMPLE_RATE)
        b = min(total, int((start+note_len*0.92)*SAMPLE_RATE))
        if b <= a:
            continue
        local_t = np.arange(b-a, dtype=np.float64)/SAMPLE_RATE
        env = np.minimum(1.0, local_t/0.035) * np.minimum(1.0, (local_t[-1]-local_t)/0.045 if len(local_t)>1 else 1.0)
        f = melody[i % len(melody)]
        audio[a:b] += 0.095 * env * (np.sin(2*np.pi*f*local_t) + 0.28*np.sin(2*np.pi*(f*2)*local_t))
        # Soft bass pulse on every other beat.
        if i % 2 == 0:
            audio[a:b] += 0.045 * env * np.sin(2*np.pi*130.81*local_t)
    # Very soft percussive ticks on the beat, no recognizable existing melody.
    beat_len = 0.60
    for start in np.arange(0.0, seconds, beat_len):
        a = int(start*SAMPLE_RATE)
        b = min(total, a+int(0.07*SAMPLE_RATE))
        if b > a:
            t = np.arange(b-a)/SAMPLE_RATE
            audio[a:b] += 0.018*np.exp(-t*45)*np.sin(2*np.pi*1100*t)
    audio = np.clip(audio, -0.35, 0.35)
    pcm = (audio*32767).astype(np.int16)
    with wave.open(str(destination), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm.tobytes())


def create_thumbnail() -> None:
    img = Image.new("RGB", (1280, 720), (220, 246, 255))
    d = ImageDraw.Draw(img)
    d.ellipse((-100, 420, 650, 980), fill=(168, 229, 180))
    d.ellipse((550, 420, 1450, 900), fill=(125, 210, 166))
    draw_dino(d, 420, 380, DINOS[0]["color"], DINOS[0]["accent"], 1.5, 1.2, "celebrate")
    d.rounded_rectangle((635, 135, 1200, 555), radius=40, fill=(255,255,255), outline=(86,160,186), width=6)
    d.text((918, 225), "LET'S COUNT!", font=font(47,True), fill=(42,82,111), anchor="mm")
    d.text((918, 315), "10 LITTLE", font=font(53,True), fill=(244,119,105), anchor="mm")
    d.text((918, 390), "DINOSAURS", font=font(51,True), fill=(42,82,111), anchor="mm")
    d.text((918, 475), "WIGGLE • COUNT • PLAY", font=font(25,True), fill=(66,130,118), anchor="mm")
    img.save(OUT / "thumbnail.jpg", quality=93)


def main() -> None:
    require_tools()
    for folder in (OUT, WORK, AUDIO, FRAMES):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    normalized: list[Path] = []
    for idx, segment in enumerate(SEGMENTS, start=1):
        raw = AUDIO / f"voice_{idx:02d}.wav"
        norm = AUDIO / f"voice_{idx:02d}_normalized.wav"
        print(f"Speaking line {idx}/{len(SEGMENTS)}: {segment['text']}", flush=True)
        synthesize(segment["text"], raw, segment.get("speed", 0.96))
        normalize_wav(raw, norm)
        normalized.append(norm)

    line_durations = create_narration(normalized, OUT / "narration.wav")
    scene_durations = [dur + (PAUSE_SECONDS if i < len(SEGMENTS)-1 else 0.35) for i, dur in enumerate(line_durations)]
    total_duration = sum(scene_durations)
    make_music(AUDIO / "background_music.wav", total_duration)

    frame_no = 0
    elapsed = 0.0
    total_frames = int(math.ceil(total_duration * FPS))
    for idx, (segment, scene_duration) in enumerate(zip(SEGMENTS, scene_durations), start=1):
        frames_this_scene = int(round(scene_duration * FPS))
        for local_frame in range(frames_this_scene):
            frame_path = FRAMES / f"frame_{frame_no:05d}.jpg"
            draw_scene(frame_path, segment, idx, len(SEGMENTS), elapsed + local_frame/FPS)
            frame_no += 1
        elapsed += scene_duration
        print(f"Animated scene {idx}/{len(SEGMENTS)}", flush=True)

    # Ensure the image sequence duration and narration are close; video is trimmed to audio duration.
    video = OUT / "video.mp4"
    music = AUDIO / "background_music.wav"
    narration = OUT / "narration.wav"
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-framerate", str(FPS), "-i", str(FRAMES / "frame_%05d.jpg"),
        "-i", str(narration), "-i", str(music),
        "-filter_complex", "[1:a]volume=1.0[voice];[2:a]volume=0.13[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=1[aout]",
        "-map", "0:v:0", "-map", "[aout]", "-t", f"{total_duration:.3f}",
        "-vf", "fps=24,scale=1280:720,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-r", "24",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(video)
    ], check=True)

    create_thumbnail()
    metadata = {
        "title": "10 Little Dinosaurs 🦕 | Count, Wiggle & Play!",
        "description": (
            "Count from one to ten with friendly dinosaurs! 🦕🌈\n"
            "Wiggle, clap, flap, and say the numbers out loud in this colorful early-learning adventure.\n\n"
            "A cheerful original instrumental, animated dinosaur characters, counting prompts, rhymes, and gentle pauses help little learners join in.\n\n"
            "Made for preschool and toddler learning. Adult supervision is recommended for young children."
        ),
        "tags": ["dinosaurs for kids", "counting for kids", "learn to count", "preschool learning", "toddler learning", "numbers 1 to 10", "kids songs", "dinosaur animation"],
        "video": "video.mp4",
        "thumbnail": "thumbnail.jpg",
        "duration_seconds": round(total_duration, 2),
        "features": ["original synthesized background music", "animated vector characters", "child participation prompts", "rhyming counting script", "pauses between spoken lines"],
    }
    (OUT / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nCreated: {video}")
    print(f"Created: {OUT / 'thumbnail.jpg'}")
    print(f"Duration: {total_duration:.1f}s | Animated frames: {frame_no}")
    print("Note: Piper TTS can vary pacing, but it is not human singing or full character acting.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
