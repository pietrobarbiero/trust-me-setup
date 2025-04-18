import argparse
import json
import multiprocessing
import time
import getpass
import os
from utils import save_pid 
import subprocess

# If running capture_data.py (this file)
from camera import RGBCamera
from microphone import Mic
from realsense import Realsense
from thermal import Thermal

# For running from main.py
# from capture_data.camera import Camera
# from capture_data.realsense import Realsense
# from capture_data.thermal import Thermal

# Default values that are already set in the hardware_config.json
# Use only for reference - if you want to change resolutions change corresponding values in the hw_config.json
# RGB_RES = (1920, 1080)
# DEPTH_RES = (640, 480)
# THERM_RES = (160, 120)
# HIGH_RES = (3840, 2160)

# --------------------------------------------------------------------------------------
# Due to multiprocessing we can only initialize the objects in this file - internal
# initializations and configs must happen within the class methods (in the subprocess),
# since multiprocessing attempts to pickle the objects created in the main process,
# which causes an error since objects like VideoCapture() are unpickable.
# --------------------------------------------------------------------------------------

# Get username from file if not specified
try:
    with open("/home/$(whoami)/trust-me-setup/tmp/current_username", "r") as f:
        default_username = f.read().strip()
except:
    default_username = "user1"

# Add command line arguments
parser = argparse.ArgumentParser(
    prog="Data Capture",
    description="Run to simultaneously capture data from multiple devices",
    epilog="Any bugs in the code are property of JSI",
)

parser.add_argument("-n", "--name", default=default_username, type=str)
parser.add_argument("-d", "--duration", default="28800", type=int)


hw_config = None


class CaptureData:
    WARMUP_TIME = 30

    def __init__(self, filename="test", seconds=28800, show_rgb=False):
        global hw_config

        self.show_rgb = show_rgb
        self.hw_config = hw_config

        self.init_objects()
        self.config(name=filename, seconds=seconds)

    def init_objects(self):
        """Creates objects with properties specified in the hardware_config.json"""


        self.realsense = Realsense(
            fps=self.hw_config["depth"]["fps"],
            resolution=(
                self.hw_config["depth"]["resolution_x"],
                self.hw_config["depth"]["resolution_y"],
            ),
            chunk_size=self.hw_config["depth"]["chunk_length"],
            save_directory="installers/data_collection/data/realsense",
        )

        self.thermal = Thermal(
            fps=self.hw_config["thermal"]["fps"],
            resolution=(
                self.hw_config["thermal"]["resolution_x"],
                self.hw_config["thermal"]["resolution_y"],
            ),
            save_directory="installers/data_collection/data/thermal",
            chunk_size=self.hw_config["thermal"]["chunk_length"],
        )

        self.audio = Mic(
            sampling_rate=self.hw_config["audio"]["sampling_rate"],
            n_channels=self.hw_config["audio"]["n_channels"],
            chunk_length=self.hw_config["audio"]["chunk_length"],
            save_directory="installers/data_collection/data/audio",
        )

        # self.rgb = RGBCamera(
            # fps=self.hw_config["rgb"]["fps"],
            # resolution=(
                # self.hw_config["rgb"]["resolution_x"],
                # self.hw_config["rgb"]["resolution_y"],
            # ),
            # channel=self.hw_config["rgb"]["channel"],
            # store_video=True,
            # save_directory="installers/data_collection/data/rgb",
            # chunk_size=self.hw_config["rgb"]["chunk_length"],
        # )

        self.hires = RGBCamera(
            fps=self.hw_config["hires"]["fps"],
            resolution=(
                self.hw_config["hires"]["resolution_x"],
                self.hw_config["hires"]["resolution_y"],
            ),
            channel=self.hw_config["hires"]["channel"],
            store_video=True,
            save_directory="installers/data_collection/data/hires",
            chunk_size=self.hw_config["hires"]["chunk_length"],
        )

       
    def config(self, name, seconds):
        """Creates video and audio processes.

        Args:
            seconds (int, optional): Defaults to 10.
            name (str, optional): Defaults to "test".
        """

        # Event to trigger all processes at once
        self.start_event = multiprocessing.Event()

        
        self.audio_process = multiprocessing.Process(
            target=self.audio.record, args=(name, seconds, self.start_event)
        )

        self.realsense_process = multiprocessing.Process(
            target=self.realsense.captureImages,
            args=(name, seconds, self.start_event),
        )

        self.thermal_process = multiprocessing.Process(
            target=self.thermal.captureImages,
            args=(name, seconds, True, self.start_event),
        )

        #  RGB
        # self.rgb_process = multiprocessing.Process(
            # target=self.rgb.captureImages,
            # args=(name, seconds, self.show_rgb, self.start_event,),
            # kwargs=({"process_type": "streamcam"})
        # )

        self.hires_process = multiprocessing.Process(
            target=self.hires.captureImages,
            args=(name, seconds, self.show_rgb, self.start_event,),
            kwargs=({"process_type": "brio"})
        )

        
    def capture(self):
        process_list = [
            self.thermal_process,
            self.realsense_process,
            self.audio_process,
            self.hires_process,
            # self.rgb_process,
        ]

        try:
            for process in process_list:
                process.start()

            # Warmup time
            time.sleep(CaptureData.WARMUP_TIME)
            print("Starting capture...")

            self.start_event.set()

        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                print(
                    "Keyboard Interrupt detected, stopping recording...[capture_data.py]"
                )

            else:
                print("An error occured:", e)

        # finally:
            # for process in process_list:
                # process.join()
                # if process.exitcode == 0:
                    # print(f"Process {process.name} exited successfully.")
                # else:
                    # if process.exitcode != None:
                        # print(
                            # f"Process {process.name} exited with exit code {process.exitcode}"
                        # )

            # time.sleep(3)

            # print("All processes finished. Recording stopped and saved")
            exit()

if __name__ == "__main__":
    print("Run capture_data.py -h for usage tips.")

    args = parser.parse_args()

    save_pid("capture_data.pid")

    with open("installers/data_capture/hardware_config.json", "r") as fp:
        hw_config = json.load(fp)

        capture = CaptureData(seconds=args.duration, filename=args.name)
        capture.capture()
