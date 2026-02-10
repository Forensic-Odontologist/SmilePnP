# SmilePnP v0.1.0 - Blender 5.x

This version is compatible with **Blender 5.0, 5.1+** and has been tested with Blender 4.0+ on MacOS 26.0

## Installation

1. Download `SmilePnP_v0.1_Blender5.zip` from releases (dont unzip the ZIP files)
2. In Blender: `Edit > Preferences > Add-ons` → `Install...`
3. Select the downloaded ZIP file
4. Enable "SmilePnP" checkbox
5. Click **"Install OpenCV"** button
6. Restart Blender

The SmilePnP addon is now installed into the Movie Clip Editor tab.

## Features

- PnP camera pose estimation
- Optional camera calibration (focal length)
- Customizable Line Art outline with color picker (RGBA)
- Transparent material for 3D dental models
- Quality assessment report generation
- Automatic render dimensions adjustment
- Scene initialization with optimized viewport

## Blender 5.0 Specific Changes

- Updated Grease Pencil API (`GREASEPENCIL` instead of `GPENCIL`)
- No `show_marker_sliders` attribute (handled gracefully)

## Documentation

Full documentation available at: [https://github.com/Forensic-Odontologist/SmilePnP/tree/main/docs](https://github.com/Forensic-Odontologist/SmilePnP/tree/main/docs)

## OpenCV Installation Issues?

OpenCV installation can fails if you use corporate firewall or if you don't have admin rights.

## License

GPL-3.0 - See [LICENSE](../LICENSE)

