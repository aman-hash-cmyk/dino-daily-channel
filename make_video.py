#!/usr/bin/env python3
"""Build Dino's free/open-source 3D-style counting episode. Voice is rhythmic speech, not AI singing."""
import json, math, os, shutil, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'output'; WORK=ROOT/'work'; AUDIO=WORK/'audio'
VOICE=Path(os.getenv('PIPER_VOICE',str(ROOT/'voices/en_US-lessac-medium.onnx'))); CONFIG=Path(os.getenv('PIPER_CONFIG',str(VOICE)+'.json'))
FPS=12; DURATION=36; SR=22050
LINES=[
"Come on, dinos, stomp your feet! Count and dance along the beat!",
"One little dino, green and bright! Bounce up high and shine with light!",
"Two triceratops go tap, tap, tap! Clap your hands and pat your lap!",
"Three T rexes wiggle with glee! Wiggle, wiggle, count with me!",
"Four stegos stomp across the floor! Stomp your feet and count once more!",
"Five little dinos, do a jive! Shake your tail and count to five!",
"Six long necks reach up to the sky! Stretch up tall and wave goodbye!",
"Seven dinos jump in a line! Jump, jump, jump, you're doing fine!",
"Eight bright wings go flap, flap, flap! Make your arms go flap, flap, flap!",
"Nine blue dinos spin around! Turn around without a sound!",
"Ten happy dinos, shout hooray! We can count another day!",
"One to ten, you did it right! Dino friends say, what a delight!",
"Wave bye-bye, our song is through! Dino friends are proud of you!"
]
def run(cmd, **kwargs): subprocess.run(cmd,check=True,**kwargs)
def make_voice():
 AUDIO.mkdir(parents=True,exist_ok=True); chunks=[]
 for i,line in enumerate(LINES):
  wav=AUDIO/f'line_{i:02d}.wav'; chunks.append(wav)
  run(['piper','--model',str(VOICE),'--config',str(CONFIG),'--output_file',str(wav),'--length_scale',str([.88,.93,1.0,.9][i%4])],input=None) if False else None
  p=subprocess.run(['piper','--model',str(VOICE),'--config',str(CONFIG),'--output_file',str(wav),'--length_scale',str([.88,.93,1.0,.9][i%4])],input=line.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if p.returncode: raise RuntimeError('Piper failed: '+p.stderr.decode(errors='ignore')[-1200:])
 # build consistent 36s track; each line gets a 2.77s slot, with spoken line clipped gently if long
 target=int(DURATION*SR); voice=np.zeros(target,dtype=np.float32)
 for i,path in enumerate(chunks):
  with wave.open(str(path),'rb') as w:
   raw=w.readframes(w.getnframes()); arr=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768
  # Piper typically mono 22050 Hz
  slot=int(target/len(chunks)); start=i*slot; arr=arr[:slot-int(.12*SR)]
  if len(arr): voice[start:start+len(arr)]=arr
 # Original synthesized accompaniment: bouncy major-key chord arpeggios; no downloaded/copyrighted track.
 t=np.arange(target,dtype=np.float64)/SR; music=np.zeros(target,dtype=np.float64)
 bpm=108; beat=60/bpm
 # C major / F / G / C cycle, plucked synth timbre
 chords=[[261.63,329.63,392.00],[349.23,440.00,523.25],[392.00,493.88,587.33],[261.63,329.63,392.00]]
 for bi,st in enumerate(np.arange(0,DURATION,beat/2)):
  idx=int(st*SR); end=min(target,idx+int(.42*SR)); tt=np.arange(end-idx)/SR
  chord=chords[(int(st/(beat*2)))%4]; note=chord[(bi)%3]*([1,2,1.5,1][bi%4])
  env=np.exp(-tt*5)*(1-np.exp(-tt*80)); tone=np.sin(2*np.pi*note*tt)+.36*np.sin(2*np.pi*note*2*tt)+.12*np.sin(2*np.pi*note*3*tt)
  music[idx:end]+=.10*env*tone
 # light kick + claps on beats
 for b in np.arange(0,DURATION,beat):
  idx=int(b*SR); n=min(int(.16*SR),target-idx); tt=np.arange(n)/SR
  music[idx:idx+n]+=.13*np.sin(2*np.pi*(85-35*tt/.16)*tt)*np.exp(-tt*24)
  idx2=int((b+beat/2)*SR); n2=min(int(.07*SR),target-idx2)
  if n2>0:
   noise=np.random.default_rng(int(b*1000)+12).normal(0,1,n2); music[idx2:idx2+n2]+=.025*noise*np.exp(-np.arange(n2)/SR*45)
 mixed=music+voice*.90
 peak=max(.01,float(np.max(np.abs(mixed)))); mixed=np.clip(mixed/peak*.88,-1,1)
 stereo=np.column_stack((mixed,mixed)).astype(np.float32)
 # write intermediate PCM then ffmpeg encode
 import soundfile as sf
 sf.write(str(WORK/'mix.wav'),stereo,SR,subtype='PCM_16')
def main():
 for c in ['piper','ffmpeg','blender']:
  if not shutil.which(c): raise RuntimeError(f'Missing required tool: {c}')
 if not VOICE.exists() or not CONFIG.exists(): raise RuntimeError(f'Piper model/config missing: {VOICE} and {CONFIG}')
 OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
 make_voice()
 silent=WORK/'dino_silent.mp4'; env=os.environ.copy(); env['DINO_SILENT_VIDEO']=str(silent)
 run(['blender','-b','-t','2','--python',str(ROOT/'blender_scene.py')],env=env)
 if not silent.exists(): raise RuntimeError('Blender did not create the animation.')
 run(['ffmpeg','-y','-i',str(silent),'-i',str(WORK/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest',str(OUT/'video.mp4')])
 # extract an attractive thumbnail from rendered video
 run(['ffmpeg','-y','-ss','3','-i',str(OUT/'video.mp4'),'-frames:v','1','-q:v','2',str(OUT/'thumbnail.jpg')])
 metadata={'title':'Dino Sing & Count! 🦖 | A Colourful Dinosaur Action Song','description':'Count from 1 to 10 with colourful dinosaur friends! Stomp, clap, wiggle and flap along. This episode uses original synthesized instrumental music and a Piper-generated spoken voice (not a singing voice). Made for kids.','tags':['dinosaurs for kids','counting song','preschool learning','kids action song','numbers 1 to 10'],'categoryId':'27','selfDeclaredMadeForKids':True}
 (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
 print('Created:',OUT/'video.mp4',OUT/'thumbnail.jpg',OUT/'metadata.json')
if __name__=='__main__': main()
