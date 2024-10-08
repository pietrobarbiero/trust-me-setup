import os
import time
from datetime import datetime
from utils import save_pid

import numpy as np
import tifffile
from camera import Camera
from flirpy.camera.lepton import Lepton


def formatted_time():
    return "{:%Y-%m-%d$%H-%M-%S-%f}".format(datetime.now())


class Thermal(Camera):
    """Class for thermal camera data capture support"""

    def __init__(
        self,
        fps=8,
        resolution=(160, 120),
        save_directory="data/thermal",
        chunk_size=1200,
    ):
        super(Thermal, self).__init__(
            fps, resolution, save_directory, chunk_size=chunk_size
        )

        print(
            f"Thermal camera set with FPS: {self.fps} and resolution: {self.resolution}!"
        )

    def initCamera(self):
        self.camera = Lepton()

    def convertToCelsius(self, img):
        assert type(img) == np.ndarray, "Image must be a numpy array"

        return img / 100 - 273.15

    def saveToDisk(self, name, img):
        if img is not None and len(img) > 0:
            tifffile.imwrite(
                f"{self.save_directory}/{name}_{formatted_time()}.tiff",
                img,
                photometric="minisblack",
                bigtiff=True,
                compression="lzw",
            )
        else:
            print("No image, skipping [thermal.py]")

    def captureImages(
        self,
        name="out",
        seconds=10,
        to_celsius=True,
        start_event=None,
        # self.chunk_size=1200,
    ):
        """to_celsius: Whether to convert the image to celsius or keep values in Kelvin * 100
        self.chunk_size: interval for saving video in seconds"""

        save_pid("thermal")
        self.initCamera()

        if start_event:
            start_event.wait()

        if seconds < 0 or seconds is None:
            seconds = float("inf")

        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

        start_time = time.time()

        # Array for saving frames
        video = []
        current_time = start_time

        try:
            while time.time() - start_time < seconds:
                frame = self.camera.grab()  # .astype(np.float32)

                if frame is None:
                    print("Can't receive frame. Exiting...")
                    break

                # Convert to celsius
                frame = self.convertToCelsius(frame) if to_celsius else frame

                # Save frame to array
                video.append(frame)

                # Write to disk
                if len(video) > 0 and time.time() - current_time >= self.chunk_size:
                    self.saveToDisk(name, video)

                    # Empty video array
                    video = []
                    current_time = time.time()

        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                print("Keyboard Interrupt [thermal.py]")
            else:
                print("Thermal camera error!", e)

        finally:
            self.saveToDisk(name, video)   # Might cause empty saves but necessary
            print("Done...[thermal.py]")


if __name__ == "__main__":
    lep = Thermal()
    lep.initCamera()
    lep.configureCamera()
    lep.captureImages(name="test", seconds=10, to_celsius=True, start_event=None)
