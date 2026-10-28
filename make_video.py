#!/usr/bin/env python3
"""Create a short original Dino Friends Storytime episode using Blender, Piper speech and synthesized music."""
import json, math, os, shutil, subprocess, wave, datetime, random
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'output'; WORK=ROOT/'work'; AUDIO=WORK/'audio'
VOICE=Path(os.getenv('PIPER_VOICE',str(ROOT/'voices/en_US-lessac-medium.onnx'))); CONFIG=Path(os.getenv('PIPER_CONFIG',str(VOICE)+'.json'))
FPS=12; DURATION=36; SR=22050
# Original mini-stories rotate by date, so scheduled runs don't repeat the same lesson every day.
STORIES=[
 {'title':'The Little Seed of Kindness','lesson':'Small acts of kindness can grow into something wonderful.','lines':[
 'Welcome to Dino Friends Storytime!','Moss found a seed beside the way.','Tilly said, let us plant it today.','Rexi brought water in a leaf cup.','Pip flew high to find sunshine up.','They took turns caring every day.','No one said, this plant is mine.','Soon a bright flower reached the sky.','Bees came buzzing, butterflies flew by.','The friends shared shade with everyone.','Kindness grew, and so did fun.','Little kind acts can bloom into something wonderful!']},
 {'title':'Rexi Learns to Say Sorry','lesson':'A sincere apology and a kind action can help repair a friendship.','lines':[
 'Welcome to Dino Friends Storytime!','Rexi ran fast through the ferny ground.','Oops! He knocked Tillys block tower down.','Tilly felt sad and turned away.','Rexi paused to think of what to say.','I am sorry. I bumped your tower.','Can I help rebuild it with you?','They stacked the blocks, one by one.','Moss and Pip joined in the fun.','Their new tall tower reached the sky.','Tilly smiled, and Rexi learned why.','When we make a mistake, we can say sorry and help make things right!']},
 {'title':'Pip and the Lost Baby Bird','lesson':'Be calm, ask for help, and care for living things.','lines':[
 'Welcome to Dino Friends Storytime!','Pip heard peeping near a tree.','A tiny bird looked worried as could be.','Moss said, stay calm, lets look around.','Tilly kept the little bird safe on the ground.','Rexi called softly, are you near?','A parent bird chirped loud and clear.','Pip showed the way up to the nest.','The baby snuggled in to rest.','The friends waved as the birds flew high.','Helping gently made their hearts fly.','When someone needs help, stay calm, be gentle, and ask a trusted helper!']},
 {'title':'The Bridge of Teamwork','lesson':'Working together helps solve problems that feel too big alone.','lines':[
 'Welcome to Dino Friends Storytime!','A little stream blocked the trail.','Rexi tried jumping, but his jump did fail.','Tilly found branches, strong and wide.','Moss laid them gently side by side.','Pip checked the bridge from the air.','Rexi held steady with extra care.','Together they made a safe way through.','Then every friend knew what to do.','They crossed the stream and cheered hooray.','Teamwork helped them save the day.','Big problems feel smaller when we share ideas and work together!']},
 {'title':'The Cave That Wasnt Scary','lesson':'When we feel afraid, we can pause, learn more, and ask a friend for support.','lines':[
 'Welcome to Dino Friends Storytime!','A strange sound echoed from a cave.','Rexi felt nervous, brave but not so brave.','Moss said, lets stop and take a breath.','Tilly stayed close; Pip peeked ahead.','They listened quietly, one, two, three.','It was a stream singing happily!','The friends laughed at the funny sound.','A hidden waterfall sparkled around.','They explored together, slow and smart.','Courage grew inside each heart.','Feeling afraid is okay. Pause, breathe, and ask a trusted friend for help!']},
 {'title':'The Great Sharing Picnic','lesson':'Sharing and including others makes playtime better for everyone.','lines':[
 'Welcome to Dino Friends Storytime!','The dinos packed a picnic to share.','Rexi brought berries, a basket to spare.','Tilly had apples, Moss brought greens.','Pip spotted someone behind the leaves.','A shy little dino sat all alone.','Come join our picnic, youre welcome here!','They made a space and passed food around.','Soon happy giggles filled the ground.','They learned there was plenty to share.','Friendship grew because they cared.','Look around today. Is there someone you can invite to play?']}
]
def run(cmd,**kwargs): subprocess.run(cmd,check=True,**kwargs)
def synth_voice(lines):
 AUDIO.mkdir(parents=True,exist_ok=True); chunks=[]
 for i,line in enumerate(lines):
  wav=AUDIO/f'line_{i:02d}.wav'; chunks.append(wav)
  p=subprocess.run(['piper','--model',str(VOICE),'--config',str(CONFIG),'--output_file',str(wav),'--length_scale',str([.91,.96,.92,1.0][i%4])],input=line.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if p.returncode: raise RuntimeError('Piper failed: '+p.stderr.decode(errors='ignore')[-1000:])
 # fit each line in its own slot, preserve pauses between story beats
 target=int(DURATION*SR); voice=np.zeros(target,dtype=np.float32); slot=target//len(chunks)
 for i,path in enumerate(chunks):
  with wave.open(str(path),'rb') as w: arr=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
  start=i*slot; maxlen=slot-int(.20*SR)
  # Keep line boundaries and avoid abrupt cuts; lines are deliberately short.
  arr=arr[:maxlen]
  n=len(arr)
  if n:
   fade=min(int(.025*SR),n//3); env=np.ones(n,dtype=np.float32)
   if fade: env[:fade]=np.linspace(0,1,fade);env[-fade:]=np.linspace(1,0,fade)
   voice[start:start+n]=arr*env
 # original synthesized cheerful accompaniment: plucked melody + soft bass and beat
 t=np.arange(target,dtype=np.float64)/SR; music=np.zeros(target,dtype=np.float64); bpm=104; beat=60/bpm
 # C / F / G / Am loop, arpeggiated pluck melody
 chords=[[261.63,329.63,392.0],[349.23,440.0,523.25],[392.0,493.88,587.33],[220.0,261.63,329.63]]
 scale=[523.25,587.33,659.25,783.99,659.25,587.33,523.25,392.0]
 step=beat/2
 for k,st in enumerate(np.arange(0,DURATION,step)):
  idx=int(st*SR); n=min(int(.34*SR),target-idx); tt=np.arange(n)/SR; chord=chords[(int(st/(beat*2)))%len(chords)]
  note=scale[k%len(scale)] if k%4 else chord[k%3]*2
  env=np.exp(-tt*5.5)*(1-np.exp(-tt*70)); tone=np.sin(2*np.pi*note*tt)+.24*np.sin(2*np.pi*note*2*tt)+.08*np.sin(2*np.pi*note*3*tt)
  music[idx:idx+n]+=.10*env*tone
  # soft chord bed
  for cn in chord[:2]: music[idx:idx+n]+=.018*env*np.sin(2*np.pi*cn*tt)
 for b in np.arange(0,DURATION,beat):
  idx=int(b*SR); n=min(int(.13*SR),target-idx); tt=np.arange(n)/SR
  music[idx:idx+n]+=.075*np.sin(2*np.pi*(90-38*tt/.13)*tt)*np.exp(-tt*23)
  idx2=int((b+beat/2)*SR); n2=min(int(.045*SR),target-idx2)
  if n2>0:
   rng=np.random.default_rng(int(b*1000)+44); music[idx2:idx2+n2]+=.012*rng.normal(0,1,n2)*np.exp(-np.arange(n2)/SR*65)
 mixed=music+voice*.94; peak=max(.01,float(np.max(np.abs(mixed)))); mixed=np.clip(mixed/peak*.9,-1,1)
 import soundfile as sf; sf.write(str(WORK/'mix.wav'),np.column_stack((mixed,mixed)).astype(np.float32),SR,subtype='PCM_16')
def main():
 for c in ['piper','ffmpeg','blender']:
  if not shutil.which(c): raise RuntimeError(f'Missing required tool: {c}')
 if not VOICE.exists() or not CONFIG.exists(): raise RuntimeError(f'Piper model/config missing: {VOICE} and {CONFIG}')
 # Date-based rotation produces different original story and moral each scheduled day.
 day=datetime.datetime.now(datetime.timezone.utc).timetuple().tm_yday
 story=STORIES[day%len(STORIES)]
 OUT.mkdir(exist_ok=True);WORK.mkdir(exist_ok=True);synth_voice(story['lines'])
 silent=WORK/'dino_silent.mp4';env=os.environ.copy();env['DINO_SILENT_VIDEO']=str(silent);env['DINO_STORY_TITLE']=story['title']
 run(['blender','-b','-t','2','--python',str(ROOT/'blender_scene.py')],env=env)
 if not silent.exists() or silent.stat().st_size==0: raise RuntimeError('Blender did not create the animation.')
 run(['ffmpeg','-y','-i',str(silent),'-i',str(WORK/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest',str(OUT/'video.mp4')])
 run(['ffmpeg','-y','-ss','3','-i',str(OUT/'video.mp4'),'-frames:v','1','-q:v','2',str(OUT/'thumbnail.jpg')])
 meta={'title':f"Dino Friends Storytime 🦕 | {story['title']}",'description':f"An original Dino Friends mini-story for children: {story['title']}. Lesson: {story['lesson']}\n\nFeaturing Moss the Gentle Longneck, Tilly the Brave Triceratops, Rexi the Curious T-Rex, and Pip the Helpful Pterosaur. Includes original synthesized background music and computer-generated spoken narration (not sung vocals). Made for kids.",'tags':['dinosaur stories for kids','kids moral stories','preschool stories','friendship for kids','Dino Friends Storytime'],'categoryId':'27','selfDeclaredMadeForKids':True}
 (OUT/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 print('Story:',story['title']);print('Lesson:',story['lesson']);print('Created video, thumbnail and metadata in output/.')
if __name__=='__main__': main()
