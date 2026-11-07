from pathlib import Path
from moviepy import ImageClip, concatenate_videoclips
# Import the crossfade effects explicitly for MoviePy v2.x
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from PIL import Image
import numpy as np
from proglog import ProgressBarLogger

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

class WMV_Creator:
    IMAGE_DURATION_CONST = 4.0
    FADE_DURATION_CONST = 1.0
   
    def __init__(self) -> None:
        self.clips = []

    def render_pipeline_worker(self, picture_list, image_duration, fade_duration, output_path, progress_callback, on_complete_callback):
        """Core rendering pipeline designed to be executed inside a background thread."""
        self.clips = []
        TARGET_SIZE = (1920, 1080) # 1080p Widescreen Canvas

        for picture in picture_list:
            try:
                with Image.open(picture) as img:
                    img = img.convert("RGB")
                    img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
                    
                    canvas = Image.new("RGB", TARGET_SIZE, (0, 0, 0))
                    
                    # FIXED: Element-wise tuple subtraction for widths and heights
                    paste_x = (TARGET_SIZE[0] - img.size[0]) // 2
                    paste_y = (TARGET_SIZE[1] - img.size[1]) // 2
                    paste_pos = (paste_x, paste_y)
                    
                    canvas.paste(img, paste_pos)
                    
                    img_array = np.array(canvas)

                clip = ImageClip(img_array).with_duration(image_duration + (fade_duration * 2))
                
                # FIXED: Correct syntax for adding transitions in MoviePy 2.x vfx pipeline
                clip = clip.with_effects([CrossFadeIn(fade_duration), CrossFadeOut(fade_duration)])
                
                self.clips.append(clip)
            except Exception as e:
                print(f"❌ Failed to process image {picture.name}: {e}")

        if self.clips:
            final_video = concatenate_videoclips(self.clips, method="compose", padding=-fade_duration)
            output_file = output_path / "slideshow.wmv"
            
            custom_logger = TkinterProgressLogger(progress_callback)
            
            final_video.write_videofile(
                str(output_file),
                fps=24,
                codec="wmv2",
                audio=False,
                threads=4,
                ffmpeg_params=["-preset", "ultrafast"],
                logger=custom_logger
            )
            
        on_complete_callback()
