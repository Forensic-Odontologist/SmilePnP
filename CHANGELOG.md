# Changelog

All notable changes to SmilePnP is documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-07

### Added
- Initial public release
- PnP camera pose estimation using OpenCV
- Optional camera calibration (focal length estimation)
- Customizable Line Art outline with color picker
- Transparent material application for 3D dental models
- Quality assessment report generation (plain text)
- Automatic render dimension adjustment
- Scene initialization with optimized viewport
- Manual compositing instructions via help dialog
- Support for Blender 4.0-4.4 and 5.0+
- Portable OpenCV installation method
- Conditional button activation (minimum landmarks check)
- User-selectable camera object

### Features
- Solve camera pose from 4+ 2D-3D correspondences
- Calibrate camera intrinsics from 6+ correspondences
- SQPNP algorithm with ITERATIVE fallback
- Per-landmark reprojection error statistics
- Automatic 3D_Landmarks collection creation
- Line Art visibility preservation across calculations
- Full RGBA color picker for outline customization

### Documentation
- Complete installation guide
- User workflow tutorial
- Troubleshooting guide
- OpenCV portable installation guide
- Interface reference with quick lookup table
- Scientific methodology documentation

### Technical
- Compatible with Blender 4.0+ and 5.0+ (tested on MacOS 26.0)
- Python 3.10+ support
- OpenCV 4.10+ integration
- GPL-3.0 license

### Inspirations
- Idea: Personal work, bibliographical research and prototypes
- Addon: Derivated from CameraPnPoint by Roger Torm

## [Unreleased]

### Planned for futures versions
- Compositing automatization (doesn't work on Blender 5.0)
- Multiple victims support
- Tutorials

