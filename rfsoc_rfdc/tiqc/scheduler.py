"""
Scheduler class for managing timing of multiple SquareWave pulses.

This module provides a scheduler that ensures proper spacing between square wave
pulses, adding padding periods as needed to avoid overlaps.
"""

import numpy as np


class Scheduler:
    """
    Schedule multiple SquareWave pulses with proper timing separation.

    The Scheduler ensures that square wave pulses don't overlap by adding
    integer multiples of the reference tone period as needed. A minimum
    padding time can be specified to guarantee separation between pulses.

    Parameters
    ----------
    square_wave_list : list of SquareWave
        List of SquareWave instances to schedule
    ref_freq : float
        Reference tone frequency in Hz (used to calculate period for padding)
    min_padding_time : float, optional
        Minimum time separation between consecutive pulses in seconds
        (default: 0.0)

    Attributes
    ----------
    square_wave_list : list
        List of SquareWave instances
    ref_freq : float
        Reference tone frequency in Hz
    min_padding_time : float
        Minimum padding time between pulses in seconds
    ref_period : float
        Period of the reference tone in seconds (1/ref_freq)
    """

    def __init__(self, square_wave_list, ref_freq, min_padding_time=0.0):
        """
        Initialize the Scheduler.

        Parameters
        ----------
        square_wave_list : list of SquareWave
            List of SquareWave instances to schedule
        ref_freq : float
            Reference tone frequency in Hz
        min_padding_time : float, optional
            Minimum padding time in seconds (default: 0.0)
        """
        self.square_wave_list = square_wave_list
        self.ref_freq = ref_freq
        self.min_padding_time = min_padding_time
        self.ref_period = 1.0 / ref_freq

        # Schedule the pulses upon initialization
        self._schedule_pulses()

    def _schedule_pulses(self):
        """
        Schedule all pulses, adding padding periods as needed to avoid overlaps.

        This method iterates through the square wave list and adjusts timing
        to ensure:
        1. No overlaps between consecutive pulses
        2. At least min_padding_time separation between pulses
        3. Timing adjustments are in integer multiples of ref_period
        """
        if not self.square_wave_list:
            return

        # Process each pulse starting from the second one
        for i in range(1, len(self.square_wave_list)):
            current_wave = self.square_wave_list[i]
            previous_wave = self.square_wave_list[i - 1]

            # Get timing of current and previous pulses
            current_start, current_end = current_wave.get_schedule()
            prev_start, prev_end = previous_wave.get_schedule()

            # Check if current pulse starts before previous pulse ends
            # with required padding
            required_start = prev_end + self.min_padding_time

            if current_start < required_start:
                # Calculate how much time we need to shift
                time_deficit = required_start - current_start

                # Calculate number of periods needed to provide sufficient padding
                # Use ceiling to ensure we have at least the minimum padding
                num_periods = int(np.ceil(time_deficit / self.ref_period))

                # Calculate the time shift (in integer multiples of ref_period)
                time_shift = num_periods * self.ref_period

                # Update the current pulse's timing
                new_start = current_start + time_shift
                new_end = current_end + time_shift
                current_wave.set_schedule(new_start, new_end)

    def get_total_duration(self):
        """
        Get the total duration from the start of the first pulse to the end
        of the last pulse.

        Returns
        -------
        total_duration : float
            Total duration in seconds, or 0.0 if list is empty
        """
        if not self.square_wave_list:
            return 0.0

        first_start, _ = self.square_wave_list[0].get_schedule()
        _, last_end = self.square_wave_list[-1].get_schedule()

        return last_end - first_start

    def get_schedule_summary(self):
        """
        Get a summary of all scheduled pulses.

        Returns
        -------
        summary : list of dict
            List of dictionaries containing timing information for each pulse
        """
        summary = []
        for i, wave in enumerate(self.square_wave_list):
            start_t, end_t = wave.get_schedule()
            summary.append({
                'index': i,
                'start_t': start_t,
                'end_t': end_t,
                'duration': end_t - start_t,
                'phase': wave.phase
            })
        return summary

    def print_schedule(self):
        """
        Print a formatted schedule of all pulses.
        """
        print("="*80)
        print("Pulse Schedule")
        print("="*80)
        print(f"Reference frequency: {self.ref_freq/1e6:.3f} MHz")
        print(f"Reference period: {self.ref_period*1e9:.3f} ns")
        print(f"Minimum padding time: {self.min_padding_time*1e9:.3f} ns")
        print(f"Total duration: {self.get_total_duration()*1e6:.3f} μs")
        print("-"*80)
        print(f"{'#':<4} {'Start (ns)':<15} {'End (ns)':<15} {'Duration (ns)':<15} "
              f"{'Phase (rad)':<15}")
        print("-"*80)

        for i, wave in enumerate(self.square_wave_list):
            start_t, end_t = wave.get_schedule()
            print(f"{i:<4} {start_t*1e9:<15.3f} {end_t*1e9:<15.3f} "
                  f"{(end_t-start_t)*1e9:<15.3f} {wave.phase:<15.6f}")

        print("="*80)
        print()

    def __repr__(self):
        """String representation of the Scheduler."""
        return (f"Scheduler(num_pulses={len(self.square_wave_list)}, "
                f"ref_freq={self.ref_freq/1e6:.1f} MHz, "
                f"min_padding={self.min_padding_time*1e9:.1f} ns, "
                f"total_duration={self.get_total_duration()*1e6:.3f} μs)")
