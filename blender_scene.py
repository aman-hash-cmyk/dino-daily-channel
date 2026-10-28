import bpy, math, os
from mathutils import Vector
OUT=os.environ.get('DINO_SILENT_VIDEO','output/silent.mp4')
FPS=12; SECONDS=36; END=FPS*SECONDS
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'; scene.eevee.taa_render_samples=8
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=END
scene.render.image_settings.file_format='FFMPEG'; scene.render.ffmpeg.format='MPEG4'; scene.render.ffmpeg.codec='H264'; scene.render.ffmpeg.constant_rate_factor='MEDIUM'; scene.render.filepath=OUT
scene.render.image_settings.color_mode='RGB'; scene.view_settings.view_transform='Standard'
scene.world.color=(0.12,0.22,0.38)
def mat(name,c,rough=.32,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal; return m
# named cast: distinct silhouettes and signature colours
mint=mat('Moss - mint green',(.12,.72,.37)); mintlight=mat('Moss belly',(.72,.95,.48)); coral=mat('Tilly - coral orange',(1,.28,.12)); cream=mat('Tilly frill',(1,.72,.25)); violet=mat('Rexi - violet',( .48,.20,.86)); lilac=mat('Rexi belly',(.85,.62,1)); blue=mat('Pip - sky blue',(.08,.58,.96)); aqua=mat('Pip wings',( .2,.94,.91)); white=mat('Eye white',(1,1,1)); black=mat('Pupil',(.012,.018,.035)); grass=mat('Velvet grass',(.09,.48,.22)); hill1=mat('Mint hills',(.15,.76,.40)); hill2=mat('Sky hill',(.10,.56,.76)); gold=mat('Sunshine',(1,.68,.08)); pink=mat('Flower pink',(1,.12,.47));
def uv(name,loc,scale,ma,parent=None,seg=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=12, location=loc); o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma);bpy.ops.object.shade_smooth()
 if parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
def cone(name,loc,r1,r2,depth,ma,parent=None,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(ma);bpy.ops.object.shade_smooth()
 if parent:o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
def cyl(name,loc,r,depth,ma,parent=None,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(ma);o.data.materials.append(ma);bpy.ops.object.shade_smooth()
 if parent:o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
# stage
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08));bpy.context.object.name='Soft grass stage';bpy.context.object.data.materials.append(grass)
for i,(x,y,s,ma) in enumerate([(-8,5,2.5,hill1),(7,5,2.8,hill2),(-4,8,3,hill2),(4,9,3,hill1)]): uv('storybook rolling hill '+str(i),(x,y,.2),(s,s,.8),ma)
# sunshine and flower props
uv('Big friendly sun',(6,4,6),(1.0,.35,1.0),gold)
for i in range(12):
 x=-7+(i%6)*2.8; y=1.5+(i%2)*.7
 cyl('flower stem',(x,y,.25),.035,.55,hill1)
 for a in range(5):
  ang=a*2*math.pi/5;uv('flower petal',(x+.13*math.cos(ang),y+.13*math.sin(ang),.52),(.10,.07,.10),pink)
 uv('flower heart',(x,y,.54),(.07,.07,.07),gold)
# camera and lighting
bpy.ops.object.camera_add(location=(0,-19,7));cam=bpy.context.object;cam.rotation_euler=(math.radians(72),0,0);cam.data.type='ORTHO';cam.data.ortho_scale=16.5;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-4,-7,10));key=bpy.context.object;key.data.energy=1800;key.data.shape='DISK';key.data.size=9;key.rotation_euler=(math.radians(25),0,math.radians(-15))
bpy.ops.object.light_add(type='AREA',location=(7,1,7));fill=bpy.context.object;fill.data.energy=900;fill.data.color=(.45,.72,1);fill.rotation_euler=(math.radians(30),0,math.radians(130))
def animate(root,idx):
 for f in range(1,END+1,6):
  t=f/FPS; root.location.z=.08+abs(math.sin(t*3.1+idx))*0.18;root.rotation_euler[1]=math.sin(t*2.1+idx)*.045;root.rotation_euler[2]=math.sin(t*1.4+idx)*.045
  root.keyframe_insert(data_path='location',frame=f);root.keyframe_insert(data_path='rotation_euler',frame=f)
 for f in range(1,END+1,12):
  t=f/FPS
  for ob in root.children:
   if 'tail' in ob.name.lower(): ob.rotation_euler[1]=math.sin(t*4+idx)*.25;ob.keyframe_insert(data_path='rotation_euler',frame=f)
def root(name,x):
 r=bpy.data.objects.new(name,None);scene.collection.objects.link(r);r.location=(x,0,0);return r
