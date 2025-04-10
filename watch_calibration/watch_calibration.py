""" WatchCalibration Class """
import copy
import csv
import os
import yaml

import librosa
import matplotlib
import numpy as np
import scipy as sp
import soundfile as sf

from matplotlib import pyplot as plt
from scipy import signal as sps
from scipy.io.wavfile import write

from .util import make_abs_path

try:
    import sounddevice as sd
    SND_DEFINED = True
except:
    SND_DEFINED = False


# default working directory to the watch-calibration top-level directory
WC_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
# use absolute paths if set or create absolute path from parent directory
RAW_DATA_PATH = make_abs_path(WC_DIR, os.environ["ARTS_RAW_DATA_PATH"])
DERIV_DATA_PATH = make_abs_path(WC_DIR, os.environ["ARTS_DERIV_DATA_PATH"])
OUTPUT_PATH = make_abs_path(WC_DIR, os.environ["ARTS_OUTPUT_PATH"])
DEFAULT_DATA_NAME = "W241130"
DEFAULT_AUDIO = os.path.join(
    RAW_DATA_PATH, f"{DEFAULT_DATA_NAME}/{DEFAULT_DATA_NAME}.wav"
)

# filtering variables
FREQ_BAND_MAX = 15000
DEFAULT_FREQ_BAND = (6000, 8500)
FILT_PROM_DIV = 70

# data generation variables
CLICK_FREQ = 7000
CLICK_DUR = 0.01

# load experiment environment variables
WINDOW_LEN = int(os.environ.get("WC_WINDOW_LEN") or 2000)
PEAK_PROMINENCE = float(os.environ.get("WC_PEAK_PROMINENCE") or 0.001)
F_FUND = float(os.environ.get("WC_F_FUND") or 6.)


