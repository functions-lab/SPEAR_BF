"""
SquareWave class for generating square wave pulses based on phase and reference tone.

This module defines a square wave that is aligned to a reference tone frequency.
The phase parameter determines the delay (start time) of the square wave relative
to the reference tone.
"""

import numpy as np


class SquareWave:
    """
    A square wave pulse aligned to a reference tone frequency.

    The square wave is characterized by:
    - A reference tone frequency that determines timing alignment
    - A phase offset that sets the start time (delay)
    - A duration that defines the pulse width

    Parameters
    ----------
    ref_freq : float
        Reference tone frequency in Hz (e.g., 153 MHz)
    phase : float
        Phase offset in radians. This determines the start time delay.
        Positive phase = later start time (lag)
        Negative phase = earlier start time (lead)
    duration : float
        Duration of the square wave pulse in seconds

    Attributes
    ----------
    ref_freq : float
        Reference tone frequency in Hz
    phase : float
        Phase offset in radians
    duration : float
        Pulse duration in seconds
    start_t : float
        Start time of the pulse in seconds (calculated from phase)
    end_t : float
        End time of the pulse in seconds (start_t + duration)
    """

    def __init__(self, ref_freq, phase, duration):
        """
        Initialize the SquareWave instance.

        Parameters
        ----------
        ref_freq : float
            Reference tone frequency in Hz
        phase : float
            Phase offset in radians
        duration : float
            Duration in seconds
        """
        self.ref_freq = ref_freq
        # Initialize directly with wrapped value
        self._phase = phase % (2 * np.pi)
        self.duration = duration

        # Calculate start_t from phase and reference frequency
        # phase = 2π × freq × delay
        # delay = phase / (2π × freq)
        self.start_t = 0
        self.end_t = self.start_t + self.duration

    @property
    def phase(self):
        """
        Get the phase offset in radians.

        Returns
        -------
        float
            Phase offset in radians (always positive, [0, 2π))
        """
        return self._phase

    @phase.setter
    def phase(self, value):
        """
        Set the phase offset in radians.

        Ensures the phase is always positive by wrapping negative values.

        Parameters
        ----------
        value : float
            Phase offset in radians
        """
        # Wrap phase to [0, 2π) range
        self._phase = value % (2 * np.pi)

    def _calculate_delay_from_phase(self):
        """
        Calculate time delay from phase offset.

        Returns
        -------
        delay : float
            Time delay in seconds corresponding to the phase offset (always >= 0)
        """
        # delay = phase / (2π × frequency)
        # Phase is already guaranteed to be positive by the setter
        delay = self._phase / (2 * np.pi * self.ref_freq)

        return delay

    def get_wave(self, t):
        """
        Get the value of the square wave at time t.

        Parameters
        ----------
        t : float or ndarray
            Time in seconds (can be scalar or array)

        Returns
        -------
        value : float or ndarray
            Square wave value: 1 if within [start_t, end_t], 0 otherwise
            Returns same type as input (scalar or array)
        """
        # Convert to numpy array for consistent handling
        t_array = np.asarray(t)
        scalar_input = t_array.ndim == 0

        if scalar_input:
            t_array = t_array.reshape(1)

        # Return 1 if t is within [start_t, end_t], else 0
        result = np.where((t_array >= self.start_t) &
                          (t_array <= self.end_t), 1.0, 0.0)

        if scalar_input:
            return result[0]
        return result

    def get_schedule(self):
        """
        Get the scheduled start and end times of this square wave.

        Returns
        -------
        start_t : float
            Start time in seconds
        end_t : float
            End time in seconds
        """
        return self.start_t, self.end_t

    def set_schedule(self, start_t, end_t):
        """
        Update the scheduled start and end times.

        This is used by the Scheduler to adjust timing when padding is needed.

        Parameters
        ----------
        start_t : float
            New start time in seconds
        end_t : float
            New end time in seconds
        """
        # Store old duration for verification
        old_duration = self.duration
        new_duration = end_t - start_t

        # Check if durations match (allow small floating point error)
        if not np.isclose(old_duration, new_duration, rtol=1e-9, atol=1e-12):
            raise ValueError(
                f"Duration mismatch: old duration = {old_duration*1e6:.6f} μs, "
                f"new duration = {new_duration*1e6:.6f} μs. "
                f"The Scheduler should preserve pulse duration."
            )

        self.start_t = start_t
        self.end_t = end_t
        # Update duration to maintain consistency
        self.duration = new_duration

    def __repr__(self):
        """String representation of the SquareWave."""
        return (f"SquareWave(ref_freq={self.ref_freq/1e6:.1f} MHz, "
                f"phase={self._phase:.6f} rad ({self._phase*180/np.pi:.2f}°), "
                f"duration={self.duration*1e6:.3f} μs, "
                f"start_t={self.start_t*1e9:.3f} ns, "
                f"end_t={self.end_t*1e9:.3f} ns)")
