import numpy as np
from rfsoc_rfdc.rfdc_type import MyRFdcType
import logging
import math

import matplotlib.pyplot as plt


class WaveFormGenerator:
    """
    A class that generates different types of waveforms.
    """
    @staticmethod
    def generate_tone(tone_freq_mhz, sample_rate, interpolation_rate, sideband="SSB", mode="iq2real"):
        pts_per_period = int(sample_rate / interpolation_rate / tone_freq_mhz)

        if pts_per_period <= 4:
            logging.warning("target CW frequency too low")

        # Ensure sample_pts * repeat_time > 8000
        repeat_time = math.ceil(8001 / pts_per_period)

        real = WaveFormGenerator.generate_sine_wave(
            repeat_time=repeat_time, sample_pts=pts_per_period)

        if mode == "real2real":
            return real

        # For iq2real / iq2iq
        if sideband == "SSB":  # Single side band
            imag = WaveFormGenerator.generate_cosine_wave(
                repeat_time=repeat_time, sample_pts=pts_per_period)
            data = real + 1j * imag
        elif sideband == "DSB":  # Double side band
            data = real + 1j * 0
        else:
            raise ValueError(f"Unknown sideband mode: {sideband}")

        return data

    @staticmethod
    def generate_sine_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0, raw_np=False):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sin(2 * np.pi * t)
        if raw_np:
            return wave
        else:
            wave *= int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_square_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sign(np.sin(2 * np.pi * t)) * \
            int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_triangle_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * np.abs(2 * (t - np.floor(t + 0.5))) - 1
        wave *= int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_sawtooth_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * (t - np.floor(0.5 + t))
        wave *= int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_cosine_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0, raw_np=False):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.cos(2 * np.pi * t)
        if raw_np:
            return wave
        else:
            wave *= int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_binary_seq(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        num_of_samples = repeat_time * sample_pts
        wave = np.tile([0, 1], num_of_samples // 2 + 1)[:num_of_samples]
        wave *= int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_ten_sine(scaling_factor=1.0):
        ten_sine = WaveFormGenerator.generate_sine_wave(
            repeat_time=10, sample_pts=10, scaling_factor=scaling_factor)
        ten_sine = np.append(ten_sine, np.zeros(
            100, dtype=MyRFdcType.DATA_PATH_DTYPE))
        wave = np.append(ten_sine, ten_sine)
        return wave

    @staticmethod
    def generate_zadoff_chu_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        u = 1  # Root index of the the ZC sequence
        seq_length = sample_pts * repeat_time
        q = 0  # Cyclic shift of the sequence

        for el in [u, seq_length, q]:
            if not float(el).is_integer():
                raise ValueError('{} is not an integer'.format(el))
        if u <= 0:
            raise ValueError('u is not stricly positive')
        if u >= seq_length:
            raise ValueError('u is not stricly smaller than seq_length')
        if np.gcd(u, seq_length) != 1:
            raise ValueError(
                'the greatest common denominator of u and seq_length is not 1')

        cf = seq_length % 2
        n = np.arange(seq_length)
        zcseq = np.exp(-1j * np.pi * u * n * (n+cf+2.*q) / seq_length)

        scale_to_max = int(MyRFdcType.DAC_MAX_SCALE * scaling_factor)

        zcseq_real = np.real(zcseq) * scale_to_max
        zcseq_real = zcseq_real.astype(MyRFdcType.DATA_PATH_DTYPE)
        zcseq_imag = np.imag(zcseq) * scale_to_max
        zcseq_imag = zcseq_imag.astype(MyRFdcType.DATA_PATH_DTYPE)

        return zcseq_real, zcseq_imag

    @staticmethod
    def generate_no_wave(repeat_time=1, sample_pts=1000, scaling_factor=1.0):
        wave = np.zeros(sample_pts * repeat_time)
        return wave.astype(MyRFdcType.DATA_PATH_DTYPE)


if __name__ == "__main__":
    # Create an instance of the WaveFormGenerator class
    generator = WaveFormGenerator()

    # Generate waveforms
    sine_wave = generator.generate_sine_wave()
    square_wave = generator.generate_square_wave()
    triangle_wave = generator.generate_triangle_wave()
    sawtooth_wave = generator.generate_sawtooth_wave()
    zadoff_chu_wave = generator.generate_zadoff_chu_wave()

    # Plotting
    fig, axs = plt.subplots(5, 1, figsize=(10, 8))

    # Plot sine wave
    axs[0].plot(sine_wave)
    axs[0].set_title("Sine Wave")

    # Plot square wave
    axs[1].plot(square_wave)
    axs[1].set_title("Square Wave")

    # Plot triangle wave
    axs[2].plot(triangle_wave)
    axs[2].set_title("Triangle Wave")

    # Plot sawtooth wave
    axs[3].plot(sawtooth_wave)
    axs[3].set_title("Sawtooth Wave")

    # Plot sawtooth wave
    axs[4].plot(zadoff_chu_wave)
    axs[4].set_title("Zadoff Chu Wave")

    # Display the plot
    plt.tight_layout()
    plt.show()
