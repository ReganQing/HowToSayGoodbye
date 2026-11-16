import imageio.v3 as iio
import numpy as np
from PIL import Image

def dark_runs(path):
    frames = iio.imread(path, index=None)
    lum = [float(np.asarray(Image.fromarray(f).convert("L")).mean()) for f in frames]
    runs = []
    start = None
    for i, v in enumerate(lum):
        if v < 30:
            if start is None: start = i
        else:
            if start is not None:
                runs.append((start, i-1, round(min(lum[start:i]),1)))
                start = None
    if start is not None: runs.append((start, len(lum)-1, round(min(lum[start:]),1)))
    print(path, "frames:", len(frames))
    for r in runs: print("  dark run:", r)

dark_runs("assets/h3_video/roughcut_v05.mp4")
dark_runs("assets/h3_video/roughcut_v06.mp4")
