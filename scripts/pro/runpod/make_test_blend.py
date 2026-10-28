# blender --background --factory-startup --python make_test_blend.py -- OUT.blend
import bpy, sys, math
out = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "smoke.blend"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 360, 100
sc.render.image_settings.file_format = 'PNG'
sc.frame_start, sc.frame_end = 1, 2
def mat(name, rgb, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    return m
bpy.ops.mesh.primitive_plane_add(size=20); bpy.context.object.data.materials.append(mat("floor",(0.8,0.8,0.8)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(-2,0,1)); bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(mat("red",(0.8,0.1,0.1)))
bpy.ops.mesh.primitive_cube_add(size=1.6, location=(0.5,1,0.8)); cube=bpy.context.object; cube.data.materials.append(mat("gold",(1,0.7,0.2),1.0,0.2))
bpy.ops.mesh.primitive_torus_add(location=(2.5,-1,0.5)); bpy.context.object.data.materials.append(mat("blue",(0.1,0.3,0.9)))
# animate cube rotation so the 2 frames differ
cube.rotation_euler=(0,0,0); cube.keyframe_insert("rotation_euler", frame=1)
cube.rotation_euler=(0,0,math.radians(45)); cube.keyframe_insert("rotation_euler", frame=2)
bpy.ops.object.light_add(type='AREA', location=(0,-3,6)); L=bpy.context.object; L.data.energy=1500; L.data.size=4
L.rotation_euler=(math.radians(25),0,0)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.06,0.08,1)
bpy.ops.object.camera_add(location=(0,-9,4), rotation=(math.radians(68),0,0)); sc.camera = bpy.context.object
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
