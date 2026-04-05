import moviepy
from moviepy import ImageClip
import numpy as np

clip = ImageClip(np.zeros((100, 100, 3), dtype=np.uint8))
print(f"MoviePy version: {moviepy.__version__}")
print(f"ImageClip type: {type(clip)}")
print(f"Attributes: {dir(clip)}")
