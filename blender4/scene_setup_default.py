# Blender environment setup script
# To be run at Blender startup
# Tested with Blender 4.0+ on MacOS 26.0

import bpy
import math
import mathutils

# ==============================
# 1. Scene cleanup
# ==============================

# Deselect all
bpy.ops.object.select_all(action="DESELECT")

# Select all objects
bpy.ops.object.select_all(action="SELECT")

# Delete all objects
bpy.ops.object.delete(use_global=False)

# Optional: remove empty collections except "Collection"
for coll in list(bpy.data.collections):
    if coll.name != "Collection" and len(coll.objects) == 0:
        bpy.data.collections.remove(coll)

# ==============================
# 2. Unit settings (meters)
# ==============================

scene = bpy.context.scene

scene.unit_settings.system = "METRIC"  # Metric system
scene.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 meter
scene.unit_settings.length_unit = "MILLIMETERS"  # Display in millimeters

# ==============================
# 3. Render settings
# ==============================

render = scene.render
render.engine = "BLENDER_EEVEE_NEXT"  # Blender 4+ uses EEVEE_NEXT instead of EEVEE
render.resolution_x = 2000
render.resolution_y = 2000
render.resolution_percentage = 100
render.film_transparent = True  # Transparency for Line Art

# Black background
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.color = (0.0, 0.0, 0.0)

# ==============================
# 4. Camera creation
# ==============================

# Create a new camera
cam_data = bpy.data.cameras.new(name="Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)

# Add camera to active collection
scene.collection.objects.link(cam_obj)

# Set as active scene camera
scene.camera = cam_obj

# Set camera to perspective mode
cam_data.type = "PERSP"

# Position camera at -100 mm on Y axis
cam_obj.location = (0.0, -100.0, 0.0)

# Calculate rotation to look at (0,0,0)
direction = mathutils.Vector((0.0, 0.0, 0.0)) - cam_obj.location
# Orient camera -Z axis toward target, Y as up
rotation_quat = direction.to_track_quat("-Z", "Y")
cam_obj.rotation_euler = rotation_quat.to_euler()

# Set reasonable orthographic scale (adjust according to your model)
cam_data.ortho_scale = 0.3  # larger = zoom out, smaller = zoom in

# Automatically select this camera for the add-on
scene.smilepnp_camera_object = cam_obj

# ==============================
# 5. Workspace preparation
# ==============================

# Place 3D cursor at origin (inter-incisal point, by convention)
scene.cursor.location = (0.0, 0.0, 0.0)

# ==============================
# 6. Create 3D_Landmarks collection
# ==============================

# Create a new collection "3D_Landmarks"
landmarks_collection = bpy.data.collections.get("3D_Landmarks")
if landmarks_collection is None:
    landmarks_collection = bpy.data.collections.new("3D_Landmarks")
    scene.collection.children.link(landmarks_collection)

# ==============================
# 7. Adjust 3D view zoom
# ==============================

# Zoom out by a factor of 3 in 3D view
wm = bpy.context.window_manager
for window in wm.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Multiply view distance by 3
                    space.region_3d.view_distance *= 3.0
        
        # Display marker names in Movie Clip Editor
        if area.type == "CLIP_EDITOR":
            for space in area.spaces:
                if space.type == "CLIP_EDITOR":
                    if hasattr(space, "show_marker_sliders"):
                        space.show_marker_sliders = True
                    if hasattr(space, "show_marker_name"):
                        space.show_marker_name = True

print("Smile workspace initialized ✅")
print("  → '3D_Landmarks' collection created")
print("  → 3D view zoomed out for better visibility")
print("  → Manually create the Grease Pencil object for Line Art")
