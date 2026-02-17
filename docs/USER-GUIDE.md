# SmilePnP V. 0.1.0 – User Guide

⚠️🚧 **Work in progress** : This content is currently being updated with videos.

## Introduction

**SmilePnP** is a Blender add-on designed for forensic dental identification. It allows you to align a 3D dental arch model with a 2D photograph of a smile by calculating the precise camera position and orientation that would have captured the photo.

The add-on uses computer vision techniques to match 2D points from a photograph with 3D points from a model, calculate the camera pose, and generate a Line Art outline that can be overlaid on the photograph for forensic comparison.

---

## Step-by-Step Guide

### Step 1: Install the add-on and OpenCV

#### 1.1: Install Blender (video 1 below)

If you haven't already, download and install Blender from the [official Blender website](https://www.blender.org/). The add-on requires Blender 4.0 or later. 

#### 1.2: Install the SmilePnP add-on (video 1 & 2)

1. Download the SmilePnP add-on (`.zip` file) - do not extract it
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` in the upper-right corner
4. Navigate to the downloaded `.zip` file and select it
5. After installation, search for "SmilePnP" in the add-ons list
6. Check the box next to "SmilePnP" to enable it

### 1.3: Installing OpenCV (required dependency) (video 2)

The add-on requires OpenCV (a computer vision library). When you first open the SmilePnP panel, you'll see an **"Install OpenCV"** button if it's not already installed.

1. Click **"Install OpenCV"** in the panel
2. Wait for the installation to complete (this may take a few minutes)
3. Blender will need to be restarted after installation
4. Once restarted, the add-on should work normally

#### Video 1 : installing Blender on MacOS

https://github.com/user-attachments/assets/8763059a-469e-498e-9b89-1ad45be599a1

#### Video 2 : opening Blender, 3D viewport interface and installing SmilePnP and OpenCV on MacOS

https://github.com/user-attachments/assets/ee71d8c2-03e0-4dc4-919a-b439b87940ce


---

### Step 2: Initialize the scene

1. Open Blender (or start a new file: `File > New > General`)
2. Switch to the **Clip Editor** workspace
3. Make sure you're in **Tracking** mode (dropdown in Clip Editor header)
4. Press `N` to open the right-side properties panel if not already visible
5. In the **"SmilePnP"** section (under "Solve" tab), click **"Initialize scene"**

The initialization automatically:
- Sets units to millimeters (better for working on dental arch)
- Zooms out the 3D viewport (factor 3) for better visibility
- Creates a default camera positioned at -100 mm on Y-axis
- Configures render settings (EEVEE Next, 2000×2000px, transparency enabled)
- Sets 3D cursor to origin (0,0,0)
- Creates a "3D_Landmarks" collection to organize landmarks

#### Video 3: Initialize the scene

https://github.com/user-attachments/assets/c7fd2422-7137-4c10-a59e-d0706a1f5125

---

### Step 3: Load the ante-mortem photograph and place 2D landmarks

#### 3.1: Load the AM photograph

1. In the **Clip Editor**, click **"Open"** (or `Image > Open Image`)
2. Navigate to your smile photograph and select it
3. The image appears in the Clip Editor

#### Video 4: Load the AM photograph (2D data)

https://github.com/user-attachments/assets/b5eacd05-1c90-4ba2-883f-583f8420b22c

#### 3.2: Place 2D tracking markers

1. Make sure you're in **Tracking** mode (dropdown in Clip Editor header)
2. Press `Ctrl + Left Click` on a characteristic point in the smile (e.g., tip of a canine, edge of an incisor)
3. A tracking marker appears (small crosshair)
4. **Recommended**: left-click the marker and rename it (e.g., "Left_Canine_Tip")
5. Repeat for at least 4 points (6+ recommended for calibration)
6. Spread points across the smile for better accuracy

**Tips**:
- Avoid ambiguous points or areas with motion blur
- Use descriptive names to make matching easier later

#### Video 5: Placement of 2D Landmarks

https://github.com/user-attachments/assets/9dc7ef3e-c243-44c6-beac-a77a2df7aa7d

#### 3.3: Link the photograph to the add-on

1. In the SmilePnP panel, find the **"2D Clip"** field
2. Select your loaded image from the dropdown (should appear automatically)

---

### Step 4: Import the 3D dental arch model (post-mortem)

1. Switch to the **3D Viewport**
2. Go to `File > Import` and select your file format (STL, OBJ, etc.)
3. Navigate to your 3D dental arch file and import it
4. The model appears in the 3D viewport

**Optional - Clean the model**:
- If the model contains unwanted geometry (gums, other structures), you can:
  - Enter Edit Mode (`Tab`)
  - Select unwanted parts
  - Delete them (`X` > Delete)
  - Exit Edit Mode (`Tab`)

#### Video 6: 3D dental model importation

https://github.com/user-attachments/assets/14cc2e5e-2d09-4400-943f-ec88d93d8628

#### Positioning the Inter-Incisal Point at the World Origin

- Identify the inter-incisal point on the mesh.
- In Object Mode, translate the model so that the inter-incisal point is positioned at the Blender scene origin (0, 0, 0).
- This operation does not alter the geometry of the model and establishes a consistent reference coordinate system for the entire workflow.

#### Video 7: Positioning the Inter-Incisal Point at the World Origin

https://github.com/user-attachments/assets/139ec673-dc41-4003-90d5-5484aabb3483

#### Orientation of the Model Along the X, Y, and Z Axes (if required)

- Adjust the orientation of the 3D model using the X, Y, and Z rotation fields.
- The desired spatial configuration is:
   - The occlusal plane parallel to the XY plane.
   - The inter-incisal point aligned with the Y axis.

- Use the View Axis controls in the upper-right corner of the 3D Viewport to verify alignment:
   - X / –X: lateral views
   - Y / –Y: frontal views (–Y corresponds to the default frontal view)
   - Z / –Z: superior and inferior views

#### Video 10: 3D orientation of the model.

https://github.com/user-attachments/assets/f3479114-4c67-4da7-82dd-9fd0bffce4a8

#### Check the Inter-Canine Distance

- Select the –Z axis view to obtain an inferior view of the dental arch.
- Activate the Measure Tool from the left toolbar of the 3D Viewport.
- Click on the cusp tip of the first canine, then click on the cusp tip of the contralateral canine.
- Record the virtual inter-canine distance measured in Blender.

#### Video 9: Inter-Canine Distance check

https://github.com/user-attachments/assets/9bd3d887-7016-471a-91ea-18f0c5807e3f

#### Scale Adjustment (If Required)

- Compare the virtual inter-canine distance with the real inter-canine distance measured post-mortem.
- If a discrepancy exists, compute the scaling factor: scaling factor = real distance / virtual distance
- In Object Mode, apply this factor using the Scale transformation.
- Validate the scaling permanently via: Object > Apply > Scale

This ensures that the 3D model is dimensionally consistent with anatomical measurements.

#### Applying the Orientation Transformation (position, rotation, scale...)

- Once the correct orientation is achieved, apply the transformation:
- Object > Apply > All Transforms

---

### Step 5: Create and configure Line Art

#### 5.1: Create a Grease Pencil object

1. In the **3D Viewport**, press `Shift + A` (or click `Add` menu)
2. Navigate to `Grease Pencil > Object Line Art`
3. A Grease Pencil object is created (you may not see it visually yet - this is normal)

#### 5.2: Configuring Line Art Parameters

- In the Object Data Properties of the Line Art object:
- Select the dental arch model as the source.

Configure edge detection:
- Enable Contour (and optionally Crease).
- Set the line thickness to a low value (e.g. 0.25) to obtain a clean and thin outline.

#### 5.3: Link Line Art to the add-on

1. In the SmilePnP panel, find the **"Line Art"** field
2. Select your Grease Pencil object from the dropdown
3. Click **"Apply outline"** (or "Apply red outline")
4. Select the Line Art object.
5. In the Data tab, uncheck Lights.

This applies a red material to the outline (by default), visible on render.

**Note**: You can change the outline color using the color picker next to the button.

#### Video 10: Line art configuration

https://github.com/user-attachments/assets/7455fdd7-707e-4941-88e6-8480ab7e0968

---

### Step 6: Configure remaining objects

#### 6.1: Select the camera

1. In the SmilePnP panel, find the **"Camera"** field
2. Select **"Camera"** from the dropdown (the camera created during initialization)

**Important**: Always use the same camera throughout your work session. This camera will be automatically updated when you solve the pose.

#### 6.2: Select the 3D arch

1. In the SmilePnP panel, find the **"3D Arcade"** field
2. Select your imported arch from the dropdown

#### 6.3: Apply transparent material to the arch

1. Click the **"Apply transparent material"** button
2. This makes the arch transparent in renders, so only the Line Art outline will be visible

---

### Step 7: Place 3D landmarks

1. In the **3D Viewport**, navigate to the corresponding point on your 3D arch model
   - Use mouse wheel to zoom in/out
   - Use `MMB` (middle mouse button) to rotate the view
   - Use `Shift + MMB` to pan

2. Place an Empty object:
   - Press `Shift + A` (or `Add` menu)
   - Navigate to `Empty > Plain Axes` (or `Sphere` if you prefer a visible marker)
   - The Empty appears at the 3D cursor location

3. Move the Empty to the exact point:
   - Select the Empty (if not already selected)
   - Press `G` to grab/move it
   - Position it precisely on the corresponding anatomical point
   - Left-click to confirm
   - You can use `G` followed by `X`, `Y`, or `Z` to constrain movement to one axis

4. **Name the Empty** (highly recommended):
   - In the Outliner, right-click the Empty and select "Rename"
   - Use the **same name** as the corresponding 2D track (e.g., "Left_Canine_Tip")

5. **Optional**: Move the Empty to the "3D_Landmarks" collection:
   - In the Outliner, drag the Empty into the "3D_Landmarks" collection

6. Repeat for each 2D tracking point you created

**Tips for accurate placement**:
- Take your time - precision directly affects final accuracy
- Use multiple views - rotate the model to see the point from different angles
- Zoom in for precise placement
- Match the exact anatomical location - the tip of a canine on the photo should match the tip of the same canine on the 3D model

Video 11: 3D Landmarks placements

https://github.com/user-attachments/assets/b6c92306-3fbc-4d9e-9823-8c633a8b51d2

---

### Step 8: Link 2D tracks to 3D landmarks

1. In the SmilePnP panel, click the **"Refresh"** button (or "Synchronize landmarks")
   - This loads all your 2D tracking tracks into the correspondence table

2. **The correspondence table appears** below the "Refresh" button
   - Each row shows a 2D track name and an empty field for the 3D object

3. **For each row**:
   - The left column shows the 2D track name
   - The right column has a dropdown to select the corresponding 3D Empty
   - Select the matching 3D Empty from the dropdown
   - If you named them the same, this should be easy to match

4. **Verify your correspondences**:
   - Make sure each 2D track is matched to the correct 3D Empty
   - Double-check that "Left_Canine_Tip" (2D) is matched to "Left_Canine_Tip" (3D), etc.

**Minimum required**: 4 correspondences / 6 or more for calibration

---

### Step 9: Calibrate and solve the camera pose

#### 9.1: Configure calibration

1. In the SmilePnP panel, find the **"Focal"** checkbox (under "Intrinsic calibration")
2. Make sure it's checked (enabled by default)
   - This tells the add-on to calibrate the focal length

#### 9.2: Calibrate the camera (if you have 6 or more correspondences)

1. Verify you have 6+ correspondences (check the correspondence table)
2. Click the **"Calibrate camera"** button
3. Wait for the calculation (usually 1-2 seconds)
4. Check the result:
   - A message appears showing the reprojection error
   - Lower error = better calibration
   - Typical good values are under 1-2 pixels

**Note**: You can skip calibration if you don't have 6+ correspondences, but accuracy will be lower.

#### 9.3: Solve the camera pose

1. Click the **"Solve camera pose"** button
2. Wait for the calculation (usually 1-2 seconds)
3. Check the result:
   - A message appears showing the reprojection error
   - Switch to Camera view (`Numpad 0`) to see the photograph as background

**What you should see**:
- The 3D arch should appear aligned with the photograph (when viewed through the camera)

**Understanding reprojection error**:
- Measures how well the calculated camera parameters match your correspondences
- Measured in pixels
- **Lower is better**: < 1 pixel = excellent, 1-2 pixels = good, > 2 pixels = may need improvement

**If you see "SQPNP failed, using ITERATIVE..."**:
- This is **not an error** - it's an automatic fallback
- The add-on tries multiple algorithms for robustness
- The final result is still accurate

#### 9.4: Reset calibration (if needed)

If you get errors or high reprojection errors:
1. Click the **🔄 Reset** button (next to "Calibrate camera")
2. This resets focal length and other parameters to defaults
3. Start over: Calibrate → Solve pose

---

### Step 10: Configure compositing

#### 10.1: Access compositing help

1. In the SmilePnP panel, click the **"Compositing help"** button (or "Help: Manual compositing")
2. A pop-up window appears with detailed instructions
3. Keep this window open or take notes

#### 10.2: Switch to Compositing workspace

1. At the top of the Blender window, click the **workspace dropdown** (usually says "Layout")
2. Select **"Compositing"** workspace
3. The interface changes to show the Node Editor

**If Compositing workspace doesn't exist**:
- Go to `Window > New Window`
- Or manually switch: `Editor Type > Compositing` in any editor

#### 10.3: Enable nodes and add compositor nodes

1. In the Compositor (Node Editor), check the **"Use Nodes"** checkbox (top right)
2. A "Render Layers" node and "Composite" node appear automatically

3. **Add a Movie Clip node**:
   - Press `Shift + A` (or `Add` menu)
   - Navigate to `Input > Movie Clip`
   - In the node settings, select your photograph from the dropdown

4. **Add an Alpha Over node**:
   - Press `Shift + A`
   - Navigate to `Color > Alpha Over`

5. **Connect the nodes**:
   - **Movie Clip → Alpha Over**: 
     - Connect "Image" output of Movie Clip to "Image" input of Alpha Over
     - Connect "Alpha" output of Movie Clip to "Alpha" input of Alpha Over
   - **Render Layers → Alpha Over**:
     - Connect "Image" output of Render Layers to "Image" input of Alpha Over (this is the Line Art)
   - **Alpha Over → Composite**:
     - Connect "Image" output of Alpha Over to "Image" input of Composite
   - **Alpha Over → Viewer** (optional, for preview):
     - Connect "Image" output of Alpha Over to "Image" input of Viewer

**Node layout**:
```
[Movie Clip] ──┐
               ├──> [Alpha Over] ──> [Composite]