class WatchCalibration:
    """ WatchCalibration class  """

    def __init__(self, data_name=None, fs=None):
        """
        Create WatchCalibration experiment instance for mechanical watch
        movement calibration. Default values are populated from constants
        defined above and associated metadata file.

        Args:
            data_name (str): dataset name for current experiment
            fs (int): sampling rate (Hz)
        """

        # constants
        if data_name is None:
            self.data_name = DEFAULT_DATA_NAME
            self.audio_file = DEFAULT_AUDIO
            self.metadata =  self.load_metadata(DEFAULT_DATA_NAME)
        else:
            self.data_name = data_name
            self.audio_file = os.path.join(
                RAW_DATA_PATH, f"{data_name}/{data_name}.wav"
            )
            self.metadata = self.load_metadata(data_name)
        self.fs = fs or self.metadata.get("sampling_rate")
        self.window_len = WINDOW_LEN
        self.peak_prominence = PEAK_PROMINENCE  # prominence used for find_peaks
        self.f_fund = F_FUND   # fundamental watch movement frequency

        # derivative data
        self.audio_len = None  # length in samples
        self.audio_wins = None # windows around peaks
        self.peaks = None      # peaks computed from find_peaks

        # calculated from stft or set to default
        self.freq_band = None


    ## Class Methods ###########################################################

    @classmethod
    def query_devices(cls):
        """Print audio devices available to sounddevice library."""

        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        print(sd.query_devices())


    @classmethod
    def load_metadata(cls, data_name):
        """Load metadata YAML file from RAW_DATA_PATH.

        Args:
            data_name (str): dataset name (used for metadata filename too)

        Returns:
            metadata (dict): dict representation of metadata YAML file
        """

        metadata_file = os.path.join(
            RAW_DATA_PATH, f"{data_name}/{data_name}.yaml"
        )
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f.read())

        return metadata


    ## Instance Methods ########################################################

    def generate_audio(self, duration, snr_db=None):

        x = librosa.clicks(
            times=np.arange(duration, step=1./self.f_fund),
            sr=self.fs, length=self.fs*duration,
            click_freq=CLICK_FREQ, click_duration=CLICK_DUR
        )

        if snr_db is not None:
            x_pwr = x ** 2
            x_avg_pwr = np.mean(x_pwr)
            x_avg_db = 10 * np.log10(x_avg_pwr)
            n_avg_db = x_avg_db - snr_db
            n_avg_pwr = 10 ** (n_avg_db / 10)
            n_mean = 0
            n = np.random.normal(n_mean, np.sqrt(n_avg_pwr), len(x))
            x = x + n

        return x

    def save_audio_to_file(
        self, duration,
        outdir=".", outfile="output.wav", input_device=None,
        generate=False, snr_db=None
    ):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        if generate:
            # generate with librosa
            recording = self.generate_audio(duration, snr_db=snr_db)
        else:
            # record from audio interface
            recording = sd.rec(
                int(duration * self.fs),
                samplerate=self.fs, channels=1, device=input_device
            )
            sd.wait()

        # write audio to file
        write(os.path.join(outdir, outfile), self.fs, recording)


    def play_audio(self, data, fs, output_device=sd.default.device):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        sd.play(data, fs, device=output_device)
        status = sd.wait()  # Wait until file is done playing


    # TODO change filename to archive loc and support s3 pulls?
    def load_audio(self, filename=None):
        if filename is None:
            filename = self.audio_file
        return librosa.load(filename, sr=self.fs)


    def plot_audio(self, audio, plt_secs=None):
        if plt_secs:
            audio_win = audio[-self.fs*plt_secs:]

        fig = plt.figure(figsize=(8,2))
        fig.canvas.header_visible = False
        plt.plot(audio_win)
        plt.ylim(np.min(audio_win), np.max(audio_win))
        plt.xlabel("time (samples)")
        plt.title("Audio signal")
        plt.show()

        fig = plt.figure(figsize=(8,2))
        fig.canvas.header_visible = False
        A, peaks = self.calculate_freq_band(audio)
        plt.plot(A, zorder=1)
        plt.fill_between(
            self.freq_band, np.min(A), np.max(A), alpha=0.7,zorder=10
        )
        plt.xlabel("frequency (Hz)")
        plt.ylabel("power")
        plt.title(f"FFT and frequency band of interest (Hz)")
        plt.show()

        # spectral
        fig = plt.figure(figsize=(8,2))
        fig.canvas.header_visible = False
        D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_win)), ref=np.max)
        librosa.display.specshow(D)
        plt.xlabel("time")
        plt.ylabel("frequency")
        plt.title("Spectrogram")


    def create_deriv_from_raw(self, raw_audio=None, filter=False):
        if raw_audio is None:
            raw_audio, _ = self.load_audio()

        audio = self.trim_audio(raw_audio)
        audio, peaks, _ = self.find_peaks(audio, filter=filter)

        # create audio windows
        audio_wins = []
        for p in peaks:
            start = p - self.window_len // 2
            end = p + self.window_len // 2
            if start > 0 and end < len(audio):
                audio_wins.append(
                    audio[p-self.window_len//2:p+self.window_len//2]
                )

        self.audio_len = len(audio)
        self.audio_wins = audio_wins
        self.peaks = peaks
        return audio


    def save_deriv_data(
        self, deriv_data_path=DERIV_DATA_PATH,
    ):
        # save audio windows and onset times to file
        if self.audio_wins is None or self.peaks is None:
            raise ValueError("Run create_deriv_from_raw function first")

        # save derivative data
        os.makedirs(
            os.path.join(deriv_data_path, self.data_name), exist_ok=True
        )
        np.save(
            os.path.join(deriv_data_path, self.data_name, "audio_len.npy"),
            self.audio_len
        )
        np.save(
            os.path.join(deriv_data_path, self.data_name, "audio.npy"),
            self.audio_wins
        )
        np.save(
            os.path.join(deriv_data_path, self.data_name, "peaks.npy"),
            self.peaks
        )


    def view_correlations(
        self, raw_audio=None, filter=False, shift=False,
        envelope=False, plot_wins=False
    ):

        audio, peaks, peak_times, diffs = _get_anaylsis_vars(
            raw_audio=raw_audio
        )

        fig = plt.figure()
        fig.canvas.header_visible = False
        plt.hist(diffs, bins=20)
        plt.title(f"Tick time diffs (Mean: {np.mean(diffs):.5f}; StdDev: {np.std(diffs):.5f})")
        plt.xlabel("time (s)")
        plt.ylabel("occurrences")
        plt.show()

        if not plot_wins:
            return

        num_fig_cols = 10
        num_fig_rows = len(peaks)//num_fig_cols+1
        with plt.ioff():
            fig, axs = plt.subplots(num_fig_rows, num_fig_cols, squeeze=False)
            fig.set_figheight(15)
            fig.set_figwidth(15)
            for i, peak in enumerate(peaks[1:-1]):
                win_start = peak - self.window_len//2
                win_end = peak + self.window_len//2
                win = audio[win_start:win_end]
                if len(win) == 0: continue

                ax = axs[i%num_fig_rows][i//num_fig_rows]
                ax.axes.get_xaxis().set_visible(False)
                ax.axes.get_yaxis().set_visible(False)

                ax.plot(win)
                ax.plot(peak-win_start, audio[peak], "x", color="orange")
                ax.vlines(
                    peaks[i+1]-win_start,
                    np.min(win), np.max(win),
                    color="r", alpha=0.8
                )

        return fig

    def perform_analysis(
        self, deriv_data_path=DERIV_DATA_PATH,
        envelope=False, filter=False, shift=False, output=True
    ):

        audio, peaks, peak_times, diffs = self._get_anaylsis_vars(
            raw_audio=raw_audio
        )

        audio_dur = len(audio) / self.fs

        actual_last_click_time = peak_times[-1]
        ideal_last_click_time = (
            peak_times[0] + (len(peak_times) - 1) * 1./self.f_fund
        )
        drift_per_s = np.mean(diffs) * self.f_fund - 1.

        if not output:
            return drift_per_s

        print(f"first tick time: {peak_times[0]:.4f} s")
        print(f"actual last tick time: {actual_last_click_time:.4f}")
        print(f"ideal last tick time: {ideal_last_click_time:.4f}")

        # print drift values over various durations
        SEC_IN_MIN = 60
        SEC_IN_HOUR = SEC_IN_MIN * 60
        SEC_IN_DAY = SEC_IN_HOUR * 24
        SEC_IN_WEEK = SEC_IN_DAY * 7
        SEC_IN_MONTH = SEC_IN_DAY * 30
        SEC_IN_YEAR =  SEC_IN_DAY * 365
        self.print_drift_over_time(
            drift_per_s, SEC_IN_MIN, "minute", format_string="%0.5f"
        )
        self.print_drift_over_time(drift_per_s, SEC_IN_HOUR, "hour")
        self.print_drift_over_time(drift_per_s, SEC_IN_DAY, "day")
        self.print_drift_over_time(drift_per_s, SEC_IN_WEEK, "week")
        self.print_drift_over_time(drift_per_s, SEC_IN_MONTH, "month (30 days)")
        self.print_drift_over_time(drift_per_s, SEC_IN_YEAR, "year (365 days)")

        return drift_per_s


    ## Class Utilities ########################################################

    def _get_anaylsis_vars(self, raw_audio=None):
        # TODO use only derivative data
        # self.create_deriv_from_raw(raw_audio, filter=filter)
        # self.load_deriv_data()

        if raw_audio is None:
            raw_audio, _ = self.load_audio()

        audio = self.trim_audio(raw_audio)

        audio, peaks, peak_times = self.find_peaks(audio, filter=filter)

        if shift or envelope:
            peaks = self.shift_peaks(
                audio, peaks, envelope=envelope
            )

        # remove first and last peaks
        peaks = peaks[1:-1]
        peak_times = peaks / self.fs
        diffs = np.diff(peak_times)

        return audio, peaks, peak_times, diffs

    def _normalize(self, x):
        return (x - np.mean(x)) / np.max(x)

    def _corr_wins(self, w1, w2):
        corr = sps.correlate(w1, w2, mode="full")
        shift_amt = np.argmax(corr) - len(corr) // 2
        return shift_amt

    def calculate_freq_band(self, audio):
        A = np.abs(sp.fft.fft(audio))[:FREQ_BAND_MAX]
        peaks = sps.find_peaks(
            A, height=np.mean(A)*8, distance=self.fs//400
        )[0]
        if len(peaks) < 3: # high SNR
            self.freq_band = DEFAULT_FREQ_BAND # use default freq_band
        else:
            self.freq_band = (peaks[0], peaks[-1])

        return A, peaks

    def trim_audio(self, audio, start=None, end=None):
        # throw out first and last ticks
        win_size = int(self.fs/self.f_fund)
        if not start:
            start = win_size
        if not end:
            end = -win_size
        return audio[start:end]

    def filter_audio(self, audio, freq_band=None, order=6):
        if freq_band is None:
            if self.freq_band is None:
                _, peaks = self.calculate_freq_band(audio)
            freq_band = self.freq_band

        b, a = sps.butter(order, freq_band, btype="bandpass", fs = self.fs)

        return sps.filtfilt(b, a, audio)

    def calculate_envelope(self, x):
        filtered = self.filter_audio(x)
        z_env, z_res = sps.envelope(filtered)

        return filtered, z_env

    def find_peaks(self, audio, filter=False):
        distance = int(self.fs/self.f_fund*.9)

        if filter:
            audio = self.filter_audio(audio)

        prominence = self.peak_prominence
        if filter:
            prominence = self.peak_prominence / FILT_PROM_DIV

        peaks = sps.find_peaks(
            audio,
            distance=distance,
            prominence=prominence,
            wlen=distance
        )[0]

        # throw out first and last peaks
        peak_times = peaks / self.fs

        return audio, peaks, peak_times

    def shift_peaks(self, audio, peaks, envelope=False):
        if envelope:
            _, env = self.calculate_envelope(audio)

        shifted_peaks = copy.copy(peaks)
        for i in range(1, len(peaks)-1):
            win1_start = peaks[i]-self.window_len//2
            if win1_start < 0:
                win1_start = 0
            win1_end = peaks[i]+self.window_len//2 + 1
            if win1_end > len(audio):
                win1_end = len(audio)
            win1 = self._normalize(audio[win1_start:win1_end])

            win2_start = peaks[i+1]-self.window_len//2
            if win2_start < 0:
                win2_start = 0
            win2_end = peaks[i+1]+self.window_len//2
            if win2_end > len(audio):
                win2_end = len(audio)
            win2 = self._normalize(audio[win2_start:win2_end])

            if envelope:
                win1 = self._normalize(env[win1_start:win1_end])
                win2 = self._normalize(env[win2_start:win2_end])

            shift_amt = self._corr_wins(win1, win2)
            if i+1 < len(shifted_peaks):
                shifted_peaks[i+1] -= shift_amt

        return shifted_peaks


    def print_drift_over_time(
            self, drift_per_sec, seconds, dur_string, format_string = "%0.2f"
        ):
            drift = drift_per_sec * seconds
            units = "s"
            if abs(drift) > 60:
                drift /= 60.
                units = "m"
            x = ".2f"
            print(f"{format_string} {units} drift in a {dur_string}" % drift)


    def load_deriv_data(self, deriv_data_path=DERIV_DATA_PATH):
        if self.audio_len is None:
            self.audio_len = np.load(f"{deriv_data_path}/audio_len.npy")

        if self.audio_wins is None:
            self.audio_wins = np.load(f"{deriv_data_path}/audio.npy")

        if self.peaks is None:
            self.peaks = np.load(f"{deriv_data_path}/peaks.npy")
