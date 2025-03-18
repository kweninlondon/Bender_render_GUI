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

    # Extract render details from Blender's output
    frame_range = None
    output_path = None
    frame_filename = None
    image_format = None
    compression = None
    compression_codec = None
    color_depth = None


    for line in result.stdout.split("\n"):
        if "Frame Range:" in line:
            frame_range = line.split("Frame Range:")[-1].strip()
        if "Output Path:" in line:
            output_path = line.split("Output Path:")[-1].strip()
        if "Frame Filename:" in line:
            frame_filename = line.split("Frame Filename:")[-1].strip()
        if "Image Format:" in line:
            image_format = line.split("Image Format:")[-1].strip()
        if "Compression:" in line:
            compression = line.split("Compression:")[-1].strip()
        if "Compression Codec:" in line:
            compression_codec = line.split("Compression Codec:")[-1].strip()
        if "Color Depth:" in line:
            color_depth = line.split("Color Depth:")[-1].strip()


    # Print extracted values summary
    print("\n📜 **Extraction Summary:**")
    print(f"✅ Frame Range: {frame_range}" if frame_range else "❌ Frame Range: MISSING")
    print(f"✅ Output Path: {output_path}" if output_path else "❌ Output Path: MISSING")
    print(f"✅ Frame Filename: {frame_filename}" if frame_filename else "❌ Frame Filename: MISSING")
    print(f"✅ Image Format: {image_format}" if image_format else "❌ Image Format: MISSING")
    print(f"✅ Compression: {compression}" if compression else "❌ Compression: MISSING")
    print(f"✅ Compression Codec: {compression_codec}" if compression else "❌ Compression Codec: MISSING")
    print(f"✅ Color Depth: {color_depth}" if color_depth else "❌ Color Depth: MISSING")

    # # Print final success or failure message
    # if missing_fields:
    #     print("\n⚠️ **Extraction Failed:** Missing ->", ", ".join(missing_fields))
    # else:
    #     print("\n✅ **All Data Successfully Extracted!**")

    if frame_range and output_path and frame_filename and image_format and compression and color_depth:
        start_frame, end_frame = map(int, frame_range.split("-"))
        return {
            "start_frame": start_frame,
            "end_frame": end_frame,
            "output_path": os.path.dirname(output_path),
            "render_filename": frame_filename,
            "image_format": image_format,
            "compression": compression,
            "compression_codec": compression_codec,
            "color_depth": color_depth
        }
    else:
        print("Error: Could not extract all render information.")
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

    # Get the render settings
    scene = bpy.context.scene
    render = scene.render

    # Get the full filepath (includes frame number)
    frame_filepath = render.filepath

    # Ensure the path is absolute
    frame_filepath = bpy.path.abspath(frame_filepath)

    # Extract the directory and full filename
    frame_directory, frame_filename = os.path.split(frame_filepath)

    # Get frame format settings
    image_format = render.image_settings.file_format
    compression = render.image_settings.compression
    compression_codec = "N/A"
    if image_format in ["OPEN_EXR", "OPEN_EXR_MULTILAYER"]:
        compression_codec = render.image_settings.exr_codec
    color_depth = render.image_settings.color_depth

    # Print or store the values
    print(f"Frame Range: {start_frame}-{end_frame}")
    print(f"Output Path: {frame_filepath}")
    print(f"Frame Filename: {frame_filename}")
    print(f"Image Format: {image_format}")
    print(f"Compression: {compression}")
    print(f"Compression Codec: {compression_codec}")
    print(f"Color Depth: {color_depth}")