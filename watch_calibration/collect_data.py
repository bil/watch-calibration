import sys
import argparse
from .watch_calibration import WatchCalibration

def collect_data():
    parser = argparse.ArgumentParser(
        prog="wc-collect-data",
        description="Watch Calibration data collection helper script"
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=60,
        help="recording duration",
    )
    parser.add_argument(
        "-o", "--outfile",
        type=str, default="output.wav",
        help="output filename"
    )
    parser.add_argument(
        "-i", "--input_device",
        type=int, default=None,
        help="input device number for sounddevice"
    )
    parser.add_argument(
        "-g", "--generate",
        action="store_true",
        help="set flag to generate watch using librosa"
    )
    args = parser.parse_args()

    wc = WatchCalibration()
    wc.save_audio_to_file(
        args.duration,
        outfile=args.outfile,
        input_device=args.input_device,
        generate=args.generate
    )
    print("COLLECT DATA!")
