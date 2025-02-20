import os
import subprocess
import tkinter as tk
from tkinter import filedialog, IntVar, StringVar, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import time
import psutil
import json
from blender_utils.blend_reader import get_blend_info

class BlenderRenderApp:
    SETTINGS_FILE = "blend_settings.json"

    def __init__(self, tk_root):
        self.root = tk_root
        self.rendered_frame_count = None
        self.root = root
        self.root.title("Blender Render Launcher")
        self.root.geometry("700x800")

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

        self.refresh_button = tk.Button(root, text="Fetch Scene Data", command=self.refresh_scene_settings)
        self.refresh_button.config(state="disabled")
        self.refresh_button.pack(pady=5)

        # Frame Range Inputs
        self.start_frame_var = IntVar(value=1)
        self.end_frame_var = IntVar(value=250)

        frame_range_frame = tk.Frame(root)
        frame_range_frame.pack(pady=5)

        tk.Label(frame_range_frame, text="Start Frame:").grid(row=0, column=0, padx=5)
        self.start_frame_entry = tk.Entry(frame_range_frame, textvariable=self.start_frame_var, width=5,
                                          font=("Arial", 12, "bold"), validate="key",
                                          validatecommand=(self.root.register(self.validate_int), "%P"))
        self.start_frame_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_range_frame, text="End Frame:").grid(row=0, column=2, padx=5)
        self.end_frame_entry = tk.Entry(frame_range_frame, textvariable=self.end_frame_var, width=5,
                                        font=("Arial", 12, "bold"), validate="key",
                                        validatecommand=(self.root.register(self.validate_int), "%P"))
        self.end_frame_entry.grid(row=0, column=3, padx=5)

        self.scene_frame_range_var = tk.BooleanVar(value = False)
        self.frame_toggle = ToggleButton(frame_range_frame, on_toggle=self.update_user_settings)
        self.frame_toggle.button.grid(row=0, column=4, padx=5)
        self.frame_toggle.set_state("Default")

        # Define the IntVar before using it
        self.override_output = IntVar(value=0)

        # Checkbox to override output settings
        self.override_checkbox = tk.Checkbutton(root, text="Override Output Path & Name",
                                                variable=self.override_output,
                                                font=("Arial", 12, "bold"),
                                                command=self.toggle_output_options)
        self.override_checkbox.pack(pady=5)
        # Render File Name Input
        self.render_filename = StringVar(value="render_output_####")
        file_name_frame = tk.Frame(root)
        file_name_frame.pack(pady=5)

        self.file_name_label = tk.Label(file_name_frame, text="Render File Name:")
        self.file_name_label.grid(row=0, column=0, padx=5)
        self.filename_entry = tk.Entry(file_name_frame, textvariable=self.render_filename, width=50, font=("Arial", 12))
        self.filename_entry.grid(row=0, column=1, padx=5)
        self.scene_filename_var = tk.BooleanVar(value = False)
        self.filename_toggle = ToggleButton(file_name_frame, on_toggle=self.update_user_settings)
        self.filename_toggle.set_state("Default")


        output_path_frame = tk.Frame(root)
        output_path_frame.pack(pady=5)

        self.output_path_label = tk.Label(output_path_frame, text="Output Path:")
        self.output_path_label.grid(row=0, column=0, padx=5)

        # Output Folder Selection
        self.output_path = StringVar(value=os.path.expanduser("~/Desktop"))

        self.output_label = tk.Label(output_path_frame, text=self.output_path.get(), font=("Arial", 12, "bold"))
        self.output_label.grid(row=0, column=1, padx=5)
        self.output_toggle = ToggleButton(output_path_frame, on_toggle=self.update_user_settings)
        self.output_toggle.set_state("Default")

        self.select_output_button = tk.Button(root, text="Select Output Folder", command=self.select_output_folder)
        self.select_output_button.pack(pady=5)

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

        # Render Button
        self.render_button = tk.Button(root, text="Render", command=self.start_render, bg="#4CAF50", fg="black", font=("Arial", 12, "bold"), padx=10, pady=5)
        self.render_button.pack(pady=10)

        # Cancel Button
        self.cancel_button = tk.Button(root, text="Cancel Render", command=self.cancel_render, bg="red", fg="black", font=("Arial", 12, "bold"))
        self.cancel_button.pack(pady=5)
        self.cancel_button.config(state="disabled")

        self.blend_file_path = None
        self.render_process = None
        self.start_time = None
        self.current_frame_start_time = None
        self.frame_times = []
        self.last_frame_number = None

        # self.first_detected_frame = None  # Initialize it to None
        self.rendering_active = False

        self.start_frame_entry.bind("<Return>", self.release_focus)
        self.end_frame_entry.bind("<Return>", self.release_focus)
        self.filename_entry.bind("<Return>", self.release_focus)

        self.start_frame_var.trace_add("write", lambda *args: self.update_user_settings())
        self.end_frame_var.trace_add("write", lambda *args: self.update_user_settings())
        self.render_filename.trace_add("write", lambda *args: self.update_user_settings())
        self.output_path.trace_add("write", lambda *args: self.update_user_settings())
        self.override_output.trace_add("write", lambda *args: self.update_user_settings())

        self.toggle_output_options()
        print("UI initialized successfully!")

    def load_settings(self):
        """Loads the settings JSON file."""
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_settings(self, settings):
        """Saves settings to the JSON file safely."""
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8", newline="") as f:
                json.dump(settings, f, indent=4)
                f.flush()  # Ensure all data is written before closing
        except Exception as e:
            print(f"Error saving settings: {e}")

    @staticmethod
    def get_blend_last_modified(file_path):
        """Returns the last modified timestamp of a .blend file."""
        return os.path.getmtime(file_path) if os.path.exists(file_path) else None

    def drop_file(self, event):
        file_path = event.data.strip('{}')  # Handle macOS paths
        print(f"Dropped file path: {file_path}")

        if not file_path.endswith(".blend"):
            messagebox.showerror("Error", "Please drop a valid .blend file")
            return

        self.blend_file_path = file_path
        settings = self.load_settings()
        last_modified = self.get_blend_last_modified(file_path)
        changed_emoji = "✅"  # Default value in case it’s used before assignment

        # If the file was previously loaded, restore user settings
        if file_path in settings:
            prev_settings = settings[file_path]
            user_settings = prev_settings.get("user_settings", {})

            # check if the .blend file has changed since last time
            file_changed = prev_settings["last_modified"] != last_modified
            changed_emoji = "⚠️" if file_changed else "✅"
            print(f"{changed_emoji} Blend file has changed: {file_changed}")

            # First, check if user settings exist and apply them
            if user_settings:
                print("🔄 Loading user settings from JSON file...")
                self.start_frame_var.set(user_settings["start_frame"])
                self.end_frame_var.set(user_settings["end_frame"])
                self.output_path.set(user_settings["output_path"])
                self.render_filename.set(user_settings["render_filename"])
                self.override_output.set(user_settings["override_output"])

                toggle_states = user_settings.get("toggle_states", {})
                self.frame_toggle.set_state(toggle_states.get("frame", "Default"))  # Default fallback
                self.filename_toggle.set_state(toggle_states.get("filename", "Default"))
                self.output_toggle.set_state(toggle_states.get("output", "Default"))

                self.toggle_output_options()

            elif "blend_info" in prev_settings:
                print("ℹ️ No user settings found, loading from .blend file...")
                self.start_frame_var.set(prev_settings["blend_info"]["start_frame"])
                self.end_frame_var.set(prev_settings["blend_info"]["end_frame"])
                self.output_path.set(prev_settings["blend_info"]["output_path"])
                self.render_filename.set(prev_settings["blend_info"]["render_filename"])

            else:
                print(f"⚠️ Warning: No previous settings found for {file_path}. Using defaults.")
                blend_info = get_blend_info(file_path)
                if blend_info:
                    self.start_frame_var.set(blend_info["start_frame"])
                    self.end_frame_var.set(blend_info["end_frame"])
                    self.output_path.set(os.path.dirname(blend_info["output_path"]))
                    self.render_filename.set(os.path.basename(blend_info["output_path"]))
                self.frame_toggle.set_state("Scene")
                self.filename_toggle.set_state("Scene")
                self.output_toggle.set_state("Scene")
        else:
            print("🆕 First time loading this .blend file, extracting info from Blender...")
            blend_info = get_blend_info(file_path)
            if blend_info:
                self.start_frame_var.set(blend_info["start_frame"])
                self.end_frame_var.set(blend_info["end_frame"])
                self.output_path.set(os.path.dirname(blend_info["output_path"]))
                self.render_filename.set(os.path.basename(blend_info["output_path"]))

                # Save both file and user settings
                settings[file_path] = {
                    "blend_info": blend_info,
                    "user_settings": {
                        "start_frame": blend_info["start_frame"],
                        "end_frame": blend_info["end_frame"],
                        "output_path": os.path.dirname(blend_info["output_path"]),
                        "render_filename": os.path.basename(blend_info["output_path"]),
                        "override_output": False
                    },
                    "last_modified": last_modified
                }
                self.save_settings(settings)
            self.frame_toggle.set_state("Scene")
            self.filename_toggle.set_state("Scene")
            self.output_toggle.set_state("Scene")

        #  Update the UI label with an emoji if the file changed
        display_path = self.shorten_path(file_path, max_length=50)
        self.file_label.config(text=f"{display_path}", fg="green")
        self.refresh_button.config(state="normal")
        self.root.after(10, lambda: self.update_ui(file_path, changed_emoji))

    @staticmethod
    def shorten_path(path, max_length=50):
        """Shortens a long file path for UI display."""
        if len(path) > max_length:
            start_chars = 15  # Number of characters to keep at the start
            end_chars = max_length - start_chars - 3  # Remaining characters for the end
            new_path = f"{path[:start_chars]}...{path[-end_chars:]}"
            print(new_path)
            return new_path
        return path

    def reset_frame_range(self):
        """Resets the frame range to the values from the .blend file."""
        if not self.blend_file_path:
            messagebox.showerror("Error", "No .blend file loaded!")
            return

        blend_info = get_blend_info(self.blend_file_path)
        if blend_info:
            self.start_frame_var.set(blend_info["start_frame"])
            self.end_frame_var.set(blend_info["end_frame"])

    def toggle_output_options(self):
        """Enable or disable output path and filename entry based on checkbox state."""
        if self.override_output.get():
            self.filename_entry.config(state="normal")  # Enable filename input
            self.output_label.config(state="normal")  # Enable output folder selection
            self.select_output_button.config(state="normal")  # Enable button
            self.file_name_label.config(state="normal") # Enable Label
            self.filename_toggle.button.config(state="normal")  # Enable toggle button
            self.output_toggle.button.config(state="normal")  # Enable toggle button
            self.output_path_label.config(state="normal")

        else:
            self.filename_entry.config(state="disabled")  # Disable filename input
            self.output_label.config(state="disabled")  # Disable output folder selection
            self.select_output_button.config(state="disabled")  # Disable button
            self.file_name_label.config(state="disabled") # Enable Label
            self.filename_toggle.button.config(state="disabled")  # Enable toggle button
            self.output_toggle.button.config(state="disabled")  # Enable toggle button
            self.output_path_label.config(state="disabled")


    def update_user_settings(self):
        """Saves the user's modified settings to the JSON file."""
        if not self.blend_file_path:
            return

        settings = self.load_settings()

        if self.blend_file_path in settings:
            settings[self.blend_file_path]["user_settings"] = {
                "start_frame": self.start_frame_var.get() if self.start_frame_var.get() != "" else 1,  # Default to 1 if empty
                "end_frame": self.end_frame_var.get() if self.end_frame_var.get() != "" else 1,  # Default to 1 if empty
                "output_path": self.output_path.get(),
                "render_filename": self.render_filename.get(),
                "override_output": bool(self.override_output.get()),
                # Save toggle button states
                "toggle_states": {
                    "frame": self.frame_toggle.states[self.frame_toggle.current_state][1],  # Scene, User, or Default
                    "filename": self.filename_toggle.states[self.filename_toggle.current_state][1],
                    "output": self.output_toggle.states[self.output_toggle.current_state][1]
                }
            }
            self.save_settings(settings)
            print(f"✅ Updated user settings for {self.blend_file_path}")

    def update_ui(self, file_path, changed_emoji):
        """ Updates the UI after a file is dropped """
        display_path = self.shorten_path(os.path.basename(file_path), max_length=50)
        label_text = f"{display_path}"
        print(f"Updating label: {label_text}")  # Debugging output
        short_path = self.shorten_path(self.output_path.get())
        self.output_label.config(text=f"{short_path}")
        self.file_label.config(text=label_text, fg="green")
        self.root.update_idletasks()  # Force UI update


        self.root.update()  # Force UI refresh
        self.scene_var.set(f"{changed_emoji} Scene")
        self.scene_label.config(fg="green")

        self.root.update()  # Ensure labels refresh

    def start_render(self):
        if not self.blend_file_path:
            messagebox.showerror("Error", "Please drag and drop a .blend file")
            return

        start_frame = self.start_frame_var.get()
        end_frame = self.end_frame_var.get()
        total_frames = end_frame - start_frame + 1

        # Disable the render button and change its text
        self.render_button.config(state="disabled", text="🚀Rendering...")

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
        ]

        # If override output path is enabled, add output path and filename
        if self.override_output.get():
            output_file = os.path.join(self.output_path.get(), self.render_filename.get())  # Construct full path
            command.extend(["-o", output_file])  # Append output path

        command.append("-a")  # Append animation render flag

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

                        # If this is not the first time we see FRA, and it is a new frame:
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

            # When the render finishes, disable cancel button and unable render button
            self.root.after(10, lambda: self.cancel_button.config(state="disabled"))
            self.root.after(10, lambda: self.render_button.config(state="normal", text="Render"))

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

                self.render_button.config(state="normal", text="Render")
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
            short_path = self.shorten_path(folder)  # Shorten the path for display
            self.output_label.config(text=short_path)  # Update the label text

    def release_focus(self, event):
        """Releases focus from the current widget only if it's an entry field."""
        widget = self.root.focus_get()  # Get the currently focused widget
        if isinstance(widget, tk.Entry):
            widget.master.focus_set()  # Shift focus away only from Entry fields

    def validate_int(self, value):
        """Validate input: only allow positive integers, no empty values."""
        if value.isdigit() or value == "":
            return True
        return False

    def refresh_scene_settings(self):
        """Refreshes the scene settings from the .blend file and updates JSON."""
        if not self.blend_file_path:
            return

        print("🔄 Refreshing scene settings from Blender...")
        blend_info = get_blend_info(self.blend_file_path)

        if blend_info:
            settings = self.load_settings()
            settings[self.blend_file_path]["blend_info"] = blend_info
            settings[self.blend_file_path]["last_modified"] = self.get_blend_last_modified(self.blend_file_path)

            self.scene_var.set(f"✅ Scene")
            self.save_settings(settings)
            print("✅ Scene settings updated in JSON.")

            # Refresh the UI to show new scene settings
            self.apply_scene_settings()


    def toggle_setting(self, setting):
        """Toggles a setting between scene values and user values."""
        if not self.blend_file_path:
            return

        settings = self.load_settings()
        if self.blend_file_path in settings:
            blend_info = settings[self.blend_file_path]["blend_info"]
            user_settings = settings[self.blend_file_path]["user_settings"]

            if setting == "frame":
                is_using_scene = self.toggle_frame_button["text"] == "🎬 Scene"
                if is_using_scene:
                    # Switch to user settings
                    self.start_frame_var.set(user_settings["start_frame"])
                    self.end_frame_var.set(user_settings["end_frame"])
                    self.toggle_frame_button.config(text="📝 Custom")
                else:
                    # Switch to scene settings
                    self.start_frame_var.set(blend_info["start_frame"])
                    self.end_frame_var.set(blend_info["end_frame"])
                    self.toggle_frame_button.config(text="🎬 Scene")

            # Save the toggle state
            self.save_settings(settings)

    def apply_scene_settings(self):
        """Applies the scene settings to the UI (without affecting user settings)."""
        if not self.blend_file_path:
            return

        settings = self.load_settings()
        if self.blend_file_path in settings and "blend_info" in settings[self.blend_file_path]:
            blend_info = settings[self.blend_file_path]["blend_info"]

            self.start_frame_var.set(blend_info["start_frame"])
            self.end_frame_var.set(blend_info["end_frame"])
            self.output_path.set(blend_info["output_path"])
            self.render_filename.set(blend_info["render_filename"])

            print("🎬 Applied scene settings to the UI.")

    def toggle_frame_range_data(self):
        """Toggles the frame range setting from scene to user and allows deselection."""
        if self.scene_frame_range_var.get():
            self.scene_frame_range_var.set(False)  # Manually uncheck
            self.frame_range_toggle_button.config(text="👥")
        else:
            self.scene_frame_range_var.set(True)  # Manually check
            self.frame_range_toggle_button.config(text="🎬")

    def toggle_filename_data(self):
        """Toggles the frame range setting from scene to user and allows deselection."""
        if self.scene_filename_var.get():
            self.scene_filename_var.set(False)  # Manually uncheck
            self.filename_toggle_button.config(text="👥")
        else:
            self.scene_filename_var.set(True)  # Manually check
            self.filename_toggle_button.config(text="🎬")


