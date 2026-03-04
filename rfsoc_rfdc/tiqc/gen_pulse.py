"""
Main script for Single-Qubit Randomized Benchmarking demonstration.

This script demonstrates the usage of the SingleQubitRB class for generating
Clifford sequences, decomposing them into native gates, and compiling to
pulse sequences.
"""

from single_qubit_rb import SingleQubitRB


def main():
    """
    Demonstrate single-qubit randomized benchmarking workflow.
    """
    # Initialize the SingleQubitRB instance
    # Parameters:
    # - carrier_729_pitime: π pulse duration = 4.0 μs
    # - max_m_for_padding: maximum sequence length for fixed-size arrays = 8
    # - rng_seed: random seed for reproducibility = 123
    rb = SingleQubitRB(
        carrier_729_pitime=4.0e-6,
        max_m_for_padding=8,
        rng_seed=123
    )

    # Optional: switch to clifford_inverse recovery mode
    # rb.recovery_mode = 'clifford_inverse'

    print("="*70)
    print("Single-Qubit Randomized Benchmarking Demo")
    print("="*70)
    print(f"\nConfiguration: {rb}")
    print()

    # Step 1: Generate a random Clifford sequence
    sequence_length = 4
    print(
        f"Step 1: Generate random Clifford sequence (length={sequence_length})")
    cliffords = rb.generate_Clifford_sequence(sequence_length)
    print(f"Clifford indices: {cliffords}")
    print()

    # Step 2: Decompose into native gate sequence
    print("Step 2: Decompose Cliffords into native gates")
    gates = rb.decomposite_Clifford_sequence_into_gate_sequence(cliffords)
    print(f"Native gates (axis, angle_deg):")
    for i, (axis, angle) in enumerate(gates, 1):
        print(f"  {i:2d}. {axis.upper()}{angle:+4d}°")
    print()

    # Step 3: Compile to pulse sequences
    print("Step 3: Compile to pulse phase/period/angle sequences")
    phases, periods, angles, valid_len, residual = \
        rb.generate_pulse_phase_period_angle_sequence(gates)

    print(f"\nValid pulses: {valid_len}")
    print(f"Total slots (with padding): {len(phases)}")
    print(
        f"Residual Z-frame phase: {residual:.6f} rad ({residual*180/3.14159:.3f}°)")
    print()

    # Display the pulse sequences (only valid pulses)
    print("Pulse Sequences (valid pulses only):")
    print("-"*70)
    print(f"{'#':<4} {'Phase (rad)':<15} {'Period (μs)':<15} {'Angle (rad)':<15}")
    print("-"*70)
    for i in range(valid_len):
        print(
            f"{i+1:<4} {phases[i]:<15.6f} {periods[i]*1e6:<15.6f} {angles[i]:<15.6f}")
    print("-"*70)
    print()

    # Summary
    print("="*70)
    print("Results Summary")
    print("="*70)
    print(f"Clifford sequence: {cliffords}")
    print(f"Number of native gates: {len(gates)}")
    print(f"Number of physical pulses: {valid_len}")
    print(
        f"Residual phase (should be ~0 for exact_inverse): {residual:.6e} rad")
    print()

    # Return results for further processing if needed
    return {
        'cliffords': cliffords,
        'gates': gates,
        'phases': phases,
        'periods': periods,
        'angles': angles,
        'valid_len': valid_len,
        'residual': residual
    }


if __name__ == "__main__":
    results = main()

    # Additional verification
    print("Verification:")
    print(f"  ✓ Generated {len(results['cliffords'])} Clifford gates")
    print(f"  ✓ Decomposed to {len(results['gates'])} native gates")
    print(f"  ✓ Compiled to {results['valid_len']} physical pulses")

    if abs(results['residual']) < 1e-10:
        print(
            f"  ✓ Residual phase is negligible ({results['residual']:.2e} rad)")
    else:
        print(f"  ⚠ Residual phase: {results['residual']:.6f} rad")
    print()
