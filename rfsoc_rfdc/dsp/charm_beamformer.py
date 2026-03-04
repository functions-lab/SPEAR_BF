import logging
import numpy as np
import os
from rfsoc_rfdc.dsp.array_factor import ArrayFactor


class CharmBeamformer(ArrayFactor):
    """
    Beamformer for the CHARM array, consisting of multiple sub-arrays (chips).

    This class models the geometry and beamforming weights for a multi-chip array.

    Attributes:
        INTRA_CHIP_SPACING (float): Spacing between chips (approx 1.08 mm).
        ELEMENT_PER_CHIP (int): Number of antenna elements per chip (4).
        SPEED_OF_LIGHT (float): Speed of light constant (3e8 m/s).
        num_chips (int): Number of RFSoC chips in the array.
        carrier_freq (float): Carrier frequency in Hz.
        chip_offsets (numpy.ndarray): Starting position of each chip relative to origin.
        spacing (numpy.ndarray): Absolute positions of all elements in the CHARM array.
    """

    INTRA_CHIP_SPACING = 1.62e-3  # Spacing between elements on adjacent chips
    INTER_CHIP_SPACING = 1.08e-3  # Spacing between elements on the same chip
    ELEMENT_PER_CHIP = 4
    SPEED_OF_LIGHT = 3e8

    def __init__(self, num_chips=4, carrier_freq=135e9):
        """
        Initialize the CharmBeamformer.

        Args:
            num_chips (int, optional): Number of chips in the array. Defaults to 4.
            carrier_freq (float, optional): Carrier frequency in Hz. Defaults to 135e9.
        """
        self.num_chips = num_chips
        self.carrier_freq = carrier_freq
        self.num_elements = self.num_chips * self.ELEMENT_PER_CHIP
        self.calib_mode = "MIN"
        # "MIN": Infer phase shift from min measured power
        # "MAX": Get phase shift directly from max measured power

        # Calculate position offsets for each chip
        # Chip 0 starts at 0.
        # Chip k starts at end of Chip k-1 + inter_chip_spacing
        # End of Chip k-1 relative to its start is (CHAN_PER_CHIP - 1) * intra_chip_spacing
        self.chip_offsets = np.zeros(num_chips)
        self.spacing = np.zeros(
            num_chips * self.ELEMENT_PER_CHIP)

        # Calculate offset for each chip
        for i in range(self.num_chips):
            self.chip_offsets[i] = ((self.ELEMENT_PER_CHIP - 1)
                                    * self.INTER_CHIP_SPACING + self.INTRA_CHIP_SPACING) * i

        # Calculate spacing for all elements in CHARM
        for chip_idx in range(self.num_chips):
            chip_offset = ((self.ELEMENT_PER_CHIP - 1) *
                           self.INTER_CHIP_SPACING + self.INTRA_CHIP_SPACING) * chip_idx
            for elem_idx in range(self.ELEMENT_PER_CHIP):
                self.spacing[chip_idx * self.ELEMENT_PER_CHIP +
                             elem_idx] = chip_offset + elem_idx * self.INTER_CHIP_SPACING

    def get_spacing(self):
        """
        Get the absolute positions of all elements in the CHARM array.

        Returns:
            numpy.ndarray: Array of element positions in meters.
        """
        return self.spacing

    def get_bfw(self, steering_angle_deg):
        """
        Calculate complex beamforming weights for the entire CHARM array (with calibration).

        Args:
            steering_angle_deg (float): The desired beam steering angle in degrees.

        Returns:
            numpy.ndarray: Complex weights for all elements in the array.
        """
        # Load calibration angles
        if self.calib_mode == "MAX":
            calib_file = "./bf_calib_max.txt"
        else:
            calib_file = "./bf_calib_min.txt"
        calib_deg = np.zeros(self.num_elements)

        if os.path.exists(calib_file):
            try:
                loaded_data = np.loadtxt(calib_file)
                if loaded_data.size == self.num_elements:
                    for ch in range(loaded_data.size):
                        if ch == 0:
                            continue
                        if self.calib_mode == "MAX":
                            calib_deg[ch] = loaded_data[ch]
                        else:
                            calib_deg[ch] = loaded_data[ch] + 180
                    logging.info(
                        f"Loaded calibration angles from {calib_file}: {calib_deg}")
                else:
                    logging.warning(
                        f"Warning: {calib_file} size {loaded_data.size} does not match expected {self.num_elements}. Using zeros.")
            except Exception as e:
                logging.error(f"Error loading {calib_file}: {e}. Using zeros.")
        else:
            logging.warning(
                f"Warning: {calib_file} does not exist. Using zeros.")

        # Conjugate beamforming
        lam = self.SPEED_OF_LIGHT / self.carrier_freq
        theta = np.deg2rad(steering_angle_deg)
        delta_phi = 2 * np.pi * self.get_spacing() * np.sin(theta) / lam

        # Apply phase calibration
        total_phase = delta_phi - np.deg2rad(calib_deg)

        steer_vec = np.exp(1j * total_phase)
        bf_weights = np.conj(steer_vec)

        return bf_weights

    def get_bfw_sim(self, steering_angle_deg):
        """
        Calculate complex beamforming weights for the entire CHARM array (Simulation Only - No Calibration).

        Args:
            steering_angle_deg (float): The desired beam steering angle in degrees.

        Returns:
            numpy.ndarray: Complex weights for all elements in the array.
        """
        # Conjugate beamforming
        lam = self.SPEED_OF_LIGHT / self.carrier_freq
        theta = np.deg2rad(steering_angle_deg)
        delta_phi = 2 * np.pi * self.get_spacing() * np.sin(theta) / lam

        # No phase calibration
        total_phase = delta_phi

        steer_vec = np.exp(1j * total_phase)
        bf_weights = np.conj(steer_vec)

        return bf_weights

    def get_bfw_fixpt(self, steering_angle_deg, bits=16):
        """
        Compute fixed-point weights for the entire array.

        Args:
            steering_angle_deg (float): The desired beam steering angle in degrees.
            bits (int, optional): The number of bits for fixed-point representation. Defaults to 16.

        Returns:
            tuple: A tuple (weights_real, weights_imag) where each is a numpy array of integers.
        """
        weights_float = self.get_bfw(steering_angle_deg)
        weights_real, weights_imag = self.convert_to_fix_pt(weights_float, bits)
        return weights_real, weights_imag

    def convert_to_fix_pt(self, weights, bits=16):
        # Extract real and imaginary parts
        real_part = np.real(weights)
        imag_part = np.imag(weights)

        # Scale to fixed-point range
        # For signed 16-bit: range is -32768 to 32767
        max_val = 2**(bits - 1) - 1

        # Convert to fixed-point (round to nearest integer)
        weights_real = np.round(real_part * max_val).astype(np.int16)
        weights_imag = np.round(imag_part * max_val).astype(np.int16)

        return weights_real, weights_imag

    def calculate_array_factor(self, steer_angle_deg, theta_scan_deg, simulation=False):
        """
        Calculates the array factor for a given steering angle over a range of scan angles.

        Args:
            steer_angle_deg: The angle to steer the beam towards (degrees).
            theta_scan_deg: Array of angles to evaluate the pattern at (degrees).
            simulation (bool, optional): If True, use ideal weights (no calibration). Defaults to False.

        Returns:
            af_magnitude: Magnitude of the array factor (linear scale).
        """
        # Constants
        c = self.SPEED_OF_LIGHT
        fc = self.carrier_freq
        lam = c / fc
        k = 2 * np.pi / lam

        # Get element positions
        positions = self.get_spacing()

        # Get Beamforming Weights for the steering angle
        if simulation:
            weights = self.get_bfw_sim(steer_angle_deg)
        else:
            weights = self.get_bfw(steer_angle_deg)

        # Calculate Array Factor
        # AF(theta) = sum( w_n * exp(j * k * x_n * sin(theta)) )

        theta_scan_rad = np.deg2rad(theta_scan_deg)

        # Create a matrix of phases for all scan angles and elements
        # shape: (num_angles, num_elements)
        # sin(theta) is (num_angles, 1)
        # positions is (1, num_elements)
        phase_shifts = k * np.outer(np.sin(theta_scan_rad), positions)

        # Manifold vectors for scan angles: v(theta) = exp(j * k * x * sin(theta))
        manifold_vectors = np.exp(1j * phase_shifts)

        # Multiply by weights and sum over elements
        # weights is (num_elements,)
        # result is (num_angles,)
        af = np.dot(manifold_vectors, weights)

        return np.abs(af)


def run_tests():
    """
    Run test cases for CharmBeamformer.
    """
    print("="*70)
    print("Running CharmBeamformer Test Cases")
    print("="*70)

    # --- Test CharmBeamformer ---
    print("\n[Testing CharmBeamformer]")
    charm_bf = CharmBeamformer(num_chips=2)
    print(f"\tChip offsets: {charm_bf.chip_offsets * 1e3} mm")
    print(f"\tSpacing: {charm_bf.get_spacing()}")

    for angle in [0, 30]:
        w = charm_bf.get_bfw(angle)
        print(f"\nAngle {angle}°:")
        print(f"\tWeights shape: {w.shape}")
        phases = np.angle(w, deg=True)
        print(f"\tPhases (deg): {phases}")
        if angle == 0:
            assert np.allclose(
                phases, 0.0, atol=1e-5), "Broadside phases should be 0"

    print("\n" + "="*70)
    print(f"All Tests Finished")
    print("="*70)


if __name__ == "__main__":
    run_tests()
