"""
Unit tests for SquareWave, Scheduler, and Digitizer classes.
"""

import numpy as np
from square_wave import SquareWave
from scheduler import Scheduler
from digitizer import Digitizer


def square_wave_test():
    """Test SquareWave class basic functionality."""
    print("Testing SquareWave class...")

    ref_freq = 153e6
    phase = -np.pi/2  # -90 degrees
    duration = 2e-6   # 2 μs

    wave = SquareWave(ref_freq, phase, duration)

    # Test delay calculation (negative phase wraps to positive by adding 2π)
    wrapped_phase = phase + 2 * np.pi if phase < 0 else phase
    expected_delay = wrapped_phase / (2 * np.pi * ref_freq)
    assert abs(wave.start_t - expected_delay) < 1e-12, "Delay calculation error"
    assert wave.start_t >= 0, "Delay should be positive"

    # Test get_wave function
    assert wave.get_wave(
        wave.start_t - 1e-9) == 0.0, "Should be 0 before start"
    assert wave.get_wave(wave.start_t) == 1.0, "Should be 1 at start"
    assert wave.get_wave((wave.start_t + wave.end_t) /
                         2) == 1.0, "Should be 1 in middle"
    assert wave.get_wave(wave.end_t) == 1.0, "Should be 1 at end"
    assert wave.get_wave(wave.end_t + 1e-9) == 0.0, "Should be 0 after end"

    # Test with array input
    t_array = np.array([wave.start_t - 1e-9, wave.start_t,
                       wave.end_t, wave.end_t + 1e-9])
    result = wave.get_wave(t_array)
    expected = np.array([0.0, 1.0, 1.0, 0.0])
    assert np.allclose(result, expected), "Array input test failed"

    print(f"  ✓ SquareWave basic tests passed")
    print(f"    {wave}")
    return True


def test_scheduler():
    """Test Scheduler class functionality."""
    print("\nTesting Scheduler class...")

    ref_freq = 153e6
    min_padding = 100e-9  # 100 ns

    # Create overlapping pulses
    wave1 = SquareWave(ref_freq, phase=-np.pi/2, duration=2e-6)
    wave2 = SquareWave(ref_freq, phase=0.0, duration=4e-6)
    wave3 = SquareWave(ref_freq, phase=0.0, duration=4e-6)

    original_start2 = wave2.start_t

    waves = [wave1, wave2, wave3]
    scheduler = Scheduler(waves, ref_freq, min_padding_time=min_padding)

    # Check that pulses don't overlap
    for i in range(len(waves) - 1):
        start_i, end_i = waves[i].get_schedule()
        start_next, end_next = waves[i+1].get_schedule()
        separation = start_next - end_i
        assert separation >= min_padding, f"Insufficient padding between pulse {i} and {i+1}"

    # Check that wave2 was shifted
    assert wave2.start_t != original_start2, "Wave2 should have been rescheduled"

    print(f"  ✓ Scheduler tests passed")
    print(f"    {scheduler}")
    scheduler.print_schedule()
    return True


def test_digitizer():
    """Test Digitizer class functionality."""
    print("\nTesting Digitizer class...")

    ref_freq = 153e6
    samp_rate = 1e9

    # Create simple pulses
    wave1 = SquareWave(ref_freq, phase=0.0, duration=1e-6)
    wave2 = SquareWave(ref_freq, phase=np.pi, duration=1e-6)

    waves = [wave1, wave2]
    scheduler = Scheduler(waves, ref_freq, min_padding_time=100e-9)

    digitizer = Digitizer(samp_rate, waves)

    # Test baseband generation
    iq_waveform, time_array = digitizer.gen_digi_iq(
        ref_freq=None, amplitude=1.0)

    assert len(iq_waveform) == len(time_array), "IQ and time arrays must match"
    assert len(iq_waveform) > 0, "Should generate some samples"
    assert iq_waveform.dtype == np.complex128, "Should be complex type"

    # Test that waveform has non-zero regions
    magnitude = np.abs(iq_waveform)
    assert np.max(magnitude) > 0, "Should have non-zero magnitude"

    # Test real waveform generation
    real_waveform, time_array2 = digitizer.gen_digi_real(amplitude=1.0)
    assert real_waveform.dtype == np.float64, "Should be real type"

    # Test statistics
    stats = digitizer.get_waveform_stats(iq_waveform)
    assert 'num_samples' in stats, "Stats should contain num_samples"
    assert 'peak_magnitude' in stats, "Stats should contain peak_magnitude"

    print(f"  ✓ Digitizer tests passed")
    print(f"    {digitizer}")
    digitizer.print_waveform_stats(iq_waveform)

    return True


def test_integration():
    """Integration test using data from gen_pulse.py."""
    print("\nTesting integration with gen_pulse.py data...")

    ref_freq = 153e6

    # Data from gen_pulse.py output
    phases = np.array([-1.570796, 0.000000, 0.000000, 1.570796])
    periods = np.array([2.0e-6, 4.0e-6, 4.0e-6, 2.0e-6])

    # Create pulses
    waves = [SquareWave(ref_freq, p, d) for p, d in zip(phases, periods)]

    # Schedule
    scheduler = Scheduler(waves, ref_freq, min_padding_time=2e-6)

    # Digitize
    digitizer = Digitizer(600e6, waves)
    iq_waveform, time_array = digitizer.gen_digi_iq(
        ref_freq=None, amplitude=1.0)

    assert len(iq_waveform) > 0, "Should generate samples"

    # Verify total duration is reasonable
    total_duration = scheduler.get_total_duration()
    expected_min_duration = sum(periods)
    assert total_duration >= expected_min_duration, "Total duration should be at least sum of periods"

    print(f"  ✓ Integration test passed")
    print(
        f"    Generated {len(iq_waveform)} samples over {total_duration*1e6:.3f} μs")

    return True


def run_all_tests():
    """Run all unit tests."""
    print("="*80)
    print("Running Unit Tests")
    print("="*80)

    tests = [
        square_wave_test,
        test_scheduler,
        test_digitizer,
        test_integration
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Test error: {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
