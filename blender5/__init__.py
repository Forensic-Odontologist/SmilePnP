#  SmilePnP - (c) 2026 Hadrien DIAKONOFF
# https://github.com/Forensic-Odontologist/SmilePnP
#  License: GPL v3 (see LICENSE)
#

from __future__ import annotations

bl_info = {
    "name": "SmilePnP",
    "author": "Hadrien Diakonoff",
    "license": "GPL-3.0",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "Clip Editor > Solve > SmilePnP",
    "warning": "Requires OpenCV (opencv-contrib-python)",
    "doc_url": "https://github.com/Forensic-Odontologist/SmilePnP",
    "description": "PnP solver for forensic smile-based dental identification.",
    "category": "Camera",
}

import importlib
import runpy
import subprocess
from collections import namedtuple
from datetime import datetime
from pathlib import Path
import tempfile

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, UIList

from .dependency import import_module, install_and_import_module, install_pip


def _update_clip_and_adjust_render(self, context):
    """Update callback when 2D clip is changed - automatically adjusts render dimensions"""
    scene = context.scene
    clip = scene.smilepnp_clip
    
    if clip is not None:
        # Automatically adjust render dimensions to match clip
        scene.render.resolution_x = clip.size[0]
        scene.render.resolution_y = clip.size[1]
        scene.render.resolution_percentage = 100
        print(f"[SmilePnP] Render dimensions automatically adjusted: {clip.size[0]} × {clip.size[1]} px")


def _update_track_name(self, context):
    scene = context.scene
    clip = getattr(scene, "smilepnp_clip", None)
    if clip is None:
        return
    new_name = (self.track_name or "").strip()
    if not new_name:
        return
    old_name = self.track_uid or new_name
    if new_name == old_name:
        if not self.track_uid:
            self.track_uid = new_name
        return
    # check uniqueness
    existing = clip.tracking.tracks.get(new_name)
    if existing and new_name != old_name:
        print(f"[SmilePnP] Cannot rename track to '{new_name}': name already in use.")
        self["track_name"] = old_name
        return
    track = clip.tracking.tracks.get(old_name) or clip.tracking.tracks.get(new_name)
    if track is None:
        print(f"[SmilePnP] Track '{old_name}' not found in clip.")
        self.track_uid = new_name
        return
    track.name = new_name
    self.track_uid = new_name
    self["track_name"] = new_name

    # force clip editor refresh to display the new name
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == "CLIP_EDITOR":
                area.tag_redraw()


def _run_scene_setup(operator: Operator, context: bpy.types.Context):
    scene = context.scene
    candidates = []
    user_path = (scene.smilepnp_scene_setup_path or "").strip()
    if user_path:
        path = Path(bpy.path.abspath(user_path))
        candidates.append(path)
    addon_path = Path(__file__).resolve().parent / "scene_setup_default.py"
    candidates.append(addon_path)

    for path in candidates:
        if not path.exists():
            continue
        try:
            runpy.run_path(str(path), run_name="__main__")
        except Exception as exc:  # pragma: no cover - script execution
            operator.report({"ERROR"}, f"Initialization failed: {exc}")
            return {"CANCELLED"}
        operator.report({"INFO"}, f"Script executed: {path.name}")
        return {"FINISHED"}

    operator.report({"ERROR"}, "No setup script found.")
    return {"CANCELLED"}

Dependency = namedtuple("Dependency", ["module", "package", "name"])

dependencies = (Dependency(module="cv2", package="opencv-contrib-python", name="cv"),)
dependencies_installed = False
solver_module = None


class SmileAlignMapping(PropertyGroup):
    track_name: StringProperty(name="2D Track", update=_update_track_name)
    track_uid: StringProperty(name="Track Identifier", default="")
    object: PointerProperty(
        name="3D Object",
        type=bpy.types.Object,
        description="3D object corresponding to the 2D track",
    )


class SMILEPNP_UL_mappings(UIList):
    bl_idname = "SMILEPNP_UL_mappings"

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.ID,
        item: SmileAlignMapping,
        icon: int,
        active_data: bpy.types.ID,
        active_propname: str,
        index: int,
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.prop(item, "track_name", text="", emboss=True, icon="TRACKER")
            row.prop(item, "object", text="")
            op = row.operator("smilepnp.remove_mapping", text="", icon="X", emboss=False)
            op.index = index
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text=str(index))


