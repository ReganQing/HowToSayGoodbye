import imageio.v3 as iio
import os
d = "assets/previs/frames08"
frames = [iio.imread(os.path.join(d, f"frame_{f:04d}.png")) for f in range(1, 193)]
iio.imwrite("assets/previs/previs_shot08.mp4", frames, fps=24, codec="libx264", quality=7)
print("saved", len(frames))
