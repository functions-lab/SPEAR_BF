"""
Demonstration script for SquareWave, Scheduler, and Digitizer classes.

This script shows how to:
1. Create multiple SquareWave pulses from phase information
2. Schedule them using the Scheduler to avoid overlaps
3. Digitize them into IQ waveforms using the Digitizer
"""

import numpy as np
import matplotlib.pyplot as plt
from square_wave import SquareWave
from scheduler import Scheduler
from digitizer import Digitizer


REF_FREQ = 153e6  # Single source of truth for reference and carrier tones
SAMP_RATE = 300e6


def plot_waveforms(iq_waveform, time_array, square_wave_list, samp_rate, ref_freq=REF_FREQ, title="IQ Waveform"):
    """
    Plot the generated IQ waveform with pulse markers, phase tracking, and reference tone.

    Parameters
    ----------
    iq_waveform : ndarray
        Complex IQ waveform
    time_array : ndarray
        Time array in seconds
    square_wave_list : list of SquareWave
        List of square wave pulses for reference
    samp_rate : float
        Sampling rate in Hz
    ref_freq : float
        Reference tone frequency in Hz
    title : str
        Plot title
    """
    fig, axes = plt.subplots(6, 1, figsize=(14, 17))

    time_ns = time_array * 1e9  # nanoseconds

    # Plot magnitude
    magnitude = np.abs(iq_waveform)
    axes[0].plot(time_ns, magnitude, linewidth=0.8)
    axes[0].set_ylabel('Magnitude')
    axes[0].set_title(f'{title} - Magnitude')
    axes[0].grid(True, alpha=0.3)

    # Mark pulse regions
    for i, wave in enumerate(square_wave_list):
        start_t, end_t = wave.get_schedule()
        axes[0].axvspan(start_t*1e9, end_t*1e9, alpha=0.2, color=f'C{i % 10}',
                        label=f'Pulse {i+1}')
    axes[0].legend(loc='upper right', fontsize=8)

    # Plot real part
    axes[1].plot(time_ns, np.real(iq_waveform),
                 linewidth=0.8, label='I (Real)')
    axes[1].set_ylabel('I (Real)')
    axes[1].set_title('In-phase Component')
    axes[1].grid(True, alpha=0.3)

    # Plot imaginary part
    axes[2].plot(time_ns, np.imag(iq_waveform),
                 linewidth=0.8, label='Q (Imag)', color='C1')
    axes[2].set_ylabel('Q (Imaginary)')
    axes[2].set_title('Quadrature Component')
    axes[2].grid(True, alpha=0.3)

    # Plot phase across time
    phase = np.angle(iq_waveform)  # Phase in radians [-π, π]
    axes[3].plot(time_ns, phase, linewidth=0.8, color='C2')
    axes[3].set_ylabel('Phase (rad)')
    axes[3].set_title('Phase vs Time')
    axes[3].grid(True, alpha=0.3)
    axes[3].set_ylim([-np.pi - 0.5, np.pi + 0.5])

    # Add horizontal lines at key phase values
    axes[3].axhline(y=0, color='gray', linestyle='--',
                    alpha=0.5, linewidth=0.8)
    axes[3].axhline(y=np.pi/2, color='gray', linestyle='--',
                    alpha=0.5, linewidth=0.8)
    axes[3].axhline(y=-np.pi/2, color='gray',
                    linestyle='--', alpha=0.5, linewidth=0.8)
    axes[3].axhline(y=np.pi, color='gray', linestyle='--',
                    alpha=0.5, linewidth=0.8)
    axes[3].axhline(y=-np.pi, color='gray', linestyle='--',
                    alpha=0.5, linewidth=0.8)

    # Mark pulse regions and their input phases
    for i, wave in enumerate(square_wave_list):
        start_t, end_t = wave.get_schedule()
        axes[3].axvspan(start_t*1e9, end_t*1e9, alpha=0.2, color=f'C{i % 10}')
        # Annotate with the input phase
        mid_t = (start_t + end_t) / 2 * 1e9
        axes[3].text(mid_t, np.pi + 0.3, f'φ={wave.phase:.2f}',
                     ha='center', fontsize=8, color=f'C{i % 10}')

    # Generate time array for reference tone (same as input time_array)
    num_samples = len(time_array)
    sample_period = 1.0 / samp_rate
    ref_tone_time_array = np.arange(num_samples) * sample_period

    # Plot reference tone and IQ mixed waveform together
    ref_tone = np.exp(1j * 2 * np.pi * ref_freq * ref_tone_time_array)

    axes[4].plot(time_ns, np.real(ref_tone), linewidth=0.6, color='C3',
                 alpha=0.6, label=f'Reference Tone ({ref_freq/1e6:.1f} MHz)')

    # Plot the real part of IQ waveform (mixed signal)
    axes[4].plot(time_ns, np.real(iq_waveform), linewidth=0.8, color='C0',
                 alpha=0.8, label='Direct synthesis (NCO=0)')

    axes[4].set_ylabel('Amplitude')
    axes[4].set_title(f'Reference Tone vs IQ Mixed Waveform')
    axes[4].grid(True, alpha=0.3)
    axes[4].legend(loc='upper right')

    # Mark pulse regions
    for i, wave in enumerate(square_wave_list):
        start_t, end_t = wave.get_schedule()
        axes[4].axvspan(start_t*1e9, end_t*1e9, alpha=0.15, color=f'C{i % 10}')

    # Plot reference tone and IQ magnitude together
    axes[5].plot(time_ns, np.real(ref_tone), linewidth=0.6, color='C3',
                 alpha=0.6, label=f'Reference Tone ({ref_freq/1e6:.1f} MHz)')

    # Plot the magnitude of IQ waveform
    axes[5].plot(time_ns, np.abs(iq_waveform), linewidth=0.8, color='C0',
                 alpha=0.8, label=f'Baseband with NCO={ref_freq/1e6:.1f} MHz')

    axes[5].set_ylabel('Amplitude')
    axes[5].set_xlabel('Time (ns)')
    axes[5].set_title(f'Reference Tone vs Baseband')
    axes[5].grid(True, alpha=0.3)
    axes[5].legend(loc='upper right')

    # Mark pulse regions
    for i, wave in enumerate(square_wave_list):
        start_t, end_t = wave.get_schedule()
        axes[5].axvspan(start_t*1e9, end_t*1e9, alpha=0.15, color=f'C{i % 10}')

    plt.tight_layout(h_pad=2.0)
    plt.show()