[Render Layers] ──┘                    [Viewer]
```

### Step 10: Render the final composite

1. **Render the image**:
   - Press `F12` (or `Render > Render Image`)
   - Blender renders the scene
   - The final composite appears in the Image Editor

**What you should see**:
- The photograph as the background
- The red Line Art outline overlaid on top
- The outline should align with the dental features in the photograph

**Saving the result**:
- In the Image Editor, go to `Image > Save As`
- Choose a location and filename
- Select your preferred format (PNG recommended for transparency support)

---

### Step 11: Generate quality report (optional)

1. In the SmilePnP panel, click the **"Generate Report"** button
2. A file browser dialog appears. Choose a location to save the report
3. Enter a filename (e.g., "SmilePnP_Report_2026-01-15.txt") and click **"Save"**

The report includes:
- Date and time of generation
- Blender version
- Scene file path
- Active clip information
- Solver message (reprojection error)
- Arcade alignment information
- 2D/3D correspondences with per-landmark errors
- 3D landmarks summary (positions in millimeters)
- Active camera parameters
- 2D clip and optical parameters
- Line Art configuration (if present)

---

## Understanding Your Results

### Visual Alignment Assessment

**How to assess**:
1. Switch to Camera view (`Numpad 0`)
2. Check if the 3D arch aligns with the photograph
3. The Line Art outline should follow the dental features in the photograph

**What good alignment looks like**:
- Line Art outline closely follows the edges of teeth in the photograph
- Correspondences appear to match (when viewed through the camera)
- Reprojection errors are low (< 2 pixels)

**How to obtain better alignment**:
- Review correspondences - check that 2D tracks match correct 3D points
- Verify 3D Empties are precisely placed
- Add more correspondences (8-12 well-placed points)
- Recalibrate and re-solve

### Reprojection Error

**What it means**:
- Measures how accurately the calculated camera pose matches your correspondences
- Measured in **pixels**
- Lower values = better alignment

**How to interpret**:
- **< 1 pixel**: Excellent alignment
- **1-2 pixels**: Good alignment, you can improve it with recalibration and re-solve
- **2-5 pixels**: Need improvement or exclusion
- **> 5 pixels**: Poor alignment : exclusion or correspondance mismatch.

