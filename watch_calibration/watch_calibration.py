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

PWD = os.path.realpath(os.path.dirname(__file__))
DEFAULT_AUDIO = os.path.join(PWD, "..", os.environ["ARTS_RAW_DATA_PATH"], "data_W241130_W241130.wav")
FREQ_GUESS = 6.
WINDOW_LEN = 2000
PEAK_PROMINENCE = 0.003

class WatchCalibration:
    """ WatchCalibration class  """

    def __init__(self, fs=44100):
        """ Initialize Watch-Calibration. """

        self.fs = fs
        self.freq_quess = FREQ_GUESS
        self.window_len = WINDOW_LEN
        self.peak_prominence = PEAK_PROMINENCE
        self.freq_band = None

    def __repr__(self):
        """ Return Watch-Calibration name. """

        return self.__class__.__name__

    ## Class Utilities ########################################################

    # TODO
    # https://stackoverflow.com/questions/41492882/find-time-shift-of-two-signals-using-cross-correlation
    def _corr_wins(self, w1, w2):
        corr = sps.correlate(w1, w2)
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
        win_size = int(self.fs/self.freq_quess)
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
        distance = int(self.fs/self.freq_quess*.9)

        if filter:
            audio = self.filter_audio(audio)

        peaks = sps.find_peaks(
            audio,
            distance=distance,
            prominence=self.peak_prominence,
            wlen=distance
        )[0]

        # throw out first and last peaks
        peaks = peaks[1:-1]
        onset_times = peaks / self.fs

        return audio, peaks, onset_times

    def shift_peaks(self, audio, peaks, hilbert=False, envelope=False):
        if envelope:
            _, env = self.calculate_envelope(audio)

        shift_amt = 0
        shifted_peaks = copy.copy(peaks)
        for i in range(len(peaks)-1):
            win1_start = peaks[i]-self.window_len//2
            if win1_start < 0:
                win1_start = 0
            win1_end = peaks[i]+self.window_len//2 + 1
            if win1_end > len(audio):
                win1_end = len(audio)
            win1 = audio[win1_start:win1_end]

            win2_start = peaks[i+1]-self.window_len//2
            if win2_start < 0:
                win2_start = 0
            win2_end = peaks[i+1]+self.window_len//2
            if win2_end > len(audio):
                win2_end = len(audio)
            win2 = audio[win2_start:win2_end]

            if hilbert:
                win1 = sps.hilbert(win1)
                win1 = sps.hilbert(win2)

            if envelope:
                win1 = env[win1_start:win1_end]
                win2 = env[win2_start:win2_end]

            shift_amt += self._corr_wins(win1, win2)
            if i+1 < len(shifted_peaks):
                shifted_peaks[i+1] -= shift_amt

        return shifted_peaks


    ## Class Functions ########################################################

    def query_devices(self):
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        print(sd.query_devices())


    def save_audio_to_file(
        self, duration, outfile="output.wav", input_device=None, generate=False
    ):
        print(input_device)
        if not SND_DEFINED:
            print("sounddevice library could not be loaded.")
            return

        if generate:
            # generate with librosa
            recording = librosa.clicks(
                times=np.arange(duration, step=1./FREQ_GUESS),
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
    def load_audio(self, filename=DEFAULT_AUDIO):
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


    def perform_analysis(self, audio, filter=False, raw_audio=None):
        if raw_audio is None:
            raw_audio, _ = self.load_audio()

        audio = self.trim_audio(raw_audio)
        audio, peaks, onset_times = self.find_peaks(audio, filter=filter)

        diffs = np.diff(onset_times)

        audio_dur = len(audio) / self.fs
        f_fund = 6

        actual_last_click_time = onset_times[-1]
        ideal_last_click_time = (
            onset_times[0] + (len(onset_times) - 1) * 1./f_fund
        )

        drift = ideal_last_click_time - actual_last_click_time
        drift_per_sec = drift / audio_dur

        print(f"first click time: {onset_times[0]:.4f} s")
        print(f"actual last click time: {actual_last_click_time:.4f}")
        print(f"ideal last click time: {ideal_last_click_time:.4f}")

        def print_drift_over_time(
            drift_per_sec, seconds, dur_string, format_string = "%0.2f"
        ):
            drift = drift_per_sec * seconds
            units = "s"
            if abs(drift) > 60:
                drift /= 60.
                units = "m"
            x = ".2f"
            print(f"{format_string} {units} drift in a {dur_string}" % drift)

        # minute
        SEC_IN_MIN = 60
        print_drift_over_time(
            drift_per_sec, SEC_IN_MIN, "minute", format_string="%0.5f"
        )

        # day
        SEC_IN_DAY = 86400
        print_drift_over_time(drift_per_sec, SEC_IN_DAY, "day")

        # week
        SEC_IN_WEEK = SEC_IN_DAY * 7
        print_drift_over_time(drift_per_sec, SEC_IN_WEEK, "week")
        # month
        SEC_IN_MONTH = SEC_IN_DAY * 30
        print_drift_over_time(drift_per_sec, SEC_IN_MONTH, "month (30 days)")

        # year
        SEC_IN_YEAR =  SEC_IN_DAY * 365
        print_drift_over_time(drift_per_sec, SEC_IN_YEAR, "year (365 days)")


    def view_correlations(
        self, raw_audio=None, shift=False, hilbert=False, envelope=False
    ):
        if raw_audio is None:
            raw_audio, _ = self.load_audio()

        if hilbert and envelope:
            raise ValueError("Set only hilbert or envelope.")

        audio = self.trim_audio(raw_audio)
        audio, peaks, onset_times = self.find_peaks(audio, filter=envelope)

        if shift:
            peaks = self.shift_peaks(peaks, env, hilbert=hilbert, envelope=envelope)

        num_fig_cols = 10
        num_fig_rows = len(peaks)//num_fig_cols+1
        with plt.ioff():
            fig, axs = plt.subplots(num_fig_rows, num_fig_cols, squeeze=False)
            fig.set_figheight(15)
            fig.set_figwidth(15)
            for i, peak in enumerate(peaks):
                win_start = peak - WINDOW_LEN//2
                win_end = peak + WINDOW_LEN//2
                if shift or hilbert or envelope:
                    win_start = peaks[i] - WINDOW_LEN//2
                    win_end = peaks[i] + WINDOW_LEN//2
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
                # break

        return fig


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

