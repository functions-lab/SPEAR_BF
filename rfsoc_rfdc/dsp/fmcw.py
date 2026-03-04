"""FMCW implementation with signal generation and analysis capabilities."""

import matplotlib.pyplot as plt
import numpy as np


class FMCW:
    """Implements FMCW functionality."""

    def __init__(self, freq_low=-0.4, freq_high=0.40, chirp_len=10000, chirp_num=1, duration=10000):
        """Initializes the FMCW object with given parameters.

        Args:
            freq_low (float): Start frequency of the chirp (normalized to sample rate).
            freq_high (float): End frequency of the chirp (normalized to sample rate).
            chirp_len (int): Number of samples in the active chirp.
            chirp_num (int): Number of chirps to generate.
            duration (int): Total duration of one chirp period (including silence/gap).
        """
        np.random.seed(0)  # Fix random seed

        self.freq_low = freq_low
        self.freq_high = freq_high
        self.chirp_len = chirp_len
        self.chirp_num = chirp_num
        self.duration = duration

    def generate(self, amp=1.0):
        """Generates FMCW signal.

        Args:
            amp (float): Amplitude of the signal.

        Returns:
            np.ndarray: The generated FMCW waveform.
        """
        freq_low = self.freq_low
        freq_high = self.freq_high
        chirp_len = self.chirp_len
        chirp_num = self.chirp_num
        duration = self.duration

        time_axis = np.arange(chirp_len)
        # Linear frequency modulation phase: 2*pi * (f0*t + 0.5*k*t^2)
        phase = 2 * np.pi * (freq_low * time_axis + 0.5 *
                             (freq_high - freq_low) / chirp_len * time_axis**2)
        # Generate chirp signal
        chirp = np.exp(1j * phase)

        wave = np.zeros((chirp_num * duration), dtype=complex)
        for chirp_idx in range(chirp_num):
            wave[chirp_idx * duration: chirp_idx * duration + chirp_len] = chirp

        wave = amp * wave / np.std(wave)
        return wave

    def analyze_mixed(self, wave_mix, sample_rate):
        """Analyzes the mixed signal (de-chirped).

        Args:
            wave_mix (np.ndarray): The product of the transmitted and received signals.
            sample_rate (float): Sampling rate in Hz.

        Returns:
            tuple: (delay_axis, chirp_mix_mat)
                delay_axis: Array of time delays corresponding to FFT bins.
                chirp_mix_mat: Matrix of FFT magnitudes for each chirp.
        """
        freq_low = self.freq_low
        freq_high = self.freq_high
        chirp_len = self.chirp_len
        chirp_num = self.chirp_num
        duration = self.duration

        # Calculate the delay axis based on frequency bandwidth and sample rate
        delay_axis = np.arange(chirp_len) / sample_rate / \
            (freq_high - freq_low)

        chirp_mix_mat = np.zeros((chirp_num, chirp_len))
        for chirp_idx in range(chirp_num):
            # FFT of the mixed signal for each chirp
            chirp_mix = np.abs(np.fft.fft(
                wave_mix[chirp_idx * duration: chirp_idx * duration + chirp_len]))
            chirp_mix_mat[chirp_idx, :] = chirp_mix

        return delay_axis, chirp_mix_mat

    def analyze_digital(self, wave_loop, wave_air, sample_rate):
        """Analyzes received FMCW signal by digitally mixing with a reference loopback.

        Args:
            wave_loop (np.ndarray): The reference loopback signal (Tx).
            wave_air (np.ndarray): The received over-the-air signal (Rx).
            sample_rate (float): Sampling rate.

        Returns:
            tuple: Results from analyze_mixed.
        """
        # Digital mixing of the received signal with the loopback signal
        wave_mix = wave_loop * np.conj(wave_air)

        return self.analyze_mixed(wave_mix, sample_rate)


