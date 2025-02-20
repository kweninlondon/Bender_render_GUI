import os
import subprocess
import tkinter as tk
from tkinter import filedialog, IntVar, StringVar, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import re
import time
import psutil

class BlenderRenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blender Render Launcher")
        self.root.geometry("700x600")

        print("Creating UI elements...")  # Debugging message

        # Drag and Drop Blender File Label
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.drop_file)

        self.file_label = tk.Label(root, text="Drag and drop a .blend file here",
                                   relief="ridge", font=("Arial", 14, "bold"), width=50, height=2)
        self.file_label.pack(pady=10)

        # Scene Loaded Display
        self.scene_var = StringVar(value="No scene loaded")
        self.scene_label = tk.Label(root, textvariable=self.scene_var, font=("Arial", 14, "bold"))
        self.scene_label.pack()

        # Checkbox to override output settings
        self.override_output = IntVar(value=0)
        self.override_checkbox = tk.Checkbutton(root, text="Override Output Path & Name",
                                                variable=self.override_output, font=("Arial", 12, "bold"))
        self.override_checkbox.pack(pady=5)

        # Render File Name Input
        self.render_filename = StringVar(value="render_output")
        file_name_frame = tk.Frame(root)
        file_name_frame.pack(pady=5)

        tk.Label(file_name_frame, text="Render File Name:").grid(row=0, column=0, padx=5)
        self.filename_entry = tk.Entry(file_name_frame, textvariable=self.render_filename, width=50, font=("Arial", 12))
        self.filename_entry.grid(row=0, column=1, padx=5)

        # Frame Range Inputs
        self.start_frame_var = IntVar(value=1)
        self.end_frame_var = IntVar(value=250)

        frame_range_frame = tk.Frame(root)
        frame_range_frame.pack(pady=5)

        tk.Label(frame_range_frame, text="Start Frame:").grid(row=0, column=0, padx=5)
        self.start_frame_entry = tk.Entry(frame_range_frame, textvariable=self.start_frame_var, width=5, font=("Arial", 12, "bold"))
        self.start_frame_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_range_frame, text="End Frame:").grid(row=0, column=2, padx=5)
        self.end_frame_entry = tk.Entry(frame_range_frame, textvariable=self.end_frame_var, width=5, font=("Arial", 12, "bold"))
        self.end_frame_entry.grid(row=0, column=3, padx=5)

        # Output Folder Selection
        self.output_path = StringVar(value=os.path.expanduser("~/Desktop"))
        tk.Button(root, text="Select Output Folder", command=self.select_output_folder).pack(pady=5)
        self.output_label = tk.Label(root, textvariable=self.output_path, fg="black", font=("Arial", 12, "bold"))
        self.output_label.pack()

        # Render Button
        self.render_button = tk.Button(root, text="Render", command=self.start_render, bg="#4CAF50", fg="black", font=("Arial", 12, "bold"), padx=10, pady=5)
        self.render_button.pack(pady=10)

        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar", thickness=60)
        # Overall Progress Bar
        self.overall_progress = ttk.Progressbar(root, style="Custom.Horizontal.TProgressbar", orient="horizontal", length=400, mode="determinate")
        self.overall_progress.pack(pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(root, style="Custom.Horizontal.TProgressbar", orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # Frame Progress Label
        self.frame_progress_var = StringVar(value="Frames Rendered: 0/0")
        self.frame_progress_label = tk.Label(root, textvariable=self.frame_progress_var, font=("Arial", 12))
        self.frame_progress_label.pack()

        # Time Tracking Labels
        self.elapsed_time_var = StringVar(value="Elapsed Time: --:--:--")
        self.current_frame_time_var = StringVar(value="Current Frame Time: --:--:--")
        self.avg_time_per_frame_var = StringVar(value="Avg Time per Frame: --.--")
        self.estimated_time_var = StringVar(value="Estimated Time Left: --:--:--")

        self.elapsed_time_label = tk.Label(root, textvariable=self.elapsed_time_var, font=("Arial", 12))
        self.elapsed_time_label.pack()

        self.current_frame_time_label = tk.Label(root, textvariable=self.current_frame_time_var, font=("Arial", 12))
        self.current_frame_time_label.pack()

        self.avg_time_per_frame_label = tk.Label(root, textvariable=self.avg_time_per_frame_var, font=("Arial", 12))
        self.avg_time_per_frame_label.pack()

        self.estimated_time_label = tk.Label(root, textvariable=self.estimated_time_var, font=("Arial", 12))
        self.estimated_time_label.pack()

        # Cancel Button
        self.cancel_button = tk.Button(root, text="Cancel Render", command=self.cancel_render, bg="red", fg="white", font=("Arial", 12, "bold"))
        self.cancel_button.pack(pady=5)
        self.cancel_button.config(state="disabled")

        self.blend_file_path = None
        self.render_process = None
        self.start_time = None
        self.current_frame_start_time = None
        self.frame_times = []
        # self.first_detected_frame = None  # Initialize it to None
        self.rendering_active = False
        print("UI initialized successfully!")

    def get_output_path(self, blend_file):
        """ Extracts the render output path and file name from a Blender file using the command line """
        script = """
    import bpy
    print(bpy.context.scene.render.filepath)
        """

        try:
            output = subprocess.check_output([
                "/Applications/Blender.app/Contents/MacOS/Blender",
                "-b", blend_file, "--python-expr", script
            ], stderr=subprocess.DEVNULL, text=True)

            full_output_path = output.strip().split("\n")[-1]

            # If Blender did not return a path, fallback to blend file directory
            if not full_output_path or "Blender quit" in full_output_path:
                return os.path.dirname(blend_file), "render_output"

            output_directory = os.path.dirname(full_output_path)
            output_filename = os.path.basename(full_output_path)

            return output_directory, output_filename
        except Exception as e:
            return os.path.dirname(blend_file), "render_output"  # Fallback on error

    def drop_file(self, event):
        file_path = event.data.strip('{}')  # Handle macOS paths
        print(f"Dropped file path: {file_path}")

        if file_path.endswith(".blend"):
            self.blend_file_path = file_path

            extracted_output_path, extracted_filename = self.get_output_path(file_path)

            self.output_path.set(extracted_output_path)  # Set output folder path
            self.render_filename.set(extracted_filename)  # Set output file name

            display_path = self.shorten_path(file_path, max_length=50)
            self.file_label.config(text=display_path, fg="green")

            self.root.after(10, lambda: self.update_ui(file_path))
        else:
            messagebox.showerror("Error", "Please drop a valid .blend file")

    def shorten_path(self, path, max_length=50):
        """ Shortens a long file path for UI display. """
        if len(path) > max_length:
            return f"{path[:15]}...{path[-30:]}"  # Show start and end of path
        return path

    def update_ui(self, file_path):
        """ Updates the UI after a file is dropped """
        self.file_label.config(text=os.path.basename(file_path), fg="green")
        self.root.update()  # Force UI refresh
        self.scene_var.set(f"✅ Scene")
        self.scene_label.config(fg="green")

        self.root.update()  # Ensure labels refresh

    def start_render(self):
        if not self.blend_file_path:
            messagebox.showerror("Error", "Please drag and drop a .blend file")
            return

        start_frame = self.start_frame_var.get()
        end_frame = self.end_frame_var.get()
        total_frames = end_frame - start_frame + 1

        # Reset UI elements
        self.frame_progress_var.set(f"Frames Rendered: 0/{total_frames}")
        self.overall_progress["maximum"] = total_frames
        self.overall_progress["value"] = 0
        self.elapsed_time_var.set("Elapsed Time: 00:00:00")
        self.current_frame_time_var.set("Current Frame Time: 0.00s")
        self.avg_time_per_frame_var.set("Avg Time per Frame: Calculating...")
        self.estimated_time_var.set("Estimated Time Left: Calculating...")

        # Reset tracking variables
        self.start_time = time.time()
        self.frame_times = []  # Store frame render times
        self.current_frame_start_time = time.time()
        self.last_frame_number = None  # Track last processed frame
        self.rendered_frame_count = 0  # Track number of frames actually rendered

        command = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "-b", self.blend_file_path,
            "-F", "OPEN_EXR_MULTILAYER",
            "-x", "1",
            "-s", str(start_frame),
            "-e", str(end_frame),
            "-a"
        ]

        self.cancel_button.config(state="normal")

        self.rendering_active = True  # Set flag before starting timer
        self.update_elapsed_time()  # Start updating elapsed time

        def run_render():
            self.render_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.rendering_active = True  # Allow updates while rendering
            rendering_frame = None
            frame_time = 0
            for line in self.render_process.stdout:
                if not self.rendering_active:  # Stop updating if rendering was canceled
                    break
                print(line.strip())  # Debugging output

                # Detect frame progress from Blender's output

                if "Fra:" in line:
                    try:
                        frame_number = int(line.split("Fra:")[1].split()[0])  # Extract actual Fra number

                        # If this is not the first time we see FRA and it is a new frame:
                        if rendering_frame is not None and rendering_frame != frame_number:
                            now = time.time()
                            frame_time = now - self.current_frame_start_time
                            if frame_time > 0:  # Ensure only positive times are added
                                self.frame_times.append(frame_time)
                            print(f"✅ Frame {rendering_frame} finished in {frame_time:.2f}s")

                        # Only update when a new frame is detected
                        if rendering_frame is None or rendering_frame != frame_number:
                            self.current_frame_start_time = time.time()  # Reset time for the new frame
                            rendering_frame = frame_number

                        # Update UI with new frame number
                        now = time.time()
                        elapsed_time = int(now - self.start_time)
                        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

                        avg_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0
                        if avg_time > 60:
                            avg_time_str = time.strftime("%M:%S", time.gmtime(avg_time))
                        else:
                            avg_time_str = f"{avg_time:.2f}s"
                        estimated_left = avg_time * (end_frame - frame_number)
                        estimated_left_str = time.strftime("%H:%M:%S", time.gmtime(estimated_left)) if self.frame_times else "--:--:--"

                        # Update UI
                        self.root.after(10, lambda: [
                            self.frame_progress_var.set(f"Frame Rendered: {frame_number}/{end_frame}"),
                            self.elapsed_time_var.set(f"Elapsed Time: {elapsed_str}"),
                            self.current_frame_time_var.set(f"Current Frame Time: {frame_time:.2f}s"),
                            self.avg_time_per_frame_var.set(f"Avg Time per Frame: {avg_time_str}s"),
                            self.estimated_time_var.set(f"Estimated Time Left: {estimated_left_str} for {end_frame - frame_number} Frames"),
                            self.overall_progress.config(value=frame_number - start_frame)
                        ])
                        self.rendered_frame_count += 1

                    except Exception as e:
                        print(f"Error parsing frame number: {e}")

            if rendering_frame is not None:
                now = time.time()
                frame_time = now - self.current_frame_start_time
                if frame_time > 0:
                    self.frame_times.append(frame_time)
                print(f"✅ Final Frame {rendering_frame} finished in {frame_time:.2f}s")

            # When the render finishes, disable cancel button
            self.root.after(10, lambda: self.cancel_button.config(state="disabled"))

        # Run the render process in a separate thread to prevent UI freezing
        threading.Thread(target=run_render, daemon=True).start()

    def update_elapsed_time(self):
        """ Updates elapsed time and current frame time every second. Stops if rendering is canceled. """
        if self.rendering_active:  # Ensure updates only happen if rendering is active
            now = time.time()
            elapsed_time = int(now - self.start_time)
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

            if self.current_frame_start_time and (now - self.current_frame_start_time) > 0.1:
                current_frame_time = now - self.current_frame_start_time
                frame_time_str = f"{current_frame_time:.2f}s"
            else:
                frame_time_str = self.current_frame_time_var.get().replace("Current Frame Time: ", "")

            # Update UI elements
            self.elapsed_time_var.set(f"Elapsed Time: {elapsed_str}")
            self.current_frame_time_var.set(f"Current Frame Time: {frame_time_str}")

            # Ensure the function is scheduled again if rendering is still active
            self.root.after(1000, self.update_elapsed_time)

    def update_progress(self, frame_text, progress_percent):
        """ Updates frame progress text and progress bar """
        self.frame_progress_var.set(frame_text)
        self.progress["value"] = progress_percent
        self.root.update()

    def cancel_render(self):
        """Stops the Blender rendering process and resets UI."""
        if self.render_process:
            try:
                # Get parent process
                parent = psutil.Process(self.render_process.pid)

                # Try to terminate all child processes first
                for child in parent.children(recursive=True):
                    child.terminate()

                # Try terminating main process
                parent.terminate()

                # Wait a moment, then force kill if still running
                gone, alive = psutil.wait_procs([parent], timeout=5)
                if alive:
                    for proc in alive:
                        proc.kill()  # Force kill remaining processes

                self.render_process = None  # Reset process reference

                # Stop timers from updating but keep the last recorded values
                self.rendering_active = False  # This will prevent further UI updates

                # Update UI safely
                self.cancel_button.config(state="disabled")
                if hasattr(self, "progress"):
                    self.progress["value"] = 0  # Reset progress bar
                if hasattr(self, "frame_progress_var"):
                    self.frame_progress_var.set("Render Canceled")

                messagebox.showinfo("Render Canceled", "Rendering has been stopped.")

            except psutil.NoSuchProcess:
                print("Error: Process not found. It may have already stopped.")
            except Exception as e:
                print(f"Error while stopping render: {e}")

    def select_output_folder(self):
        initial_dir = self.output_path.get() if os.path.exists(self.output_path.get()) else os.path.expanduser("~")
        folder = filedialog.askdirectory(initialdir=initial_dir, title="Select Output Folder")
        if folder:
            self.output_path.set(folder)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = BlenderRenderApp(root)
    root.mainloop()