class SMILEPNP_OT_install_dependencies(Operator):
    bl_idname = "smilepnp.install_dependencies"
    bl_label = "Install OpenCV"
    bl_description = (
        "Downloads and installs opencv-contrib-python for the current Blender instance (requires Internet)."
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return not dependencies_installed

    def execute(self, context):
        try:
            install_pip()
            for dependency in dependencies:
                install_and_import_module(
                    module_name=dependency.module,
                    package_name=dependency.package,
                    global_name=dependency.name,
                )
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        global dependencies_installed, solver_module
        dependencies_installed = True
        solver_module = importlib.import_module(f"{__name__}.solver")
        self.report({"INFO"}, "OpenCV installed, module loaded.")
        return {"FINISHED"}


class SMILEPNP_OT_sync_landmarks(Operator):
    bl_idname = "smilepnp.sync_landmarks"
    bl_label = "Synchronize landmarks"
    bl_description = "Refreshes the correspondence table from the active clip tracks"

    def execute(self, context):
        scene = context.scene
        clip = getattr(scene, "smilepnp_clip", None)
        if clip is None:
            area = getattr(context, "area", None)
            if area and area.type == "CLIP_EDITOR":
                clip = area.spaces.active.clip

        if clip is None:
            self.report({"ERROR"}, "No active clip. Select a clip in the Movie Clip Editor.")
            return {"CANCELLED"}

        scene.smilepnp_clip = clip
        tracks = sorted(clip.tracking.tracks, key=lambda tr: tr.name)
        if not tracks:
            self.report({"ERROR"}, "No tracks found in clip.")
            return {"CANCELLED"}

        mapping_coll = scene.smilepnp_mappings
        existing_objects = {item.track_uid or item.track_name: item.object for item in mapping_coll}
        mapping_coll.clear()

        for track in tracks:
            item = mapping_coll.add()
            item.track_uid = track.name
            item.track_name = track.name
            previous_obj = existing_objects.get(track.name)
            if previous_obj:
                item.object = previous_obj
            else:
                candidate = bpy.data.objects.get(track.name)
                if candidate is not None:
                    item.object = candidate

        scene.smilepnp_mappings_index = 0
        self.report({"INFO"}, f"{len(mapping_coll)} correspondences initialized.")
        return {"FINISHED"}


class SMILEPNP_OT_remove_mapping(Operator):
    bl_idname = "smilepnp.remove_mapping"
    bl_label = "Remove correspondence"
    bl_description = "Removes this correspondence line"

    index: IntProperty()

    def execute(self, context):
        scene = context.scene
        coll = scene.smilepnp_mappings
        idx = self.index
        if 0 <= idx < len(coll):
            coll.remove(idx)
            scene.smilepnp_mappings_index = min(idx, len(coll) - 1)
            return {"FINISHED"}
        return {"CANCELLED"}


class _BaseSolverOp(Operator):
    bl_options = {"UNDO"}

    def _check_dependencies(self) -> bool:
        global dependencies_installed, solver_module
        if not dependencies_installed:
            self.report({"ERROR"}, "OpenCV is not installed. Use the installation button.")
            return False
        if solver_module is None:
            solver_module = importlib.import_module(f"{__name__}.solver")
        return True


class SMILEPNP_OT_solve_pose(_BaseSolverOp):
    bl_idname = "smilepnp.solve_pose"
    bl_label = "Solve camera pose"
    bl_description = "Solves extrinsics from 2D/3D correspondences"

    def execute(self, context):
        if context.object and context.object.mode != "OBJECT":
            self.report({"ERROR"}, "Switch to Object Mode before running the solver.")
            return {"CANCELLED"}
        if not self._check_dependencies():
            return {"CANCELLED"}
        try:
            msg = solver_module.solve_pnp(self, context)
        except RuntimeError:
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SMILEPNP_OT_calibrate(_BaseSolverOp):
    bl_idname = "smilepnp.calibrate"
    bl_label = "Calibrate camera"
    bl_description = "Solves camera intrinsic parameters"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        mappings = scene.smilepnp_mappings
        # Requires at least 6 correspondences for calibration
        valid_count = sum(1 for m in mappings if m.object is not None)
        return valid_count >= 6

    def execute(self, context):
        if context.object and context.object.mode != "OBJECT":
            self.report({"ERROR"}, "Switch to Object Mode before running calibration.")
            return {"CANCELLED"}
        if not self._check_dependencies():
            return {"CANCELLED"}
        try:
            msg = solver_module.calibrate_camera(self, context)
        except RuntimeError:
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SMILEPNP_OT_reset_calibration(Operator):
    bl_idname = "smilepnp.reset_calibration"
    bl_label = "Reset calibration"
    bl_description = "Resets calibration parameters to default values"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        clip = scene.smilepnp_clip
        
        if clip is None:
            self.report({"ERROR"}, "No clip selected.")
            return {"CANCELLED"}
        
        # Reset focal length to 2000 pixels (typical value)
        clip.tracking.camera.focal_length_pixels = 2000.0
        
        # Reset optical center to image center
        if bpy.app.version < (3, 5, 0):
            clip.tracking.camera.principal = [clip.size[0] / 2.0, clip.size[1] / 2.0]
        else:
            clip.tracking.camera.principal_point_pixels = [clip.size[0] / 2.0, clip.size[1] / 2.0]
        
        # Reset distortion coefficients
        clip.tracking.camera.k1 = 0.0
        clip.tracking.camera.k2 = 0.0
        clip.tracking.camera.k3 = 0.0
        clip.tracking.camera.brown_k1 = 0.0
        clip.tracking.camera.brown_k2 = 0.0
        clip.tracking.camera.brown_k3 = 0.0
        
        # Clear solver message
        scene.smilepnp_msg = "Calibration reset"
        
        self.report({"INFO"}, "Calibration reset successfully (focal: 2000 px)")
        return {"FINISHED"}


class SMILEPNP_OT_show_compositing_help(Operator):
    bl_idname = "smilepnp.show_compositing_help"
    bl_label = "Help: Manual compositing"
    bl_description = "Displays instructions for manually configuring compositing"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return {"FINISHED"}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Manual compositing setup", icon="INFO")
        layout.separator()
        
        box = layout.box()
        box.label(text="1. Switch to Compositing workspace", icon="NODE_COMPOSITING")
        box.label(text="   (at the top of the Blender window)")
        
        box = layout.box()
        box.label(text="2. Add the following nodes (Shift+A):", icon="NODETREE")
        box.label(text="   • Movie Clip (your photo)")
        box.label(text="   • Render Layers (Line Art of the arch)")
        box.label(text="   • Alpha Over")
        box.label(text="   • Viewer (preview)")
        box.label(text="   • Composite (final output)")
        
        box = layout.box()
        box.label(text="3. Connect the nodes:", icon="CON_TRACKTO")
        box.label(text="   • Movie Clip → Alpha Over (Background)")
        box.label(text="   • Render Layers → Alpha Over (Foreground)")
        box.label(text="   • Alpha Over → Viewer")
        box.label(text="   • Alpha Over → Composite")
        
        box = layout.box()
        box.label(text="4. In Render Properties:", icon="RENDER_STILL")
        box.label(text="   • Check 'Transparent' under Film")
        box.label(text="   • Resolution: photo size")
        
        box = layout.box()
        box.label(text="5. Dental arch:", icon="MATERIAL")
        box.label(text="   • Material: Transparent BSDF")
        
        layout.separator()
        layout.label(text="6. Launch render (F12) to see the result!", icon="RENDER_RESULT")


class SMILEPNP_OT_generate_report(_BaseSolverOp):
    bl_idname = "smilepnp.generate_report"
    bl_label = "Generate Report"
    bl_description = "Produces a Markdown report detailing scene parameters"

    filepath: StringProperty(
        name="Report file",
        description="Output path for the report",
        subtype="FILE_PATH",
    )

    def invoke(self, context, event):
        if not self._check_dependencies():
            return {"CANCELLED"}
        blend_name = Path(bpy.data.filepath).stem if bpy.data.filepath else "smilealign_report"
        default_dir = Path(bpy.path.abspath("//")) if bpy.data.filepath else Path(tempfile.gettempdir())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"Quality_Report_{timestamp}.txt"
        self.filepath = str(default_dir / default_name)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self._check_dependencies():
            return {"CANCELLED"}
        if not self.filepath:
            self.report({"ERROR"}, "No file selected.")
            return {"CANCELLED"}
        try:
            path = solver_module.generate_report(context, Path(self.filepath))
        except Exception as exc:  # pragma: no cover - protection
            self.report({"ERROR"}, f"Generation failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Report written: {path}")
        return {"FINISHED"}


class SMILEPNP_PT_panel(Panel):
    bl_label = "SmilePnP"
    bl_idname = "SMILEPNP_PT_panel"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "UI"
    bl_category = "Solve"

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.mode == "TRACKING"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if not dependencies_installed:
            box = layout.box()
            box.label(text="OpenCV dependency missing.", icon="ERROR")
            box.operator("smilepnp.install_dependencies", icon="CONSOLE")
            box.operator("wm.url_open", text="CameraPnPoint Documentation", icon="HELP").url = (
                "https://github.com/RT-studios/camera-pnpoint/"
            )
            return

        layout.operator("smilepnp.scene_setup", icon="SCENE_DATA", text="Initialize scene")
        
        layout.separator()

        layout.prop(scene, "smilepnp_clip", text="2D Clip")
        
        layout.prop(scene, "smilepnp_camera_object", text="Camera")
        
        layout.prop(scene, "smilepnp_arcade_object", text="3D Arcade")
        layout.operator("smilepnp.apply_transparent_material", icon="MATERIAL")
        
        layout.prop(scene, "smilepnp_lineart_object", text="Line Art")
        
        # Row with button and color picker side by side
        row = layout.row(align=True)
        row.operator("smilepnp.apply_colored_outline", icon="STROKE", text="Apply outline")
        row.prop(scene, "smilepnp_outline_color", text="")

        layout.label(text="2D/3D Correspondences")
        layout.operator("smilepnp.sync_landmarks", text="Refresh")

        layout.template_list(
            "SMILEPNP_UL_mappings",
            "",
            scene,
            "smilepnp_mappings",
            scene,
            "smilepnp_mappings_index",
            rows=5,
        )

        layout.separator()

        layout.prop(scene, "smilepnp_intrinsics_focal_length")
        layout.operator("smilepnp.solve_pose", icon="OUTLINER_OB_CAMERA")
        row = layout.row(align=True)
        row.operator("smilepnp.calibrate", icon="CAMERA_DATA")
        row.operator("smilepnp.reset_calibration", text="", icon="FILE_REFRESH")

        col = layout.column(align=True)
        col.label(text=scene.smilepnp_msg or "Ready.")

        layout.separator()
        layout.operator("smilepnp.show_compositing_help", icon="QUESTION")
        layout.operator("smilepnp.generate_report", icon="TEXT")


class SMILEPNP_OT_scene_setup(Operator):
    bl_idname = "smilepnp.scene_setup"
    bl_label = "Initialize Smile-Align scene"
    bl_description = "Executes the scene setup script defined below"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _run_scene_setup(self, context)


class SMILEPNP_OT_apply_colored_outline(Operator):
    bl_idname = "smilepnp.apply_colored_outline"
    bl_label = "Apply colored outline"
    bl_description = "Applies a colored material to the selected Line Art object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        # Active only if a Line Art object is selected
        return context.scene.smilepnp_lineart_object is not None

    def execute(self, context):
        scene = context.scene
        # Get the LineArt object from the scene property
        gpencil_obj = scene.smilepnp_lineart_object
        
        if gpencil_obj is None:
            self.report({"ERROR"}, "No Line Art object selected. First select the object in 'Line Art'.")
            return {"CANCELLED"}
        
        if gpencil_obj.type != 'GREASEPENCIL':
            self.report({"ERROR"}, f"Object '{gpencil_obj.name}' is not a Grease Pencil object.")
            return {"CANCELLED"}
        
        try:
            gpencil_data = gpencil_obj.data
            
            # Get the selected color (RGB + Alpha)
            outline_color = scene.smilepnp_outline_color
            
            # Configure Line Art modifier if it exists
            lineart_mod = None
            for mod in gpencil_obj.modifiers:
                if mod.type == 'GP_LINEART':
                    lineart_mod = mod
                    self.report({"INFO"}, f"Line Art modifier found: {mod.name}")
                    break
            
            if lineart_mod:
                # Line Radius: 0.25 (thickness = 25)
                try:
                    old_thickness = lineart_mod.thickness
                    lineart_mod.thickness = 25
                    self.report({"INFO"}, f"Thickness changed from {old_thickness} to {lineart_mod.thickness}")
                except Exception as e:
                    self.report({"WARNING"}, f"Cannot modify thickness: {e}")
                
                # Uncheck Lights
                try:
                    old_light = lineart_mod.use_light
                    lineart_mod.use_light = False
                    self.report({"INFO"}, f"use_light changed from {old_light} to {lineart_mod.use_light}")
                except Exception as e:
                    self.report({"WARNING"}, f"Cannot modify use_light: {e}")
            else:
                self.report({"WARNING"}, "No Line Art modifier found on object. Settings not configured.")
            
            # Create or get the "LineArt_Outline" material
            mat_outline = bpy.data.materials.get("LineArt_Outline")
            if mat_outline is None:
                mat_outline = bpy.data.materials.new(name="LineArt_Outline")
                mat_outline.use_nodes = False
            
            # Configure Grease Pencil material with selected color
            if not mat_outline.is_grease_pencil:
                bpy.data.materials.create_gpencil_data(mat_outline)
            
            # Configure stroke color from color picker (RGBA)
            mat_outline.grease_pencil.color = (
                outline_color[0],  # Red
                outline_color[1],  # Green
                outline_color[2],  # Blue
                outline_color[3]   # Alpha
            )
            mat_outline.grease_pencil.show_stroke = True
            mat_outline.grease_pencil.show_fill = False
            
            # Apply material to Line Art object
            if gpencil_data.materials:
                gpencil_data.materials[0] = mat_outline
            else:
                gpencil_data.materials.append(mat_outline)
            
            # Report with color info
            color_name = f"RGB({outline_color[0]:.2f}, {outline_color[1]:.2f}, {outline_color[2]:.2f})"
            if lineart_mod:
                self.report({"INFO"}, f"Outline applied: {color_name} (Line Radius: 0.25, Lights: unchecked).")
            else:
                self.report({"INFO"}, f"Outline applied: {color_name} (manually configure Line Art modifier).")
            return {"FINISHED"}
            
        except Exception as exc:
            self.report({"ERROR"}, f"Error applying colored outline: {exc}")
            return {"CANCELLED"}


class SMILEPNP_OT_apply_transparent_material(Operator):
    bl_idname = "smilepnp.apply_transparent_material"
    bl_label = "Apply transparent material"
    bl_description = "Applies a Transparent BSDF material to the selected 3D dental arch"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        # Active only if a 3D arcade is selected
        return context.scene.smilepnp_arcade_object is not None

    def execute(self, context):
        # Get the dental arch from the scene property
        arcade_obj = context.scene.smilepnp_arcade_object
        
        if arcade_obj is None:
            self.report({"ERROR"}, "No 3D arcade selected. First select the object in '3D Arcade'.")
            return {"CANCELLED"}
        
        if arcade_obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            self.report({"ERROR"}, f"Object '{arcade_obj.name}' is not an object that can have a material.")
            return {"CANCELLED"}
        
        try:
            # Create or get the "Transparent_Arcade" material
            mat_transparent = bpy.data.materials.get("Transparent_Arcade")
            if mat_transparent is None:
                mat_transparent = bpy.data.materials.new(name="Transparent_Arcade")
                mat_transparent.use_nodes = True
                nodes = mat_transparent.node_tree.nodes
                nodes.clear()
                
                # Create a Transparent BSDF node
                node_transparent = nodes.new(type='ShaderNodeBsdfTransparent')
                node_transparent.location = (0, 0)
                
                # Create a Material Output node
                node_output = nodes.new(type='ShaderNodeOutputMaterial')
                node_output.location = (200, 0)
                
                # Connect Transparent BSDF to Material Output
                links = mat_transparent.node_tree.links
                links.new(node_transparent.outputs['BSDF'], node_output.inputs['Surface'])
            
            # Apply material to the arcade
            if arcade_obj.data.materials:
                # Replace first material
                arcade_obj.data.materials[0] = mat_transparent
            else:
                # Add material
                arcade_obj.data.materials.append(mat_transparent)
            
            self.report({"INFO"}, f"Transparent material applied to '{arcade_obj.name}'.")
            return {"FINISHED"}
            
        except Exception as exc:
            self.report({"ERROR"}, f"Error applying transparent material: {exc}")
            return {"CANCELLED"}


class SMILEPNP_preferences(bpy.types.AddonPreferences):
    bl_label = "SmilePnP"
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        status = "OpenCV installed." if dependencies_installed else "OpenCV not detected."
        layout.label(text=status)
        layout.operator("smilepnp.install_dependencies", icon="CONSOLE")


classes = (
    SmileAlignMapping,
    SMILEPNP_UL_mappings,
    SMILEPNP_OT_install_dependencies,
    SMILEPNP_OT_scene_setup,
    SMILEPNP_OT_apply_colored_outline,
    SMILEPNP_OT_apply_transparent_material,
    SMILEPNP_OT_sync_landmarks,
    SMILEPNP_OT_remove_mapping,
    SMILEPNP_OT_solve_pose,
    SMILEPNP_OT_calibrate,
    SMILEPNP_OT_reset_calibration,
    SMILEPNP_OT_show_compositing_help,
    SMILEPNP_OT_generate_report,
    SMILEPNP_PT_panel,
    SMILEPNP_preferences,
)


def _try_import_dependencies():
    global dependencies_installed, solver_module
    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True
        solver_module = importlib.import_module(f"{__name__}.solver")
    except ModuleNotFoundError:
        dependencies_installed = False
        solver_module = None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.smilepnp_clip = PointerProperty(
        name="2D Clip",
        type=bpy.types.MovieClip,
        description="Clip used for 2D correspondences",
        update=_update_clip_and_adjust_render,
    )
    bpy.types.Scene.smilepnp_scene_setup_path = StringProperty(
        name="Setup script",
        description="Path to the Python scene setup script",
        default="",
        subtype="FILE_PATH",
    )
    bpy.types.Scene.smilepnp_camera_object = PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        description="Camera used for pose solving",
    )
    bpy.types.Scene.smilepnp_arcade_object = PointerProperty(
        name="Dental arcade",
        type=bpy.types.Object,
        description="Main arcade object used as reference",
    )
    bpy.types.Scene.smilepnp_lineart_object = PointerProperty(
        name="Line Art",
        type=bpy.types.Object,
        description="Grease Pencil Line Art object for rendering",
    )
    bpy.types.Scene.smilepnp_outline_color = FloatVectorProperty(
        name="Outline Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 0.0, 0.0, 1.0),  # Red by default (RGBA)
        description="Color for the Line Art outline",
    )
    bpy.types.Scene.smilepnp_mappings = CollectionProperty(type=SmileAlignMapping)
    bpy.types.Scene.smilepnp_mappings_index = IntProperty(default=0)
    bpy.types.Scene.smilepnp_intrinsics_focal_length = BoolProperty(
        name="Focal",
        description="Calibrate focal length",
        default=True,
    )
    bpy.types.Scene.smilepnp_intrinsics_principal_point = BoolProperty(
        name="Optical center",
        description="Calibrate optical center",
        default=False,
    )
    bpy.types.Scene.smilepnp_intrinsics_distortion_k1 = BoolProperty(
        name="K1",
        description="Calibrate radial distortion K1",
        default=False,
    )
    bpy.types.Scene.smilepnp_intrinsics_distortion_k2 = BoolProperty(
        name="K2",
        description="Calibrate radial distortion K2",
        default=False,
    )
    bpy.types.Scene.smilepnp_intrinsics_distortion_k3 = BoolProperty(
        name="K3",
        description="Calibrate radial distortion K3",
        default=False,
    )
    bpy.types.Scene.smilepnp_msg = StringProperty(
        name="Solver message",
        default="",
        description="SmilePnP solver message",
    )
    bpy.types.Scene.smilepnp_last_pairs = StringProperty(
        name="Pairs JSON",
        default="[]",
        description="Error results per pair (JSON)",
    )
    bpy.types.Scene.smilepnp_last_distance = FloatProperty(
        name="Calculated distance",
        description="Camera-smile distance calculated during last solve",
        default=0.0,
    )
    _try_import_dependencies()


def unregister():
    global dependencies_installed, solver_module

    del bpy.types.Scene.smilepnp_scene_setup_path
    del bpy.types.Scene.smilepnp_last_pairs
    del bpy.types.Scene.smilepnp_msg
    del bpy.types.Scene.smilepnp_last_distance
    del bpy.types.Scene.smilepnp_intrinsics_distortion_k3
    del bpy.types.Scene.smilepnp_intrinsics_distortion_k2
    del bpy.types.Scene.smilepnp_intrinsics_distortion_k1
    del bpy.types.Scene.smilepnp_intrinsics_principal_point
    del bpy.types.Scene.smilepnp_intrinsics_focal_length
    del bpy.types.Scene.smilepnp_mappings_index
    del bpy.types.Scene.smilepnp_mappings
    del bpy.types.Scene.smilepnp_arcade_object
    del bpy.types.Scene.smilepnp_camera_object
    del bpy.types.Scene.smilepnp_lineart_object
    del bpy.types.Scene.smilepnp_outline_color
    del bpy.types.Scene.smilepnp_clip

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    dependencies_installed = False
    solver_module = None


if __name__ == "__main__":
    register()

