import subprocess
import os


def get_blend_info(blend_file):
    """Runs Blender in background mode to extract scene frame range."""

    blender_exe = "/Applications/Blender.app/Contents/MacOS/Blender"
    script_path = os.path.abspath(__file__)  # Get the full path to this script

    command = [
        blender_exe, "-b", blend_file, "--python", script_path
    ]

    # Run Blender and capture output
    result = subprocess.run(command, capture_output=True, text=True)

    # Print Blender's output for debugging
    print("Blender Output:")
    print(result.stdout)
    print(result.stderr)

    # Extract frame range from Blender's output
    frame_range = None
    for line in result.stdout.split("\n"):
        if "Frame Range:" in line:
            frame_range = line.split("Frame Range:")[-1].strip()
        if "Output Path:" in line:
            output_path = line.split("Output Path:")[-1].strip()

    if frame_range:
        start_frame, end_frame = map(int, frame_range.split("-"))
        return {"start_frame": start_frame, "end_frame": end_frame, "output_path": output_path}
    else:
        print("Error: Could not extract info.")
        return None


# If Blender is running this script, extract and print the frame range
if __name__ == "__main__":
    import bpy
    import sys

    print("Received arguments:", sys.argv)

    # Find the .blend file argument
    blend_file = None
    for arg in sys.argv:
        if arg.endswith(".blend"):
            blend_file = arg
            break

    if not blend_file:
        print("Error: No .blend file found in arguments.")
        sys.exit(1)


    # Get the scene frame range
    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end

    # Get the render output path
    output_path = bpy.context.scene.render.filepath

    print(f"Frame Range: {start_frame} - {end_frame}")
    print(f"Output Path: {output_path}")