def demo_with_carrier():
    """
    Demonstration with carrier frequency modulation.
    """
    print("="*80)
    print("DEMO: IQ Waveform with Carrier Modulation")
    print("="*80)
    print()

    # Reference frequency used for both scheduling and modulation
    ref_freq = REF_FREQ

    # Use same pulses as demo_basic_usage
    phases = np.array([-1.570796, 0.000000, 0.000000, 1.570796])
    # phases = np.array([0, 0.000000, 0.000000, 1.570796])
    periods = np.array([2.0e-6, 4.0e-6, 4.0e-6, 2.0e-6])

    # Offset phase shift caused by all the first pulses
    phase_offset = phases[0]
    for p_i in range(0, len(phases)):
        phases[p_i] -= phase_offset

    # Make sure all phases are positive
    for p in phases:
        p = p % (2 * np.pi)

    print("Creating pulses with different phases...")
    square_wave_list = []
    for i, (phase, period) in enumerate(zip(phases, periods)):
        wave = SquareWave(ref_freq=ref_freq, phase=phase, duration=period)
        square_wave_list.append(wave)
        print(f"Pulse {i+1}: {wave}")
    print()

    # Schedule the pulses
    print("Step 2: Schedule pulses with minimum padding")
    print("-"*80)
    min_padding = 2e-6  # 2 μs minimum padding
    scheduler = Scheduler(square_wave_list, ref_freq,
                          min_padding_time=min_padding)
    print(scheduler)
    print()
    scheduler.print_schedule()

    # Digitize the waveform
    print("Step 3: Digitize to IQ waveform")
    print("-"*80)
    digitizer = Digitizer(SAMP_RATE, square_wave_list)
    print(digitizer)
    print()

    # Generate IQ waveform with carrier
    print(f"Generating IQ waveform with {ref_freq/1e6:.1f} MHz reference...")
    iq_waveform, time_array = digitizer.gen_digi_iq(
        ref_freq=ref_freq,
        amplitude=1.0
    )
    print(f"Generated {len(iq_waveform)} samples")
    print()

    digitizer.print_waveform_stats(iq_waveform)

    # Save with carrier
    output_file = "rb_direct_syn.npy"
    digitizer.save_waveform(
        output_file, iq_waveform, time_array, ref_freq=ref_freq)

    # Generate and save baseband waveform
    real_waveform, bb_time_array = digitizer.gen_digi_real(amplitude=1.0)
    # Convert to complex with zero imaginary part
    bb_complex_waveform = real_waveform + 0j
    bb_filename = "rb_baseband.npy"
    digitizer.save_waveform(
        bb_filename, bb_complex_waveform, bb_time_array, ref_freq=None)

    return iq_waveform, time_array, square_wave_list


def main():
    """
    Run all demonstrations.
    """
    print("\n" + "="*80 + "\n")

    # Demo 1: With carrier modulation
    iq_waveform, time_array, waves = demo_with_carrier()

    # Optional: Plot the waveforms
    try:
        print("\nGenerating plots...")
        plot_waveforms(iq_waveform, time_array, waves, SAMP_RATE, ref_freq=REF_FREQ,
                       title="Carrier-Modulated Square Wave Pulses")
    except Exception as e:
        print(f"Plotting skipped: {e}")

    print("\n" + "="*80)
    print("All demonstrations completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
