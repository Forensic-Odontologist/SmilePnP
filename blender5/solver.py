"""
SmilePnP solver utilities.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Tuple

import bpy
import cv2 as cv
import numpy as np
from mathutils import Matrix, Vector


@dataclass
class MappingEntry:
    track_name: str
    object: bpy.types.Object


def _get_active_clip(context: bpy.types.Context) -> bpy.types.MovieClip | None:
    scene_clip = getattr(context.scene, "smilepnp_clip", None)
    if scene_clip:
        return scene_clip
    area = getattr(context, "area", None)
    if area and area.type == "CLIP_EDITOR":
        space = area.spaces.active
        return getattr(space, "clip", None)
    return None


def _to_world_coordinates(obj: bpy.types.Object) -> Vector:
    return obj.matrix_world.translation.copy()


def _collect_mappings(
    scene: bpy.types.Scene,
) -> Tuple[List[MappingEntry], List[str]]:
    entries: List[MappingEntry] = []
    errors: List[str] = []
    clip = scene.smilepnp_clip
    mapping_coll = scene.smilepnp_mappings

    if clip is None:
        errors.append("No Movie clip selected.")
        return entries, errors

    if not mapping_coll:
        errors.append("No 2D/3D correspondences. Run landmark synchronization.")
        return entries, errors

    tracks_by_name = {track.name: track for track in clip.tracking.tracks}
    for item in mapping_coll:
        if not item.track_name:
            continue
        track = tracks_by_name.get(item.track_name)
        if track is None:
            errors.append(f"2D track not found : {item.track_name}")
            continue
        if item.object is None:
            errors.append(f"No object assigned for {item.track_name}")
            continue
        entries.append(MappingEntry(track_name=item.track_name, object=item.object))
    if not entries:
        errors.append("All correspondences are incomplete.")
    return entries, errors


def get_scene_info(
    operator: bpy.types.Operator, context: bpy.types.Context
) -> Tuple[
    bpy.types.MovieClip,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    Tuple[int, int],
    List[str],
]:
    clip = _get_active_clip(context)
    if clip is None:
        operator.report({"ERROR"}, "Please select a clip in the Movie Clip Editor.")
        raise RuntimeError("clip_missing")

    mappings, mapping_errors = _collect_mappings(context.scene)
    if mapping_errors:
        for msg in mapping_errors:
            operator.report({"ERROR"}, msg)
        raise RuntimeError("mapping_error")

    size = clip.size
    clipcam = clip.tracking.camera
    focal = clipcam.focal_length_pixels
    
    # Validation : la focale doit être positive
    if focal <= 0:
        operator.report(
            {"WARNING"}, 
            f"Focale invalide ({focal}). Réinitialisation à une valeur par défaut (2000 px)."
        )
        focal = 2000.0
        clipcam.focal_length_pixels = focal
    
    if bpy.app.version < (3, 5, 0):
        optcent = clipcam.principal
    else:
        optcent = clipcam.principal_point_pixels

    if clipcam.distortion_model == "POLYNOMIAL":
        k1, k2, k3 = clipcam.k1, clipcam.k2, clipcam.k3
    elif clipcam.distortion_model == "BROWN":
        k1, k2, k3 = clipcam.brown_k1, clipcam.brown_k2, clipcam.brown_k3
    else:
        operator.report(
            {"WARNING"},
            "Modèle de distorsion non pris en charge. Utilisation de coefficients nuls.",
        )
        k1 = k2 = k3 = 0.0

    frame = context.scene.frame_current
    points2d = []
    point_labels = []
    for entry in mappings:
        track = clip.tracking.tracks.get(entry.track_name)
        marker = track.markers.find_frame(frame)
        if marker is None:
            operator.report({"ERROR"}, f"Track {entry.track_name} undefined on current frame.")
            raise RuntimeError("marker_missing")
        points2d.append([marker.co[0] * size[0], size[1] - marker.co[1] * size[1]])
        point_labels.append(entry.track_name)

    points3d = []
    for entry in mappings:
        obj = entry.object
        if obj.type != "EMPTY":
            operator.report({"WARNING"}, f"{obj.name} n'est pas un Empty. Utilisation de son origine.")
        points3d.append(_to_world_coordinates(obj))

    if len(points2d) != len(points3d):
        operator.report({"ERROR"}, "Le nombre de points 2D et 3D ne correspond pas.")
        raise RuntimeError("point_mismatch")

    points2d_arr = np.asarray(points2d, dtype="double")
    points3d_arr = np.asarray(points3d, dtype="double")

    camintr = np.array(
        [
            [focal, 0, optcent[0]],
            [0, focal, size[1] - optcent[1]],
            [0, 0, 1],
        ],
        dtype="double",
    )
    distcoef = np.array([k1, k2, 0.0, 0.0, k3], dtype="double")

    return clip, points3d_arr, points2d_arr, camintr, distcoef, size, point_labels


def _select_solution(
    rvecs: Sequence[np.ndarray],
    reprojection_errors: Sequence[float] | None,
) -> int:
    if len(rvecs) == 1:
        return 0

    if reprojection_errors and len(reprojection_errors) == len(rvecs):
        return int(np.argmin(reprojection_errors))

    return 0


def solve_pnp(operator: bpy.types.Operator, context: bpy.types.Context) -> str:
    scene = context.scene
    clip, points3d, points2d, camintr, distcoef, size, labels = get_scene_info(operator, context)
    if len(points2d) < 4:
        operator.report({"ERROR"}, "Minimum 4 correspondances requises pour la pose caméra.")
        raise RuntimeError("not_enough_points")

    # Essayer d'abord avec SQPNP (rapide et précis)
    try:
        retval, rvecs, tvecs, reprojection_errors = cv.solvePnPGeneric(
            points3d, points2d, camintr, distcoef, flags=cv.SOLVEPNP_SQPNP
        )
        if not retval or not rvecs:
            raise cv.error("No solution from SQPNP")
    except cv.error as e:
        # Si SQPNP échoue, essayer ITERATIVE avec des paramètres plus robustes
        try:
            # Essayer d'abord ITERATIVE standard
            retval, rvecs, tvecs, reprojection_errors = cv.solvePnPGeneric(
                points3d, points2d, camintr, distcoef, flags=cv.SOLVEPNP_ITERATIVE
            )
        except cv.error as e2:
            # En dernier recours, utiliser EPNP (plus robuste aux configurations difficiles)
            operator.report({"WARNING"}, "ITERATIVE échoué, utilisation de EPNP...")
            try:
                retval, rvecs, tvecs, reprojection_errors = cv.solvePnPGeneric(
                    points3d, points2d, camintr, distcoef, flags=cv.SOLVEPNP_EPNP
                )
            except cv.error as e3:
                operator.report(
                    {"ERROR"}, 
                    "Tous les algorithmes PnP ont échoué. Vérifiez que vos points ne sont pas coplanaires et que la calibration est correcte."
                )
                raise RuntimeError("pnp_failed")
    
    if not retval or not rvecs:
        operator.report({"ERROR"}, "solvePnP returned no solution.")
        raise RuntimeError("pnp_failed")

    idx = _select_solution(rvecs, reprojection_errors)
    rvec = rvecs[idx]
    tvec = tvecs[idx]
    repro_error = float(reprojection_errors[idx]) if reprojection_errors else 0.0

    rmat, _ = cv.Rodrigues(rvec)
    R_world2cv = Matrix(rmat.tolist())
    T_world2cv = Vector(tvec.reshape(3))

    R_bcam2cv = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
    R_cv2world = R_world2cv.transposed()
    rot = R_cv2world @ R_bcam2cv
    loc = -1 * R_cv2world @ T_world2cv

    # Utiliser la caméra sélectionnée par l'utilisateur ou la caméra active de la scène
    cam = scene.smilepnp_camera_object
    if cam is None:
        cam = scene.camera
    if cam is None or cam.type != "CAMERA":
        operator.report({"ERROR"}, "No camera selected. First select a camera in 'Camera'.")
        raise RuntimeError("no_camera_selected")
    camd = cam.data
    camd.type = "PERSP"
    camd.lens = clip.tracking.camera.focal_length
    camd.sensor_width = clip.tracking.camera.sensor_width
    camd.sensor_height = clip.tracking.camera.sensor_width * size[1] / size[0]

    render = context.scene.render
    render_size = [
        render.pixel_aspect_x * render.resolution_x,
        render.pixel_aspect_y * render.resolution_y,
    ]
    camd.sensor_fit = "HORIZONTAL" if render_size[0] / render_size[1] <= size[0] / size[1] else "VERTICAL"
    refsize = size[0] if render_size[0] / render_size[1] <= size[0] / size[1] else size[1]
    if bpy.app.version < (3, 5, 0):
        camd.shift_x = (size[0] * 0.5 - clip.tracking.camera.principal[0]) / refsize
        camd.shift_y = (size[1] * 0.5 - clip.tracking.camera.principal[1]) / refsize
    else:
        camd.shift_x = (size[0] * 0.5 - clip.tracking.camera.principal_point_pixels[0]) / refsize
        camd.shift_y = (size[1] * 0.5 - clip.tracking.camera.principal_point_pixels[1]) / refsize

    cam.matrix_world = Matrix.Translation(loc) @ rot.to_4x4()
    context.scene.camera = cam

    camd.show_background_images = True
    bg = camd.background_images[0] if camd.background_images else camd.background_images.new()
    bg.source = "MOVIE_CLIP"
    bg.clip = clip
    bg.frame_method = "FIT"
    bg.display_depth = "FRONT"
    bg.show_background_image = True
    if hasattr(bg, "clip_user"):
        bg.clip_user.use_render_undistorted = True

    # S'assurer que le LineArt reste visible après calibration
    lineart_obj = scene.smilepnp_lineart_object
    if lineart_obj and lineart_obj.type == 'GREASEPENCIL':
        lineart_obj.hide_viewport = False
        lineart_obj.hide_render = False
        # S'assurer que tous les layers sont visibles
        if hasattr(lineart_obj.data, 'layers'):
            for layer in lineart_obj.data.layers:
                layer.hide = False

    points3dproj, _ = cv.projectPoints(points3d, rvec, tvec, camintr, distcoef)
    per_point_errors = []
    mapping_lookup = {
        item.track_uid or item.track_name: item.object for item in scene.smilepnp_mappings
    }
    scale_to_mm = (scene.unit_settings.scale_length or 1.0) * 1000.0
    for label, proj, target, origin in zip(labels, points3dproj, points2d, points3d):
        err = float(np.linalg.norm(proj[0] - target))
        obj = mapping_lookup.get(label)
        obj_name = obj.name if obj else ""
        obj_loc = obj.matrix_world.translation if obj else None
        location_world = obj_loc if obj_loc is not None else Vector(origin)
        location_mm = [float(coord * scale_to_mm) for coord in location_world]
        per_point_errors.append(
            {
                "track": label,
                "error_px": err,
                "object": obj_name,
                "object_location_mm": location_mm,
                "marker_px": [float(target[0]), float(target[1])],
                "projected_px": [float(proj[0][0]), float(proj[0][1])],
            }
        )

    scene.smilepnp_last_pairs = json.dumps(per_point_errors)
    scene.smilepnp_msg = (
        f"Reprojection error : {repro_error:.3f} px (solution #{idx + 1})"
    )
    return scene.smilepnp_msg


def calibrate_camera(operator: bpy.types.Operator, context: bpy.types.Context) -> str:
    scene = context.scene
    clip, points3d, points2d, camintr, distcoef, size, _ = get_scene_info(operator, context)
    if len(points2d) < 6:
        operator.report({"ERROR"}, "Minimum 6 correspondances requises pour calibrer la caméra.")
        raise RuntimeError("not_enough_points")

    flags = (
        cv.CALIB_USE_INTRINSIC_GUESS
        + cv.CALIB_FIX_ASPECT_RATIO
        + cv.CALIB_ZERO_TANGENT_DIST
        + (0 if scene.smilepnp_intrinsics_principal_point else cv.CALIB_FIX_PRINCIPAL_POINT)
        + (0 if scene.smilepnp_intrinsics_focal_length else cv.CALIB_FIX_FOCAL_LENGTH)
        + (0 if scene.smilepnp_intrinsics_distortion_k1 else cv.CALIB_FIX_K1)
        + (0 if scene.smilepnp_intrinsics_distortion_k2 else cv.CALIB_FIX_K2)
        + (0 if scene.smilepnp_intrinsics_distortion_k3 else cv.CALIB_FIX_K3)
    )

    try:
        ret, camintr, distcoef, _, _ = cv.calibrateCamera(
            np.asarray([points3d], dtype="float32"),
            np.asarray([points2d], dtype="float32"),
            size,
            camintr,
            distcoef,
            flags=flags,
        )
    except cv.error as e:
        operator.report(
            {"ERROR"}, 
            f"Calibration failed : {str(e)}. Check that your points are well placed and not coplanar."
        )
        raise RuntimeError("calibration_failed")

    # Validation : s'assurer que la focale calibrée est positive
    new_focal = float(camintr[0][0])
    if new_focal <= 0:
        operator.report(
            {"WARNING"}, 
            f"Calibration invalide (focale négative: {new_focal}). Conservation des valeurs précédentes."
        )
        # Ne pas appliquer cette calibration invalide
        scene.smilepnp_msg = "Calibration invalide - valeurs précédentes conservées"
        return scene.smilepnp_msg

    if scene.smilepnp_intrinsics_focal_length:
        clip.tracking.camera.focal_length_pixels = new_focal
    if scene.smilepnp_intrinsics_principal_point:
        principal = [float(camintr[0][2]), float(size[1] - camintr[1][2])]
        if bpy.app.version < (3, 5, 0):
            clip.tracking.camera.principal = principal
        else:
            clip.tracking.camera.principal_point_pixels = principal
    if (
        scene.smilepnp_intrinsics_distortion_k1
        or scene.smilepnp_intrinsics_distortion_k2
        or scene.smilepnp_intrinsics_distortion_k3
    ):
        clip.tracking.camera.k1 = float(distcoef[0])
        clip.tracking.camera.k2 = float(distcoef[1])
        clip.tracking.camera.k3 = float(distcoef[4])
        clip.tracking.camera.brown_k1 = float(distcoef[0])
        clip.tracking.camera.brown_k2 = float(distcoef[1])
        clip.tracking.camera.brown_k3 = float(distcoef[4])

    # S'assurer que le LineArt reste visible après calibration
    lineart_obj = scene.smilepnp_lineart_object
    if lineart_obj and lineart_obj.type == 'GREASEPENCIL':
        lineart_obj.hide_viewport = False
        lineart_obj.hide_render = False
        # S'assurer que tous les layers sont visibles
        if hasattr(lineart_obj.data, 'layers'):
            for layer in lineart_obj.data.layers:
                layer.hide = False

    scene.smilepnp_msg = f"Reprojection error (calibration) : {ret:.3f} px"
    return scene.smilepnp_msg


def generate_report(context: bpy.types.Context, output_path: Path) -> Path:
    scene = context.scene
    clip = _get_active_clip(context)

    per_point_errors = json.loads(scene.smilepnp_last_pairs or "[]")
    mappings = [
        (item.track_name, item.object.name if item.object else "(undefined)")
        for item in scene.smilepnp_mappings
    ]

    lines = []
    lines.append("=" * 80)
    lines.append("SmilePnP Quality Report")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Blender: {bpy.app.version_string}")
    lines.append(f".blend file: {bpy.data.filepath or 'not saved'}")
    if clip:
        lines.append(f"Active clip: {clip.name} ({clip.size[0]}x{clip.size[1]} px)")
    lines.append(f"Solver message: {scene.smilepnp_msg}")
    lines.append("")

    arcade = scene.smilepnp_arcade_object
    if arcade:
        loc = arcade.matrix_world.translation
        lines.append("-" * 80)
        lines.append("Arcade Alignment")
        lines.append("-" * 80)
        lines.append(f"Origin position: ({loc.x:.4f}, {loc.y:.4f}, {loc.z:.4f}) m, norm {loc.length:.4f} m")
        scale = arcade.scale
        lines.append(f"Scale: ({scale.x:.4f}, {scale.y:.4f}, {scale.z:.4f})")
        lines.append("")

    if per_point_errors:
        lines.append("-" * 80)
        lines.append("2D/3D Correspondences")
        lines.append("-" * 80)
        lines.append(f"{'#':<4} {'Track':<15} {'3D Object':<15} {'3D Pos (mm)':<20} {'2D Meas (px)':<15} {'2D Proj (px)':<15} {'Error (px)':<10}")
        lines.append("-" * 100)
        for idx, item in enumerate(per_point_errors, 1):
            obj_name = item.get("object") or "(undefined)"
            loc = item.get("object_location_mm") or []
            loc_fmt = ", ".join(f"{coord:.1f}" for coord in loc) if loc else "-"
            marker = item.get("marker_px") or []
            marker_fmt = ", ".join(f"{coord:.1f}" for coord in marker) if marker else "-"
            projected = item.get("projected_px") or []
            proj_fmt = ", ".join(f"{coord:.1f}" for coord in projected) if projected else "-"
            lines.append(
                f"{idx:<4} {item.get('track',''):<15} {obj_name:<15} {loc_fmt:<20} {marker_fmt:<15} {proj_fmt:<15} {item['error_px']:<10.3f}"
            )
        moyenne = float(np.mean([item["error_px"] for item in per_point_errors]))
        lines.append("")
        lines.append("NOTE: Reprojection error - the lower the value, the better the alignment.")
        lines.append(f"Average error: {moyenne:.3f} px")
    else:
        lines.append("-" * 80)
        lines.append("2D/3D Correspondences")
        lines.append("-" * 80)
        lines.append(f"{'2D Track':<30} {'3D Object':<30}")
        lines.append("-" * 60)
        for track, obj_name in mappings:
            lines.append(f"{track:<30} {obj_name:<30}")
        lines.append("")
        lines.append("No error measurements available. Run a solver before generating the report.")
    lines.append("")

    # 3D landmarks summary
    scale_to_mm = (scene.unit_settings.scale_length or 1.0) * 1000.0
    lines.append("-" * 80)
    lines.append("3D Landmarks Summary")
    lines.append("-" * 80)
    lines.append(f"{'Track':<20} {'Object':<20} {'Type':<10} {'3D Position (mm)':<30}")
    lines.append("-" * 80)
    for track, obj_name in mappings:
        obj = next((item.object for item in scene.smilepnp_mappings if item.track_name == track), None)
        if obj:
            loc = obj.matrix_world.translation
            loc_mm = [float(coord * scale_to_mm) for coord in loc]
            loc_fmt = ", ".join(f"{coord:.1f}" for coord in loc_mm)
            obj_type = obj.type
        else:
            loc_fmt = "-"
            obj_type = "-"
        lines.append(f"{track:<20} {obj_name:<20} {obj_type:<10} {loc_fmt:<30}")
    lines.append("")

    camera = scene.camera
    if camera:
        loc = camera.matrix_world.translation
        rot = camera.matrix_world.to_euler("XYZ")
        cam_data = camera.data
        lines.append("-" * 80)
        lines.append("Active Camera")
        lines.append("-" * 80)
        lines.append(f"Object: {camera.name}")
        lines.append(f"Position (m): ({loc.x:.4f}, {loc.y:.4f}, {loc.z:.4f})")
        lines.append(f"Rotation (°): ({np.degrees(rot.x):.2f}, {np.degrees(rot.y):.2f}, {np.degrees(rot.z):.2f})")
        lines.append(f"Distance to origin: {loc.length:.4f} m")
        lines.append(f"Focal length: {cam_data.lens:.3f} mm")
        lines.append(f"Sensor: {cam_data.sensor_width:.2f} x {cam_data.sensor_height:.2f} mm")
        lines.append(f"Shift: X {cam_data.shift_x:.4f}, Y {cam_data.shift_y:.4f}")
        lines.append("")

    if clip:
        clip_cam = clip.tracking.camera
        lines.append("-" * 80)
        lines.append("2D Clip and Optical Parameters")
        lines.append("-" * 80)
        lines.append(f"Clip resolution: {clip.size[0]} x {clip.size[1]} px")
        lines.append(f"Clip focal length: {clip_cam.focal_length:.3f} mm")
        lines.append(f"Clip sensor: {clip_cam.sensor_width:.2f} mm")
        principal = (
            clip_cam.principal if bpy.app.version < (3, 5, 0) else clip_cam.principal_point_pixels
        )
        lines.append(f"Optical center: {principal[0]:.3f}, {principal[1]:.3f} px")
        lines.append(f"Distortion (k1/k2/k3): {clip_cam.k1:.6f}, {clip_cam.k2:.6f}, {clip_cam.k3:.6f}")
        lines.append("")

    # Line Art summary
    lineart_rows = []
    for obj in bpy.data.objects:
        if obj.type == "GPENCIL":
            for mod in obj.modifiers:
                if mod.type == "GP_LINEART":
                    row = {
                        "object": obj.name,
                        "source_type": mod.source_type,
                        "target": getattr(mod, "target_object", None).name if getattr(mod, "target_object", None) else "(none)",
                        "thickness": getattr(mod, "thickness", 0.0),
                        "use_material_override": getattr(mod, "use_material_override", False),
                        "material": getattr(mod, "material_override", None).name if getattr(mod, "material_override", None) else "(none)",
                    }
                    lineart_rows.append(row)
    if lineart_rows:
        lines.append("-" * 80)
        lines.append("Line Art Parameters")
        lines.append("-" * 80)
        lines.append(f"{'GP Object':<15} {'Source':<15} {'Target':<15} {'Thickness':<12} {'Mat Override':<15} {'Material':<15}")
        lines.append("-" * 90)
        for row in lineart_rows:
            lines.append(
                f"{row['object']:<15} {row['source_type']:<15} {row['target']:<15} {row['thickness']:<12.3f} {'Yes' if row['use_material_override'] else 'No':<15} {row['material']:<15}"
            )
        lines.append("")

    lines.append("-" * 80)
    lines.append("NOTE: 3D coordinates are expressed in millimeters. Check units if reimporting the scene.")
    lines.append("=" * 80)

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


