import argparse
import errno
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
        type=str, default=None,
        help="output folder"
    )
    parser.add_argument(
        "-n", "--data_name",
        type=str, default=None,
        help="dataset name"
    )
    parser.add_argument(
        "-x", "--data_suffix",
        type=str, default=None,
        help="dataset suffix"
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
    parser.add_argument(
        "-s", "--snr_db",
        type=int, default=None,
        help="desired SNR in decibels for generated audio"
    )
    args = parser.parse_args()

    # increment data_name if necessary
    data_name = args.data_name or f"{time.strftime('%y%m%d')}"
    if args.data_suffix is None:
        i = 1
        while os.path.exists(os.path.normpath(
            make_abs_path(WC_DIR, f"{RAW_DATA_PATH}/{data_name}")
        )):
            data_name = f"{time.strftime('%y%m%d')}_{i}"
            i += 1

    # define paths and create data directory
    if args.data_suffix is not None:
        data_name = f"{data_name}{args.data_suffix}"

    outdir = args.outdir
    if outdir is None:
        outdir = make_abs_path(WC_DIR, f"{RAW_DATA_PATH}/{data_name}")
    outdir = os.path.normpath(outdir)
    try:
        os.makedirs(outdir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        raise ValueError("Supplied data name clashes with existing dataset.")

    outfile = f"{os.path.basename(outdir)}.wav"

    # record audio data using WatchCalibration class
    wc = WatchCalibration(fs=args.rate)
    wc.save_audio_to_file(
        args.duration,
        outdir=outdir,
        outfile=outfile,
        input_device=args.input_device,
        generate=args.generate,
        snr_db=args.snr_db
    )


    # read in metadata template, assign variables, and write out to data folder
    with open(METADATA_TEMPLATE, "r") as f:
        metadata = yaml.safe_load(f)

    metadata["dataset"] = data_name
    metadata["sampling_rate"] = args.rate
    metadata["duration"] = args.duration

    with open(f"{outdir}/{data_name}.yaml", "w") as f:
        yaml.dump(metadata, f)

    # Print out data directory and file names for trusted timestamping scripts
    print(outdir)
    print(data_name)
