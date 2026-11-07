import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from file_explorer import File_Explorer
from wmv_creator import WMV_Creator

class SlideshowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Video Slideshow Compiler")
        self.root.geometry("600x300")  # Bumped height slightly to accommodate the configuration row
        self.root.resizable(False, False)

        self.explorer = File_Explorer()
        self.creator = WMV_Creator()
        
        self.progress_queue = queue.Queue()
        self.selected_pictures = []
        
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Folder Selection Row
        self.select_btn = ttk.Button(main_frame, text="Select Image Folder", command=self.browse_folder)
        self.select_btn.pack(fill=tk.X, pady=5)

        self.folder_label = ttk.Label(main_frame, text="No folder selected", wraplength=380, foreground="gray")
        self.folder_label.pack(fill=tk.X, pady=2)

        # 2. Configuration Settings Row (Duration and Fade)
        config_frame = ttk.LabelFrame(main_frame, text=" Slideshow Settings ", padding="10")
        config_frame.pack(fill=tk.X, pady=10)

        # Image Duration Input
        ttk.Label(config_frame, text="Image Duration (s):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.img_dur_var = tk.DoubleVar(value=4.0)
        self.img_dur_spin = ttk.Spinbox(config_frame, from_=0.5, to=60.0, increment=0.5, textvariable=self.img_dur_var, width=8)
        self.img_dur_spin.grid(row=0, column=1, padx=(0, 15), sticky=tk.W)

        # Fade Duration Input
        ttk.Label(config_frame, text="Fade Duration (s):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.fade_dur_var = tk.DoubleVar(value=1.0)
        self.fade_dur_spin = ttk.Spinbox(config_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.fade_dur_var, width=8)
        self.fade_dur_spin.grid(row=0, column=3, sticky=tk.W)

        # 3. Compile Row (Disabled until images are fetched)
        self.compile_btn = ttk.Button(main_frame, text="Compile Slideshow (.wmv)", command=self.start_rendering, state=tk.DISABLED)
        self.compile_btn.pack(fill=tk.X, pady=(0, 10))

        # 4. Progress Display
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=380, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(main_frame, text="Status: Ready", font=("Helvetica", 10))
        self.status_label.pack(anchor=tk.W)

    def browse_folder(self):
        self.selected_pictures = self.explorer.get_picture_list_from_directory()
        folder_path = self.explorer.get_path()

        if self.selected_pictures and folder_path:
            self.folder_label.config(text=f"Selected Folder: {folder_path.name} ({len(self.selected_pictures)} images)", foreground="black")
            self.compile_btn.config(state=tk.NORMAL)
            self.progress_bar['value'] = 0
            self.status_label.config(text="Status: Ready to compile.")
        else:
            self.folder_label.config(text="No folder selected", foreground="gray")
            self.compile_btn.config(state=tk.DISABLED)

    def start_rendering(self):
        # Read the current customized timing values from the inputs
        try:
            chosen_image_duration = self.img_dur_var.get()
            chosen_fade_duration = self.fade_dur_var.get()
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for the duration settings.")
            return

        # Safeguard: Make sure the transition isn't longer than the slide visibility itself
        if chosen_fade_duration * 2 >= chosen_image_duration:
            messagebox.showwarning("Timing Warning", "Fade duration is too long compared to image duration! Please lower your fade time.")
            return

        # Lock UI components while background processing handles frames
        self.select_btn.config(state=tk.DISABLED)
        self.compile_btn.config(state=tk.DISABLED)
        self.img_dur_spin.config(state=tk.DISABLED)
        self.fade_dur_spin.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Starting background render pipeline...")
        self.progress_bar['value'] = 0

        render_thread = threading.Thread(
            target=self.creator.render_pipeline_worker,
            args=(
                self.selected_pictures, 
                chosen_image_duration, 
                chosen_fade_duration, 
                self.explorer.get_path(),
                self.enqueue_progress,  
                self.enqueue_completion 
            ),
            daemon=True
        )
        render_thread.start()
        
        self.root.after(100, self.poll_progress_queue)

    def enqueue_progress(self, percent):
        self.progress_queue.put(("PROGRESS", percent))

    def enqueue_completion(self):
        self.progress_queue.put(("COMPLETE", 100))

    def poll_progress_queue(self):
        try:
            while True:
                msg_type, value = self.progress_queue.get_nowait()
                
                if msg_type == "PROGRESS":
                    self.progress_bar['value'] = value
                    self.status_label.config(text=f"Status: Rendering Video... {value}%")
                    
                elif msg_type == "COMPLETE":
                    self.progress_bar['value'] = 100
                    self.status_label.config(text="Status: Finished Rendering!")
                    
                    # Unlock UI components when done
                    self.select_btn.config(state=tk.NORMAL)
                    self.img_dur_spin.config(state=tk.NORMAL)
                    self.fade_dur_spin.config(state=tk.NORMAL)
                    
                    messagebox.showinfo("Success", f"Slideshow compiled successfully!\nSaved inside image directory.")
                    return 
                    
        except queue.Empty:
            pass 
        
        self.root.after(100, self.poll_progress_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideshowApp(root)
    root.mainloop()
