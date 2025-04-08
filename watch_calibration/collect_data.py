import argparse
import os
import sys
import time
import yaml
from watch_calibration import WatchCalibration, WC_DIR, make_abs_path

RECORDING_DURATION = int(os.environ.get("WC_RECORDING_DURATION") or 60)
SAMPLING_RATE = int(os.environ.get("WC_SAMPLING_RATE") or 44100)
RAW_DATA_PATH = make_abs_path(
    WC_DIR, os.environ.get("ARTS_RAW_DATA_PATH") or "."
)
METADATA_TEMPLATE = f"{RAW_DATA_PATH}/metadata.yaml"
DATA_NAME = f"{time.strftime('%y%m%d')}"
DATA_FOLDER = make_abs_path(WC_DIR, f"{RAW_DATA_PATH}/{DATA_NAME}")
i = 1
while os.path.exists(os.path.normpath(DATA_FOLDER)):
    DATA_NAME = f"{time.strftime('%y%m%d')}_{i}"
    DATA_FOLDER = make_abs_path(WC_DIR, f"{RAW_DATA_PATH}/{DATA_NAME}")
    i += 1
# set data path variables in environment for trusted timestamping
os.environ["WC_DATA_NAME"] = DATA_NAME
os.environ["WC_DATA_FOLDER"] = DATA_FOLDER

def query_devices():
    """Print system audio devices for input and output."""

    wc = WatchCalibration()
    wc.query_devices()


def collect_data():
    """Collect data
        Can be called via CLI with wc-collect-data

    """

    # parse user input to define recording variables
    parser = argparse.ArgumentParser(
        prog="wc-collect-data",
        description="Watch Calibration data collection helper script"
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=RECORDING_DURATION,
        help="recording duration",
    )
    parser.add_argument(
        "-r", "--rate", type=int, default=SAMPLING_RATE,
        help="sampling rate",
    )
    parser.add_argument(
        "-o", "--outdir",
        type=str, default=DATA_FOLDER,
        help="output folder"
    )
    parser.add_argument(
        "-f", "--filename",
        type=str, default=DATA_NAME,
        help="output folder"
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

    # define paths and create data directory
    outdir = make_abs_path(WC_DIR, args.outdir)
    outfile = f"{os.path.basename(os.path.normpath(args.outdir))}.wav"
    os.makedirs(outdir)

    # record audio data using WatchCalibration class
    wc = WatchCalibration(fs=args.rate)
    wc.save_audio_to_file(
        args.duration,
        outdir=outdir,
        outfile=f"{os.path.basename(os.path.normpath(args.outdir))}.wav",
        input_device=args.input_device,
        generate=args.generate
    )


    # read in metadata template, assign variables, and write out to data folder
    with open(METADATA_TEMPLATE, "r") as f:
        metadata = yaml.safe_load(f)

    metadata["dataset"] = DATA_NAME
    metadata["sampling_rate"] = args.rate
    metadata["duration"] = args.duration

    with open(f"{DATA_FOLDER}/{DATA_NAME}.yaml", "w") as f:
        yaml.dump(metadata, f)

    # Print out data directory and file names for trusted timestamping scripts
    print(outdir)
    print(DATA_NAME)
