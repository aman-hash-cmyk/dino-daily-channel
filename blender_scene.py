import bpy, math, os
from mathutils import Vector
OUT=os.environ.get('DINO_SILENT_VIDEO','/workspace/work/dino_silent.mp4')
FPS=12; DURATION=36; END=FPS*DURATION
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
scene=bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples=8
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=END
scene.render.image_settings.file_format='FFMPEG'; scene.render.ffmpeg.format='MPEG4'; scene.render.ffmpeg.codec='H264'; scene.render.ffmpeg.constant_rate_factor='MEDIUM'; scene.render.filepath=OUT
scene.world.color=(0.18,0.28,0.5)
# lighting
bpy.ops.object.light_add(type='AREA', location=(0,-8,11)); key=bpy.context.object; key.data.energy=1600; key.data.shape='DISK'; key.data.size=9; key.rotation_euler=(math.radians(25),0,0)
bpy.ops.object.light_add(type='AREA', location=(7,3,7)); fill=bpy.context.object; fill.data.energy=900; fill.data.color=(0.45,0.7,1); fill.rotation_euler=(math.radians(25),0,math.radians(130))
def mat(name,color,metal=0,rough=.35):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough; return m
colors=[(0.08,.72,.32),(.98,.38,.12),(.13,.42,.95),(.68,.18,.82),(1,.68,.08)]
accents=[(.95,.83,.2),(1,.75,.35),(.3,.9,1),(1,.35,.63),(.45,.95,.3)]
mats=[mat('Dino jewel '+str(i),c) for i,c in enumerate(colors)]; accents_m=[mat('Dino accent '+str(i),c) for i,c in enumerate(accents)]
white=mat('Eye white',(1,1,1)); black=mat('Pupil',(.015,.025,.04)); groundmat=mat('Candy grass',(.12,.62,.29)); sky=mat('Sky',(0.12,.55,.9)); gold=mat('Golden number',(1,.65,.02),.15,.22)
def uv(name,loc,scale,ma,parent=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.shade_smooth(); o.data.materials.append(ma)
 if parent:o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
def cone(name,loc,r1,r2,depth,ma,parent=None,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot); o=bpy.context.object;o.name=name;o.data.materials.append(ma); bpy.ops.object.shade_smooth()
 if parent:o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
def cylinder(name,loc,r,depth,ma,parent=None,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=depth, location=loc, rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(ma);bpy.ops.object.shade_smooth()
 if parent:o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
# floor and rolling hills
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.1)); bpy.context.object.data.materials.append(groundmat)
for i,(x,y,s) in enumerate([(-8,4,2),(7,5,2.5),(-5,8,3),(4,9,3)]): uv('soft hill',(x,y,.4),(s,s,.9),mat('hill'+str(i),[(.1,.8,.55),(.2,.65,.8),(.65,.85,.25),(.6,.4,.8)][i]))
# camera
bpy.ops.object.camera_add(location=(0,-17,7.5)); cam=bpy.context.object; cam.rotation_euler=(math.radians(72),0,0); cam.data.type='ORTHO'; cam.data.ortho_scale=17; scene.camera=cam
# root dinosaur models across screen, deliberately different silhouettes
def make_dino(idx,x):
 root=bpy.data.objects.new('DinoRoot'+str(idx),None);scene.collection.objects.link(root); root.location=(x,0,0)
 ma=mats[idx%5]; ac=accents_m[idx%5]
 # base body, neck/head shape varies by species
 uv('round body',(x,0,1.45),(1.05,.55,.72),ma,root)
 if idx==0: # long neck sauropod
  cylinder('long neck',(x+.45,0,2.25),.24,1.45,ma,root,rot=(0,0,-.28)); uv('long head',(x+.65,-.02,3.02),(.52,.37,.42),ma,root)
  cone('tail',(x-1.3,0,1.58),.38,.04,1.3,ma,root,rot=(0,math.radians(90),0))
 elif idx==1: # triceratops frill and horns
  uv('frill',(x+.58,0,2.15),(.62,.22,.68),ac,root); uv('head',(x+.72,-.03,2.13),(.55,.38,.4),ma,root)
  for dx in [.48,.82]: cone('horn',(x+dx,-.04,2.57),.18,.015,.62,white,root,rot=(0,math.radians(-12),0))
  cone('nose horn',(x+1.12,-.02,2.22),.13,0,.35,white,root,rot=(0,math.radians(80),0))
  cone('tail',(x-1.22,0,1.52),.3,.03,1.05,ma,root,rot=(0,math.radians(90),0))
 elif idx==2: # T rex big head and tiny arms
  uv('big head',(x+.73,-.02,2.22),(.64,.43,.5),ma,root); uv('jaw',(x+.8,-.05,1.96),(.48,.4,.19),ac,root)
  for dx in [.4,.65]: cylinder('tiny arm',(x+dx,-.42,1.55),.09,.45,ac,root,rot=(0,math.radians(55),0))
  cone('tail',(x-1.25,0,1.5),.4,.02,1.25,ma,root,rot=(0,math.radians(90),0))
 elif idx==3: # stego plates
  cone('tail',(x-1.25,0,1.5),.36,.02,1.2,ma,root,rot=(0,math.radians(90),0))
  for j in range(5): cone('back plate',(x-.65+j*.34,0,2.13),.24,0,.48,ac,root)
 else: # pterosaur-like dino with wings
  uv('head',(x+.7,-.02,2.35),(.48,.35,.38),ma,root); cone('beak',(x+1.1,-.02,2.3),.17,0,.48,ac,root,rot=(0,math.radians(90),0))
  for side in [-1,1]:
   wing=uv('wing',(x-.05,side*.5,2.05),(.75,.13,.18),ac,root); wing.rotation_euler[1]=side*.45
  cone('tail',(x-1.25,0,1.52),.3,.02,1.1,ma,root,rot=(0,math.radians(90),0))
 # four sturdy legs
 for lx in [-.58,.45]:
  for ly in [-.32,.32]: cylinder('stumpy leg',(x+lx,ly, .62),.19,.78,ma,root)
 # eyes on visible side
 uv('eye white',(x+.94,-.34,2.48),(.22,.12,.24),white,root); uv('eye pupil',(x+1.0,-.445,2.48),(.095,.05,.12),black,root)
 # nostrils and cheek
 uv('nostril',(x+1.18,-.32,2.23),(.045,.035,.04),black,root)
 uv('cheek',(x+.68,-.39,2.03),(.16,.05,.1),ac,root)
 # bounce and sway animation
 for f in range(1,END+1,12):
  t=f/FPS; root.location.z=.10+abs(math.sin(t*3+idx))*0.20; root.rotation_euler[1]=math.sin(t*2+idx)*.06; root.keyframe_insert(data_path='location',frame=f);root.keyframe_insert(data_path='rotation_euler',frame=f)
 return root
