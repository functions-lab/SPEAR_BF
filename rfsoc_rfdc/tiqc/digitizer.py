"""
Digitizer class for converting SquareWave pulses to IQ waveforms.

This module digitizes square wave pulses at a specified sampling rate and
generates complex IQ waveforms suitable for RF transmission.
"""

import numpy as np


class Digitizer:
    """
    Digitize SquareWave pulses into IQ waveforms.

    The Digitizer samples the square wave pulses at a specified sampling rate
    and generates complex-valued IQ waveforms. The output is a baseband
    representation where the square wave modulates a carrier.

    Parameters
    ----------
    samp_rate : float
        Sampling rate in Hz (e.g., 100 MHz for RFSoC)
    square_wave_list : list of SquareWave
        List of SquareWave instances to digitize

    Attributes
    ----------
    samp_rate : float
        Sampling rate in Hz
    square_wave_list : list
        List of SquareWave instances
    sample_period : float
        Time between samples in seconds (1/samp_rate)
    """

    def __init__(self, samp_rate, square_wave_list):
        """
        Initialize the Digitizer.

        Parameters
        ----------
        samp_rate : float
            Sampling rate in Hz
        square_wave_list : list of SquareWave
            List of SquareWave instances to digitize
        """
        self.samp_rate = samp_rate
        self.square_wave_list = square_wave_list
        self.sample_period = 1.0 / samp_rate

    def _calculate_time_range(self):
        """
        Calculate the time range needed to capture all pulses.

        Returns
        -------
        t_start : float
            Start time in seconds
        t_end : float
            End time in seconds
        """
        if not self.square_wave_list:
            return 0.0, 0.0

        # Find the earliest start and latest end across all pulses
        t_start = self.square_wave_list[0].start_t
        t_end = self.square_wave_list[-1].end_t

        return t_start, t_end

    def gen_digi_iq(self, ref_freq=None, amplitude=1.0):
        """
        Generate IQ waveform from the scheduled square wave pulses.

        Parameters
        ----------
        ref_freq : float, optional
            Reference frequency in Hz. If None, generates baseband pulses.
            If specified, modulates the square waves onto this reference tone.
        amplitude : float, optional
            Output amplitude scaling factor (default: 1.0)

        Returns
        -------
        iq_waveform : ndarray
            Complex-valued IQ waveform (dtype: complex128)
        time_array : ndarray
            Time array corresponding to the samples (in seconds)
        """
        # Calculate time range
        t_start, t_end = self._calculate_time_range()

        # Generate time array
        num_samples = int(np.ceil((t_end - t_start) * self.samp_rate))
        time_array = t_start + np.arange(num_samples) * self.sample_period

        # Initialize IQ waveform (complex array)
        iq_waveform = np.zeros(num_samples, dtype=np.complex128)

        # Sum contributions from all square waves
        for wave in self.square_wave_list:
            # Get the square wave envelope
            envelope = wave.get_wave(time_array)
            phase = wave.phase  # Phase in radians

            if ref_freq is not None:
                # Modulate onto reference tone with phase shift: envelope * exp(j * (2π * f_ref * t + φ))
                carrier = np.exp(
                    1j * (2 * np.pi * ref_freq * time_array + phase))
                iq_waveform += amplitude * envelope * carrier
            else:
                # Baseband: just the envelope as complex value (real part)
                # Using exp(j*0) = 1 for baseband representation
                iq_waveform += amplitude * envelope

        return iq_waveform, time_array

    def gen_digi_real(self, amplitude=1.0):
        """
        Generate a real-valued waveform (sum of all square waves).

        This is useful for direct digital synthesis without carrier modulation.

        Parameters
        ----------
        amplitude : float, optional
            Output amplitude scaling factor (default: 1.0)

        Returns
        -------
        waveform : ndarray
            Real-valued waveform
        time_array : ndarray
            Time array corresponding to the samples (in seconds)
        """
        # Calculate time range
        t_start, t_end = self._calculate_time_range()

        # Generate time array
        num_samples = int(np.ceil((t_end - t_start) * self.samp_rate))
        time_array = t_start + np.arange(num_samples) * self.sample_period

        # Initialize waveform
        waveform = np.zeros(num_samples, dtype=np.float64)

        # Sum contributions from all square waves
        for wave in self.square_wave_list:
            waveform += amplitude * wave.get_wave(time_array)

        return waveform, time_array

    def save_waveform(self, filename, waveform, time_array, ref_freq=None):
        """
        Save a generated waveform to a file.

        Parameters
        ----------
        filename : str
            Output filename (typically .npy extension)
        waveform : ndarray
            The complex-valued waveform to save.
        time_array : ndarray
            Time array corresponding to the samples (in seconds)
        ref_freq : float, optional
            Reference frequency in Hz (None for baseband), used only for print statement.
        """
        np.save(filename, waveform)

        print(f"Waveform saved to: {filename}")
        print(f"  Number of samples: {len(waveform)}")
        print(f"  Duration: {len(waveform) / self.samp_rate * 1e6:.3f} μs")
        print(f"  Sampling rate: {self.samp_rate/1e9:.3f} GHz")
        print(
            f"  Reference frequency: {ref_freq/1e6 if ref_freq else 0:.3f} MHz")

        return waveform, time_array

    def get_waveform_stats(self, iq_waveform):
        """
        Calculate statistics of the generated waveform.

        Parameters
        ----------
        iq_waveform : ndarray
            Complex IQ waveform

        Returns
        -------
        stats : dict
            Dictionary containing waveform statistics
        """
        magnitude = np.abs(iq_waveform)
        power = magnitude ** 2

        stats = {
            'num_samples': len(iq_waveform),
            'peak_magnitude': np.max(magnitude),
            'mean_magnitude': np.mean(magnitude),
            'rms_magnitude': np.sqrt(np.mean(power)),
            'total_energy': np.sum(power),
            'peak_to_avg_ratio': np.max(magnitude) / (np.mean(magnitude) + 1e-10)
        }

        return stats

    def print_waveform_stats(self, iq_waveform):
        """
        Print statistics of the generated waveform.

        Parameters
        ----------
        iq_waveform : ndarray
            Complex IQ waveform
        """
        stats = self.get_waveform_stats(iq_waveform)

        print("="*60)
        print("Waveform Statistics")
        print("="*60)
        print(f"Number of samples:    {stats['num_samples']}")
        print(f"Peak magnitude:       {stats['peak_magnitude']:.6f}")
        print(f"Mean magnitude:       {stats['mean_magnitude']:.6f}")
        print(f"RMS magnitude:        {stats['rms_magnitude']:.6f}")
        print(f"Total energy:         {stats['total_energy']:.6e}")
        print(f"Peak-to-avg ratio:    {stats['peak_to_avg_ratio']:.3f}")
        print("="*60)
        print()

    def __repr__(self):
        """String representation of the Digitizer."""
        return (f"Digitizer(samp_rate={self.samp_rate/1e9:.3f} GHz, "
                f"num_pulses={len(self.square_wave_list)})")