def simulate(wave_tx, delay_list, atten_list, phase_list, snr, sample_rate):
    """Simulates channel propagation with multipath, attenuation, and noise.

    Args:
        wave_tx (np.ndarray): Transmitted waveform.
        delay_list (list): List of delays in seconds for each path.
        atten_list (list): List of attenuation in dB for each path.
        phase_list (list): List of phase shifts in degrees for each path.
        snr (float): Signal-to-Noise Ratio in dB.
        sample_rate (float): Sampling rate in Hz.

    Returns:
        np.ndarray: Received waveform with channel effects.
    """
    assert len(delay_list) == len(atten_list)
    assert len(delay_list) == len(phase_list)

    wave_amp = np.sqrt(np.mean(np.abs(wave_tx)**2))
    wave_len = np.shape(wave_tx)[0]

    wave_rx = np.zeros((wave_len), dtype=complex)

    for delay, atten, phase in zip(delay_list, atten_list, phase_list):
        # Apply attenuation and phase shift
        wave_path = 10**(-atten / 20) * np.exp(1j * 2 *
                                               np.pi * phase / 360) * wave_tx

        # Apply delay (integer sample shift)
        delay_samples = int(np.round(sample_rate * delay))
        if delay_samples == 0:
            wave_rx += wave_path
        elif delay_samples < wave_len:
            wave_rx[delay_samples:] += wave_path[:-delay_samples]

    # Add Gaussian White Noise
    noise = 10**(-snr / 20) * wave_amp * (np.random.randn(wave_len) +
                                          1j * np.random.randn(wave_len)) / np.sqrt(2)
    wave_rx += noise

    return wave_rx


if __name__ == "__main__":
    sample_rate = 600e6
    snr = 30

    # Loop Parameters
    atten_loop = 10
    phase_loop = 314

    # Over-the-air Parameters
    delay_air_list = [0.1e-6, 0.2e-6, 0.5e-6]
    atten_air_list = [20, 30, 35]
    phase_air_list = [159, 265, 358]

    fmcw = FMCW()
    wave = fmcw.generate()

    # Simulate reference loopback
    wave_loop = simulate(wave,
                         delay_list=[0],
                         atten_list=[atten_loop],
                         phase_list=[phase_loop],
                         snr=snr,
                         sample_rate=sample_rate)

    # Simulate over-the-air signal
    wave_air = simulate(wave,
                        delay_list=delay_air_list,
                        atten_list=atten_air_list,
                        phase_list=phase_air_list,
                        snr=snr,
                        sample_rate=sample_rate)

    delay_axis, chirp_mat = fmcw.analyze_digital(
        wave_loop, wave_air, sample_rate=sample_rate)

    # Define limits for plots
    limit_time = delay_air_list[-1] * 2
    limit_idx = np.searchsorted(delay_axis, limit_time)
    limit_samples = int(limit_time * sample_rate)

    # Plot signals
    fig, ax = plt.subplots()
    ax.plot(np.arange(np.shape(wave_loop)[0])[
            :limit_samples], np.real(wave_loop)[:limit_samples], label='Loopback')
    ax.plot(np.arange(np.shape(wave_air)[0])[
            :limit_samples], np.real(wave_air)[:limit_samples], label='Air')
    ax.plot(np.arange(np.shape(wave_air)[0])[:limit_samples], np.real(
        wave_air * wave_loop)[:limit_samples], label='Mixed')
    ax.legend()
    ax.set_xlabel('Time (samples)')
    ax.set_ylabel('Amplitude')
    fig.savefig('wave.png')
    plt.close(fig)

    # Plot single chirp response
    fig, ax = plt.subplots()
    ax.plot(delay_axis[:limit_idx], 20 * np.log10(chirp_mat[0, :limit_idx]))
    ax.set_xlabel('Delay (s)')
    ax.set_ylabel('Magnitude (dB)')
    fig.savefig('result_single_chirp_response.png')
    plt.close(fig)

    # Plot range map
    fig, ax = plt.subplots()
    im = ax.imshow(20 * np.log10(chirp_mat[:, :limit_idx]), aspect='auto', cmap='viridis',
                   extent=[0, delay_axis[limit_idx - 1], chirp_mat.shape[0], 0])
    fig.colorbar(im, ax=ax, label='Magnitude (dB)')
    ax.set_title('Range Map')
    ax.set_xlabel('Delay (s)')
    ax.set_ylabel('Chirp Number')
    fig.savefig('result_range_map.png')
    plt.close(fig)