# five characters centered; x coordinates scaled to fit camera
roots=[make_dino(i,x) for i,x in enumerate([-5.7,-2.9,0,2.9,5.7])]
# colorful floating bubbles/stars
for i in range(18):
 x=-7.5+(i%9)*1.85; z=3.7+(i%3)*.55; y=1.5+(i%2)*.5
 o=uv('floating sparkle',(x,y,z),(.11,.11,.11),accents_m[i%5]);
 for f in [1,END//2,END]: o.location.z=z+(.25 if f==END//2 else 0);o.keyframe_insert(data_path='location',frame=f)
# numbers in front/right, visibility switched every 3.6 seconds
font=bpy.data.fonts.get('Bfont')
for n in range(1,11):
 cu=bpy.data.curves.new('NumberText'+str(n),'FONT');cu.body=str(n);cu.extrude=.06;cu.bevel_depth=.02;cu.bevel_resolution=2; ob=bpy.data.objects.new('Count '+str(n),cu);scene.collection.objects.link(ob);ob.location=(5.1,-1.2,3.15);ob.rotation_euler=(math.radians(75),0,0);ob.scale=(1.6,1.6,1.6);ob.data.materials.append(gold)
 for f in range(1,END+1):
  show=((f-1)//(END//10))==n-1
  ob.hide_render=not show
  if f in [1,END//10*n, min(END,END//10*n+1)]: ob.keyframe_insert(data_path='hide_render',frame=f)
# headline text
cu=bpy.data.curves.new('Headline','FONT');cu.body='DINO SING & COUNT!';cu.size=.65;cu.extrude=.015; title=bpy.data.objects.new('Headline',cu);scene.collection.objects.link(title);title.location=(-6.8,-1.1,5.5);title.rotation_euler=(math.radians(75),0,0);title.data.materials.append(white)
# make keyframes smooth
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for kp in fc.keyframe_points: kp.interpolation='BEZIER'
scene.render.image_settings.color_mode='RGB';scene.render.ffmpeg.audio_codec='AAC';scene.render.ffmpeg.audio_channels='STEREO';scene.render.ffmpeg.audio_mixrate=44100
scene.view_settings.view_transform='AgX'
scene.frame_set(1)
os.makedirs(os.path.dirname(OUT),exist_ok=True)
bpy.ops.render.render(animation=True)
