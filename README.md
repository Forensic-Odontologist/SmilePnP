# SmilePnP

**Blender Add-on for Forensic Smile-Based Dental Identification**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Blender](https://img.shields.io/badge/Blender-4.0%20%7C%205.0+-orange.svg)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
![Version](https://img.shields.io/badge/version-0.1.0-blue)

## Overview

🤳☠️🦷 SmilePnP is a Blender add-on implementing a **Perspective-n-Point (PnP)** approach for quantitative 2D-3D dental superimposition in forensic identification contexts. The method aligns post-mortem 3D intraoral scans (or digitalized casts) with ante-mortem smile photographs through geometric optimization, providing objective quality metrics and reproducible workflows.

### Key Features

- ✅ **Geometric alignment** using PnP solver (OpenCV)
- ✅ **Camera pose estimation** from 2D-3D correspondences  
- ✅ **No camera calibration** required (works with social media photos, selfies)
- ✅ **Quantitative metrics** (reprojection error per landmark)
- ✅ **Customizable Line Art** with color picker
- ✅ **Quality assessment reports** with detailed statistics (.txt file)
- ✅ **Open-source** and free (GPL-3.0)

---

## Download & Installation

### Version Selection

The following versions of SmilePnP have been tested on macOS 26.0.
If you encounter any bugs, please contact me!

| Blender Version | Download | Documentation |
|----------------|----------|---------------|
| **4.0 - 4.4** | [SmilePnP_v0.1_Blender4.zip](https://github.com/Forensic-Odontologist/SmilePnP/releases/v0.1.0/SmilePnP_v0.1_Blender4.zip) | [Installation Guide](docs/installation.md) |
| **5.0+** | [SmilePnP_v0.1_Blender5.zip](https://github.com/Forensic-Odontologist/SmilePnP/releases/v0.1.0/SmilePnP_v0.1_Blender5.zip) | [Installation Guide](docs/installation.md) |

### Quick Install

1. Download the appropriate ZIP file for your Blender version
2. In Blender: `Edit > Preferences > Add-ons` → `Install...`
3. Select the downloaded ZIP file
4. Enable "SmilePnP" checkbox
5. Click **"Install OpenCV"** in the add-on panel (first use only)
6. Restart Blender

The SmilePnP addon is now installed into the Movie Clip Editor tab.

**Detailed instructions:** [Installation Guide](docs/INSTALLATION.md)

---

## Quick Start

1. **Initialize scene**: Click "Initialize scene" button
2. **Load data**: Import ante-mortem photo in Movie Clip Editor
3. **Select objects**: Choose Camera, 3D Arcade, Line Art
4. **Customize color**: (Optional) Use color picker to select outline color
5. **Apply materials**: Click "Apply transparent material" and "Apply outline"
6. **Place landmarks**: Ctrl+Click on photo and 3D model (≥4 points)
7. **Synchronize**: Click "Refresh" to link 2D-3D correspondences
8. **Solve**: Click "Solve camera pose"
9. **Render**: F12 to visualize the superimposition

**Full workflow:** [User Guide](docs/USER-GUIDE.md)

---

## Features

### Customizable Line Art

- **Color picker** with full RGBA support
- **Default red color** for standard forensic use
- **Custom colors** for better contrast or institutional standards
- **Transparency control** via alpha channel

### Quantitative Quality Assessment

- **Per-landmark reprojection errors** in pixels
- **Mean and standard deviation** statistics
- **Detailed quality report** in plain text format
- **Camera parameters** estimation (pose, focal length, optical center)

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Complete installation instructions
- [User Guide](docs/USER-GUIDE.md) - Step-by-step workflow
- [Interface Reference](docs/INTERFACE.md) - UI elements description

---

## Scientific Background

SmilePnP addresses limitations of traditional smile-based identification methods by introducing explicit geometric modeling and quantitative validation.

### Method Overview

1. **Manual landmark placement**: User defines anatomical correspondences between 2D photograph and 3D model
2. **PnP optimization**: Camera pose solved via OpenCV's solvePnPGeneric (SQPNP algorithm with ITERATIVE fallback)
3. **Optional calibration**: Intrinsic parameters (focal length) can be estimated from ≥6 correspondences
4. **Quality metrics**: Reprojection error computed for each landmark to assess alignment quality

### Use Cases

- **Forensic dental identification**: Post-mortem victim identification via smile comparison (dental records unavailable, Cold cases)
- **Disaster victim identification (DVI)**: When conventional dental records unavailable

### Advantages

- **Quantitative validation** (vs. subjective visual comparison)
- **Reproducible workflow** (standardized environment)
- **No calibration required** (works with smartphone photos, social media images)
- **Transparent documentation** (quality report with all parameters)
- **Open-source** (auditable code, free for research and operational use)

---

## Citation

If you use SmilePnP in your research, please cite:

```bibtex
@software{smilepnp2026,
  author = {Diakonoff, Hadrien},
  title = {SmilePnP: Blender Add-on for Forensic Smile-Based Dental Identification},
  year = {2026},
  url = {https://github.com/Forensic-Odontologist/SmilePnP},
  version = {0.1.0},
  license = {GPL-3.0}
}
```

---

## Technical Requirements

**Software:**
- Blender: 4.0+ or 5.0+ (choose corresponding version of the add-on)
- Python: 3.10+ (included with Blender)
- OpenCV: opencv-contrib-python 4.10+ (auto-installed by add-on)

**Data:**
- 3D dental model: STL, OBJ, or PLY format (from intraoral scanner or digitalized casts)
- Ante-mortem photo: JPG, PNG (uncalibrated, from any source)

---

## License

This project is derivated from CameraPnPoint (https://github.com/RT-studios/camera-pnpoint) by Roger Torm and licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

---

## Issues & Support

Bug reports, questions : please contact me on Linkedin

---

## Acknowledgments

- **Blender Foundation** for the open-source 3D software
- **OpenCV community** for computer vision algorithms
- **Roger Torm** for the original CameraPnPoint add-on

---

## Screenshots

### Interface

*(To be added: Screenshot of SmilePnP panel in Blender)*

### Workflow Example

*(To be added: Before/after superimposition comparison)*

### Quality Report

*(To be added: Example of generated report)*

---

## Links

- **Documentation**: [docs/](docs/)
- **Releases**: [GitHub Releases](https://github.com/Forensic-Odontologist/SmilePnP/releases)
- **Issues**: [GitHub Issues](https://github.com/Forensic-Odontologist/SmilePnP/issues)
- **License**: [GPL-3.0](LICENSE)

---

🦷☠️ **Made for the forensic science community** 

*SmilePnP aims to bring geometric rigor, transparency, and reproducibility to smile-based forensic dental identification, supporting practitioners worldwide in their critical mission of human identification.*