class ToggleButton:
    def __init__(self, parent, on_toggle=None):
        """
        A reusable toggle button for switching between Scene, User, and Default settings.
        For now, it only prints a message when toggled.

        :param parent: The parent Tkinter frame.
        """
        self.states = [
            ("🎬", "Scene"),
            ("👥", "User"),
            ("⚙️", "Default")
        ]  # (Emoji, Full Name) # Scene, User, Default
        self.current_state = 2  # Start at Scene
        self.on_toggle = on_toggle  # Callback function

        # Create button (only displays emoji)
        self.button = tk.Button(parent, text=self.states[self.current_state][0], command=self.toggle)
        self.button.grid(row=0, column=2, padx=5)

    def toggle(self):
        """Cycles through the 3 states and prints the full name with emoji."""
        self.current_state = (self.current_state + 1) % 3  # 🎬 → 👥 → ⚙️ → 🎬

        emoji, name = self.states[self.current_state]  # Extract new emoji + name
        self.button.config(text=emoji)  # Update button text (emoji only)
        print(f"Loading {emoji} {name} settings")  # Print full message
        if self.on_toggle:
            self.on_toggle()  # Trigger save when toggled

    def set_state(self, state_name):
        """
        Sets the button state externally.

        :param state_name: Must be "Scene", "User", or "Default".
        """
        state_map = {"Scene": 0, "User": 1, "Default": 2}
        if state_name in state_map:
            self.current_state = state_map[state_name]
            emoji, _ = self.states[self.current_state]
            self.button.config(text=emoji)  # Update button text
            print(f"Button set to {emoji} {state_name} externally")
        else:
            print(f"⚠️ Invalid state: {state_name}. Must be 'Scene', 'User', or 'Default'.")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = BlenderRenderApp(root)
    root.mainloop()
