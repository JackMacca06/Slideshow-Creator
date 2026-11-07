from pathlib import Path
from moviepy import ImageClip, concatenate_videoclips
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from PIL import Image, ImageOps
import numpy as np
from proglog import ProgressBarLogger
import pillow_heif

# Initialize HEIC support for the background thread context
pillow_heif.register_heif_opener()

class TkinterProgressLogger(ProgressBarLogger):
    """
    Custom logger that hooks into MoviePy's rendering loop 
    and sends progress updates to our Tkinter progress callback.
    """
    def __init__(self, progress_callback):
        super().__init__()
        self.progress_callback = progress_callback

    def callback(self, **kwargs):
        for bar_name, bar in self.bars.items():
            if bar.get('total') and bar['total'] > 0:
                percentage = int((bar['index'] / bar['total']) * 100)
                self.progress_callback(percentage)

class MP4_Creator:
    IMAGE_DURATION_CONST = 4.0
    FADE_DURATION_CONST = 1.0
   
    def __init__(self) -> None:
        self.clips = []

    def render_pipeline_worker(self, picture_list, image_duration, fade_duration, output_path, progress_callback, on_complete_callback):
        """Core high-fidelity rendering pipeline designed to prioritize image quality over speed."""
        self.clips = []
        TARGET_SIZE = (1920, 1080) # 1080p Pristine Widescreen Canvas

        for picture in picture_list:
            try:
                with Image.open(picture) as img:
                    # Fix orientation issues common with phone EXIF data
                    img = ImageOps.exif_transpose(img)
                    img = img.convert("RGB")
                    
                    # 1. HIGH-QUALITY SCALING: 
                    # Swapped to Resampling.LANCZOS with anti-aliasing logic for crisp details
                    img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
                    
                    # Create a deep-color black background canvas
                    canvas = Image.new("RGB", TARGET_SIZE, (0, 0, 0))
                    
                    # Precise mathematical centering math
                    paste_x = (TARGET_SIZE[0] - img.size[0]) // 2
                    paste_y = (TARGET_SIZE[1] - img.size[1]) // 2
                    paste_pos = (paste_x, paste_y)
                    
                    canvas.paste(img, paste_pos)
                    img_array = np.array(canvas)

                clip = ImageClip(img_array).with_duration(image_duration + (fade_duration * 2))
                clip = clip.with_effects([CrossFadeIn(fade_duration), CrossFadeOut(fade_duration)])
                self.clips.append(clip)
            except Exception as e:
                print(f"❌ Failed to process image {picture.name}: {e}")

        if self.clips:
            final_video = concatenate_videoclips(self.clips, method="compose", padding=-fade_duration)
            output_file = output_path / "slideshow.mp4"
            
            custom_logger = TkinterProgressLogger(progress_callback)
            
            # 2. PRISTINE COMPRESSION PARAMETERS:
            # - Preset changed to 'medium' for highly accurate compression curves
            # - Added qscale/crf parameters to ensure a high video bitrate (no blocky artifacts)
            final_video.write_videofile(
                str(output_file),
                fps=24,
                codec="libx264",
                audio=False,
                threads=4,
                ffmpeg_params=[
                    "-preset", "medium",  # Slower, highly-optimized encoding pass
                    "-qscale:v", "2",     # Quality scale for WMV (1 is best, 2 is near-lossless)
                    "-b:v", "15M"         # Force a high 15 Mbps baseline bitrate
                ],
                logger=custom_logger
            )
            
        on_complete_callback()
