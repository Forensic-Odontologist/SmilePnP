# SmilePnP Installation Guide

This installation guide provides detailed instructions for installing the SmilePnP add-on and its required dependencies (OpenCV) for both Blender 4.x and Blender 5.x.

---

## Prerequisites

Before installing SmilePnP, ensure you have:

1. **Blender 4.0 or later** OR **Blender 5.0 or later** installed (higher is better)
   - Download from the [official Blender website](https://www.blender.org/)
   - Note: Blender 5 is not compatible with Intel-based Macs (Apple Silicon only)
2. **Administrator/sudo privileges** (may be required for OpenCV installation)
3. **Active internet connection** (required for OpenCV installation)

---

## Part 1: Installing Blender

### Windows

1. Download the Blender installer from [blender.org](https://www.blender.org/download/)
2. Run the installer executable
3. Follow the installation wizard
4. Choose between:
   - **Standard installation**: Installs Blender in Program Files
   - **Portable installation**: Can be run from any location (no installation required)

### macOS

1. Download the Blender disk image (`.dmg`) from [blender.org](https://www.blender.org/download/)
2. Open the downloaded `.dmg` file
3. Drag Blender to the Applications folder
4. Launch Blender from Applications
5. **Note for Blender 5**: Only compatible with Apple Silicon Macs (M1, M2, M3, etc.)

### Linux

1. Download the Blender archive from [blender.org](https://www.blender.org/download/)
2. Extract the archive to your desired location
3. Run Blender from the extracted directory
4. Alternatively, install via your distribution's package manager:
   ```bash
   # Ubuntu/Debian
   sudo apt install blender
   
   # Fedora
   sudo dnf install blender
   
   # Arch Linux
   sudo pacman -S blender
   ```

---

## Part 2: Installing the SmilePnP Add-on

### Step 1: Download the Add-on

1. Download the appropriate SmilePnP version:
   - **For Blender 4.x**: Download `SmilePnP_v0.1_Blender4.zip`
   - **For Blender 5.x**: Download `SmilePnP_v0.1_Blender5.zip`
2. **Important**: Do not extract the ZIP file - Blender handles decompression automatically

### Step 2: Install via Blender Preferences

1. **Launch Blender**

2. **Open Preferences**:
   - Go to `Edit > Preferences` (or press `Ctrl + ,` on Windows/Linux, `Cmd + ,` on macOS)

3. **Navigate to Add-ons**:
   - Click on **"Add-ons"** in the left sidebar

4. **Install the add-on**:
   - Click the **"Install..."** button in the upper-right corner of the Add-ons panel
   - A file browser dialog opens
   - Navigate to the location of the downloaded ZIP file
   - Select the ZIP file (e.g., `SmilePnP_v0.1_Blender4.zip`)
   - Click **"Install Add-on"** or **"Open"**

5. **Enable the add-on**:
   - After installation, the add-on appears in the Add-ons list
   - Use the search field to quickly find "SmilePnP"
   - Check the checkbox next to "SmilePnP" to enable it
   - The add-on is now active
---

## Part 3: Installing OpenCV

SmilePnP requires the OpenCV library (`opencv-contrib-python`) to perform its calculations. This section covers both automatic and manual installation methods.

### Method 1: Automatic Installation (Recommended)

#### For Blender 4.x and 5.x

1. **Open the SmilePnP panel** (see Part 2, Step 3)

2. **Check for OpenCV**:
   - If OpenCV is not installed, you'll see:
     - A message: "OpenCV dependency missing."
     - An **"Install OpenCV"** button

3. **Install OpenCV**:
   - Click the **"Install OpenCV"** button
   - Wait for the installation to complete (typically 1-3 minutes)
   - You'll see progress messages in Blender's console/terminal
   - **Important**: Do not close Blender during installation

4. **Restart Blender**:
   - After installation completes, **restart Blender completely**
   - Close all Blender windows
   - Launch Blender again

5. **Verify installation**:
   - Open the SmilePnP panel again
   - The "Install OpenCV" button should be gone
   - The panel should show normal functionality
   - You can now use all SmilePnP features

<img width="1512" height="982" alt="SmilePnP Open CV" src="https://github.com/user-attachments/assets/a44313b9-7632-4b72-88bc-bae53cf65ac3" />


**Troubleshooting automatic installation**:
- If installation fails, try Method 2 (manual installation)
- Check your internet connection
- Ensure you have write permissions to Blender's Python directory
- On some systems, administrator/sudo privileges may be required

### Method 2: Manual Installation

If automatic installation fails, you can install OpenCV manually using Blender's Python.

#### Step 1: Locate Blender's Python Executable

**Windows**:
```
C:\Program Files\Blender Foundation\Blender [version]\[version]\python\bin\python.exe
```
Example for Blender 4.5:
```
C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe
```

**macOS**:
1. Right-click on Blender.app
2. Select "Show Package Contents"
3. Navigate to: `Contents/Resources/[version]/python/bin/python3.[version]`
4. Example for Blender 4.5: `Contents/Resources/4.5/python/bin/python3.10`

**Linux**:
```
/usr/bin/blender
```
Or if installed from archive:
```
[blender_directory]/[version]/python/bin/python3.[version]
```

#### Step 2: Install OpenCV via Command Line

1. **Open a terminal/command prompt**:
   - **Windows**: Press `Win + R`, type `cmd`, press Enter
   - **macOS**: Open Terminal from Applications > Utilities
   - **Linux**: Open your terminal application

2. **Navigate to Blender's Python directory** (optional, if Python is not in PATH)

3. **Install OpenCV**:
   - Use the full path to Blender's Python executable
   - Run the pip install command

**Windows**:
```cmd
"C:\Program Files\Blender Foundation\Blender 4.5\4.5\python\bin\python.exe" -m pip install opencv-contrib-python
```

**macOS**:
```bash
/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.10 -m pip install opencv-contrib-python
```

**Linux**:
```bash
/usr/bin/blender --python-expr "import subprocess; subprocess.check_call(['python3', '-m', 'pip', 'install', 'opencv-contrib-python'])"
```

Or if you have direct access to Python:
```bash
[path_to_blender_python] -m pip install opencv-contrib-python
```

4. **Wait for installation**:
   - Installation typically takes 1-3 minutes
   - You'll see progress messages in the terminal

5. **Restart Blender**:
   - Close all Blender windows
   - Launch Blender again

6. **Verify installation**:
   - Open the SmilePnP panel
   - The "Install OpenCV" button should be gone
   - All features should be available

---

## Part 4: Verification and Testing

After completing installation, verify that everything works:

### Quick Test

1. **Open Blender** and switch to Clip Editor workspace
2. **Set to Tracking mode** in the Clip Editor
3. **Open SmilePnP panel** (press `N`, click "Solve" tab)
4. **Check for errors**:
   - No "OpenCV dependency missing" message
   - All buttons are visible and enabled
   - "Initialize scene" button is available

### Full Test

1. **Click "Initialize scene"**:
   - Should complete without errors
   - Camera should be created
   - Scene units should be set to millimeters

2. **Load a test image**:
   - In Clip Editor, load any image
   - Should work without errors

3. **If all steps complete successfully**: Installation is complete!

---

# Other

## Choosing the Right Version

- **Use Blender 4.x if**:
  - You have an Intel-based Mac
  - You need maximum compatibility
  - You're working in a mixed environment

- **Use Blender 5.x if**:
  - You have an Apple Silicon Mac (M1/M2/M3)
  - You want the latest features
  - You're starting a new project

**Note**: Both versions of SmilePnP provide the same core functionality. Choose based on your Blender version and system compatibility.

## Uninstallation

### Removing the Add-on

1. Go to `Edit > Preferences > Add-ons`
2. Search for "SmilePnP"
3. Uncheck the box to disable, or
4. Click the **"Remove"** button to uninstall completely

### Removing OpenCV

**Note**: OpenCV is shared with other add-ons. Only remove it if you're sure no other add-ons need it.

1. Locate Blender's Python (see Part 3, Method 2, Step 1)
2. Run:
   ```bash
   [path_to_python] -m pip uninstall opencv-contrib-python
   ```
3. Restart Blender

**Last updated**: February 2026  

