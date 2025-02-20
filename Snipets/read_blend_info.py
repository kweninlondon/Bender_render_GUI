import bpy
import sys

# Print all arguments to debug
print("Received arguments:", sys.argv)

# Find the .blend file argument in sys.argv
blend_file = None
for arg in sys.argv:
    if arg.endswith(".blend"):
        blend_file = arg
        break

# Ensure a .blend file is found
if not blend_file:
    print("Error: No .blend file found in arguments.")
    sys.exit(1)

print(f"Opening Blender file: {blend_file}")

# Open the Blender file
bpy.ops.wm.open_mainfile(filepath=blend_file)

# Get the scene frame range
start_frame = bpy.context.scene.frame_start
end_frame = bpy.context.scene.frame_end

print(f"Frame Range: {start_frame} - {end_frame}")