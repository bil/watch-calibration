""" WatchCalibration Class """
import copy
import csv
import os

from bokeh.plotting import figure, output_file, save
import librosa
import matplotlib
# matplotlib.rcParams['figure.subplot.top'] = 1   # Extend plot to top of figure
from matplotlib import pyplot as plt
import numpy as np
import scipy as sp
from scipy import signal as sps
import soundfile as sf
from scipy.io.wavfile import write

try:
    import sounddevice as sd
    SND_DEFINED = True
except:
    SND_DEFINED = False

# default working directory to the watch-calibration top-level directory
WC_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

# use absolute paths if set or create absolute path from parent directory
if os.path.isabs(os.environ["ARTS_RAW_DATA_PATH"]):
    RAW_DATA_PATH = os.environ["ARTS_RAW_DATA_PATH"]
else:
    RAW_DATA_PATH = os.path.join(WC_DIR, os.environ["ARTS_RAW_DATA_PATH"])

if os.path.isabs(os.environ["ARTS_DERIV_DATA_PATH"]):
    DERIV_DATA_PATH = os.environ["ARTS_DERIV_DATA_PATH"]
else:
    DERIV_DATA_PATH = os.path.join(WC_DIR, os.environ["ARTS_DERIV_DATA_PATH"])
DEFAULT_AUDIO = os.path.join(RAW_DATA_PATH, "data_W241130_W241130.wav")
# grab experiment
WINDOW_LEN = int(os.environ.get("WC_WINDOW_LEN") or 1000)
PEAK_PROMINENCE = float(os.environ.get("WC_PEAK_PROMINENCE") or 0.001)
F_FUND = float(os.environ.get("WC_F_FUND") or 6.)

