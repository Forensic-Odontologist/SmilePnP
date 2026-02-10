## Troubleshooting

### The panel doesn't appear

**Solutions:**
1. Check the editor: Switch to `Clip Editor > Tracking` mode
2. Check preferences: `Edit > Preferences > Add-ons`, search for "SmilePnP" and check the box
3. Press `N` to open the right-side properties panel

### OpenCV not found

Click **"Install OpenCV"** in the panel. If installation fails, you may need to install OpenCV manually using Blender's Python. See the troubleshooting section for details.

### "Apply outline" doesn't work

**Symptom**: Error "No Line Art object selected" or "Object X is not a Grease Pencil object"

**Solution**: 
1. Create a Grease Pencil object: `Shift + A > Grease Pencil > Empty`
2. Add a Line Art modifier: Properties panel > Modifier Properties > Add Modifier > Line Art
3. In the SmilePnP panel, select this object in the **"Line Art"** field
4. Try the button again

### "Solve camera pose" doesn't work

**Symptom 1**: Error "No camera selected"

**Solution**:
1. Check that you clicked **"Initialize scene"** (creates the "Camera" camera)
2. In the SmilePnP panel, select "Camera" in the **"Camera"** field
3. Try again

**Symptom 2**: Error "At least 4 correspondances required"

**Solution**:
1. Check your correspondence table - you need at least 4 correspondences
2. Add more 2D tracks and 3D Empties
3. Click "Refresh" and match them in the table
4. Try again

**Symptom 3**: Errors after successive modifications

**Solution**:
1. Always use the same camera for all calculations
2. If you modify landmarks, click **"Calibrate camera"** then **"Solve camera pose"** again
3. If errors persist, click **🔄 Reset** and start over

**Note**: The message "SQPNP failed, using ITERATIVE algorithm..." is not an error - it's an automatic fallback that works correctly.

### OpenCV errors after multiple calibrations

**Symptom**: Errors "Focal length must be positive" or "Assertion failed" after several calibrations

**Solutions**:
1. Click the **🔄 Reset** button (next to "Calibrate camera")
2. This resets all camera parameters to safe defaults
3. Start fresh: Calibrate → Solve pose
4. Check your correspondences - make sure 3D Empties are precisely placed

**Prevention**:
- Don't calibrate repeatedly without changing correspondences
- If you modify landmarks: Always do Calibrate → Solve (in that order)
- Use 6+ correspondences for more stable calibration

---