# Moss: tall long-necked gentle sauropod
r=root('Moss the Gentle Longneck',-5.1);uv('Moss rounded body',(-5.1,0,1.25),(1.0,.58,.72),mint,r);cyl('Moss tall neck',(-4.55,0,2.05),.25,1.45,mint,r,rot=(0,0,-.18));uv('Moss kind head',(-4.4,-.02,2.83),(.52,.38,.4),mint,r);uv('Moss belly',(-5.0,-.48,1.17),(.62,.13,.4),mintlight,r);cone('Moss tail',(-6.1,0,1.25),.34,.02,1.1,mint,r,rot=(0,math.radians(90),0))
# Tilly: broad triceratops with frill and three horns
r=root('Tilly the Brave Triceratops',-1.7);uv('Tilly body',(-1.7,0,1.15),(.95,.58,.68),coral,r);uv('Tilly frill',(-1.05,0,1.95),(.62,.23,.65),cream,r);uv('Tilly face',(-.95,-.05,1.92),(.53,.39,.38),coral,r)
for x in [-1.24,-.88]: cone('Tilly brow horn',(x,-.06,2.43),.16,.01,.52,cream,r,rot=(0,math.radians(-10),0))
cone('Tilly nose horn',(-.48,-.08,2.02),.13,.01,.36,white,r,rot=(0,math.radians(80),0));cone('Tilly tail',(-2.6,0,1.18),.25,.02,.85,coral,r,rot=(0,math.radians(90),0))
# Rexi: purple T-rex, oversized head and tiny arms
r=root('Rexi the Curious T Rex',1.7);uv('Rexi body',(1.7,0,1.2),(.95,.58,.68),violet,r);uv('Rexi giant head',(2.35,-.02,2.0),(.68,.45,.52),violet,r);uv('Rexi smile jaw',(2.42,-.08,1.73),(.48,.39,.18),lilac,r)
for x in [2.18,2.45]: cyl('Rexi tiny arm',(x,-.42,1.38),.075,.38,lilac,r,rot=(0,math.radians(60),0))
cone('Rexi tail',(.65,0,1.2),.36,.02,1.15,violet,r,rot=(0,math.radians(90),0))
# Pip: blue flying pterosaur with wings and beak
r=root('Pip the Helpful Pterosaur',5.0);uv('Pip body',(5,0,1.55),(.65,.4,.45),blue,r);uv('Pip head',(5.55,-.02,2.1),(.42,.32,.34),blue,r);cone('Pip beak',(5.95,-.03,2.02),.18,.01,.42,aqua,r,rot=(0,math.radians(90),0));uv('Pip left wing',(4.55,0,1.95),(.72,.12,.20),aqua,r);uv('Pip right wing',(5.15,.25,1.95),(.72,.12,.20),aqua,r);cone('Pip tail',(4.35,0,1.5),.22,.02,.65,blue,r,rot=(0,math.radians(90),0))
# friendly eyes on each character visible toward camera
for x,z,ma in [(-4.15,2.91,mint),(-.73,2.08,coral),(2.55,2.18,violet),(5.68,2.19,blue)]:
 uv('Big eye white',(x,-.36,z),(.19,.10,.21),white);uv('Shiny eye pupil',(x+.04,-.455,z),(.08,.045,.11),black);uv('Eye sparkle',(x+.06,-.49,z+.045),(.025,.018,.03),white)
# make each character bob and wag tails; shift focal emphasis by gentle camera movement
for i,r in enumerate([o for o in bpy.data.objects if o.type=='EMPTY']): animate(r,i)
for f,x in [(1,0),(END//3,-.5),(2*END//3,.5),(END,0)]:
 cam.location.x=x;cam.keyframe_insert(data_path='location',frame=f)
# title banner text facing camera
banner=mat('Title banner',(.08,.20,.42));uv('Floating title badge',(0,-.2,5.35),(5.8,.18,.62),banner)
def text_obj(body,name,loc,size,ma):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.012;o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(math.radians(72),0,0);o.data.materials.append(ma);return o
story_title=os.environ.get('DINO_STORY_TITLE','DINO FRIENDS STORYTIME').upper()
text_obj(story_title,'Episode title',(-4.9,-.43,5.2),.40 if len(story_title)>22 else .50,white)
# glowing floating motes
for i in range(20):
 x=-7.4+(i%10)*1.65;z=3.35+(i%4)*.42;y=1.0+(i%3)*.2;o=uv('magic sparkle',(x,y,z),(.07,.07,.07),[gold,pink,aqua][i%3])
 for f in [1,END//2,END]:o.location.z=z+(.22 if f==END//2 else 0);o.keyframe_insert(data_path='location',frame=f)
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for kp in fc.keyframe_points:kp.interpolation='BEZIER'
scene.render.ffmpeg.audio_codec='AAC';scene.render.ffmpeg.audio_channels='STEREO';scene.render.ffmpeg.audio_mixrate=44100
scene.frame_set(1);os.makedirs(os.path.dirname(OUT),exist_ok=True);bpy.ops.render.render(animation=True)