class WatchCalibration:
    """ WatchCalibration class  """

    def __init__(self, fs=44100, audio_file=None):
        """ Initialize WatchCalibration. """

        # constants
        self.fs = fs
        if audio_file is None:
            self.audio_file = DEFAULT_AUDIO
        else:
            self.audio_file = audio_file
        self.window_len = WINDOW_LEN
        self.peak_prominence = PEAK_PROMINENCE
        self.f_fund = F_FUND

        # derivative data
        self.audio_len = None
        self.audio_wins = None
        self.peaks = None

        # calculated from stft
        self.freq_band = None


    ## Class Functions ########################################################

    @classmethod
    def query_devices(self):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        print(sd.query_devices())


    def save_audio_to_file(
        self, duration, outfile="output.wav", input_device=None, generate=False
    ):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        if generate:
            # generate with librosa
            recording = librosa.clicks(
                times=np.arange(duration, step=1./self.f_fund),
                sr=self.fs, length=self.fs*duration, click_duration=0.01
            )
        else:
            # record from audio interface
            recording = sd.rec(int(duration * self.fs), samplerate=self.fs, channels=1, device=input_device)

        sd.wait()  # Wait until recording is finished
        write(outfile, self.fs, recording)  # Save as WAV file


    def play_audio(self, filename, output_device=sd.default.device):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        # Extract data and sampling rate from file
        data, fs = sf.read(filename, dtype='float32')
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
        plt.fill_between(peaks, np.min(A), np.max(A), alpha=0.7,zorder=10)
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
            audio_wins.append(audio[p-self.window_len//2:p+self.window_len//2])

        self.audio_len = len(audio)
        self.audio_wins = audio_wins
        self.peaks = peaks
        return audio


    def save_deriv_data(
        self, deriv_data_path=DERIV_DATA_PATH
    ):
        # save audio windows and onset times to file

        if self.audio_wins is None or self.peaks is None:
            raise ValueError("Run create_deriv_from_raw function first")

        # save derivative data
        np.save(f"{deriv_data_path}/audio_len.npy", self.audio_len)
        np.save(f"{deriv_data_path}/audio.npy", self.audio_wins)
        np.save(f"{deriv_data_path}/peaks.npy", self.peaks)


    def view_correlations(
        self, raw_audio=None, filter=False, shift=False,
        envelope=False, plot_wins=False
    ):
        # TODO do this with derivative data?
        #self.load_deriv_data()
        # onset_times = self.peaks / self.fs
        # diffs = np.diff(onset_times)

        if raw_audio is None:
            raw_audio, _ = self.load_audio()

        audio = self.trim_audio(raw_audio)

        audio, peaks, onset_times = self.find_peaks(audio, filter=filter)

        if shift or envelope:
            peaks = self.shift_peaks(
                audio, peaks, envelope=envelope
            )

        onset_times = peaks / self.fs
        diffs = np.diff(onset_times)

        plt.figure()
        plt.hist(diffs, bins="auto")
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
            for i, peak in enumerate(peaks):
                win_start = peak - self.window_len//2
                win_end = peak + self.window_len//2
                # if shift or envelope:
                #     win_start = peaks[i] - self.window_len//2
                #     win_end = peaks[i] + self.window_len//2
                win = audio[win_start:win_end]

                ax = axs[i%num_fig_rows][i//num_fig_rows]
                ax.axes.get_xaxis().set_visible(False)
                ax.axes.get_yaxis().set_visible(False)

                ax.plot(win)
                ax.plot(peak-win_start, audio[peak], "x", color="orange")
                ax.vlines(
                    peaks[i]-win_start,
                    np.min(win), np.max(win),
                    color='r', alpha=0.8
                )

        return fig

    def perform_analysis(self, deriv_data_path=DERIV_DATA_PATH, envelope=False, filter=False, shift=False, output=True):
        self.load_deriv_data()

        raw_audio, _ = self.load_audio()
        print(raw_audio)
        print(len(raw_audio))

        audio = self.trim_audio(raw_audio)

        audio, peaks, onset_times = self.find_peaks(audio, filter=filter)
        print(peaks)
        if shift or envelope:
            peaks = self.shift_peaks(
                audio, peaks, envelope=envelope
            )

        onset_times = peaks / self.fs

        # remove first and last onset times
        onset_times = onset_times[1:-1]
        diffs = np.diff(onset_times)

        audio_dur = self.audio_len / self.fs

        actual_last_click_time = onset_times[-1]
        ideal_last_click_time = (
            onset_times[0] + (len(onset_times) - 1) * 1./self.f_fund
        )

        drift = ideal_last_click_time - actual_last_click_time
        drift_per_s = drift / audio_dur

        drift_per_s = np.mean(diffs) * self.f_fund - 1.

        if not output:
            return drift_per_s

        print(f"first tick time: {onset_times[0]:.4f} s")
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


    def generate_figures(self, audio=None):
        if audio is None:
            audio, _ = self.load_audio()

        # create figures
        fig = plt.figure(figsize=(8,2))
        fig.canvas.header_visible = False
        plt.plot(audio)
        plt.axis('off')
        plt.gca().set_position([0, 0, 1, 1])
        plt.savefig("fig1.svg")

        # create HTML bokeh page
        p = figure(title="Basic Title")#, plot_width=300, plot_height=300)
        p.circle([1, 2], [3, 4])
        output_file("fig1.html")
        save(p)


    ## Class Utilities ########################################################

    def _normalize(self, x):
        return (x - np.mean(x)) / np.max(x)

    def _corr_wins(self, w1, w2):
        corr = sps.correlate(w1, w2, mode="full")
        shift_amt = np.argmax(corr) - len(corr) // 2
        return shift_amt

    def calculate_freq_band(self, audio):
        A = np.abs(sp.fft.fft(audio))[:self.fs//2]
        peaks = sps.find_peaks(
            A, height=np.mean(A)*8, distance=self.fs//400
        )[0]
        self.freq_band = (peaks[0], peaks[-1])
        return A, peaks

    def trim_audio(self, audio):
        # throw out first and last ticks
        win_size = int(self.fs/self.f_fund)
        return audio[win_size:-win_size]

    def filter_audio(self, audio, freq_band=None):
        if freq_band is None:
            if self.freq_band is None:
                _, peaks = self.calculate_freq_band(audio)
            freq_band = self.freq_band

        b, a = sps.butter(6, freq_band, btype="bandpass", fs = self.fs)

        return sps.filtfilt(b, a, audio)

    def calculate_envelope(self, x):
        filtered = self.filter_audio(x)
        z_env, z_res = sps.envelope(filtered)

        return filtered, z_env

    def find_peaks(self, audio, filter=False):
        distance = int(self.fs/self.f_fund*.9)

        if filter:
            audio = self.filter_audio(audio)

        peaks = sps.find_peaks(
            audio,
            distance=distance,
            prominence=.001,#self.peak_prominence,
            wlen=distance
        )[0]

        # throw out first and last peaks
        onset_times = peaks / self.fs

        return audio, peaks, onset_times

    def shift_peaks(self, audio, peaks, envelope=False):
        if envelope:
            _, env = self.calculate_envelope(audio)

        shifted_peaks = copy.copy(peaks)
        for i in range(len(peaks)-1):
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


    def pad_wins(self, w1, w2, shift_amt):
        if shift_amt > 0:
            w1 = np.pad(w1, (0,shift_amt//2))
            w2 = np.pad(w2, (shift_amt//2,0))
        else:
            w2 = np.pad(w2, (0,-shift_amt//2))
            w1 = np.pad(w1, (-shift_amt//2,0))

        return w1, w2

    def plot_wins(self, w1, w2, shift_amt=0, title=None):
        fig = plt.figure(figsize=(8,2))
        fig.canvas.header_visible = False

        w1, w2 = self.pad_wins(w1, w2, shift_amt)
        plt.plot(w1)
        plt.plot(w2)

        if title:
            plt.title(title)

        plt.show()



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
