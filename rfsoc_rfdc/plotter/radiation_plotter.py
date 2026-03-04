import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, Union, List
from dataclasses import dataclass

from rfsoc_rfdc.dsp.charm_beamformer import CharmBeamformer
from rfsoc_rfdc.plotter.plot_format import PlotFormat


@dataclass
class RadiationPatternData:
    """
    Data class for radiation pattern measurements.
    """
    angles: Union[List[float], np.ndarray]
    powers: Union[List[float], np.ndarray]
    powers_uncalib: Union[List[float], np.ndarray, None] = None
    angles_uncalib: Union[List[float], np.ndarray, None] = None


class RadiationPlotter:
    """
    Class for plotting polar radiation patterns with simulation overlay.
    """

    def __init__(self, num_channels: int, fmt: Union[PlotFormat, None] = None, theta_offset=0):
        """
        Initialize the RadiationPlotter.

        Args:
            num_channels (int): Number of transmitting channels (e.g., 4 or 8).
            fmt (PlotFormat, optional): Formatting object. Defaults to None (uses default PlotFormat).
        """
        self.num_channels = num_channels
        self.num_chips = int(np.ceil(num_channels / 4))
        self.format = fmt if fmt else PlotFormat()
        self.FILE_NAME = f"antenna_pattern_{self.num_channels}T"
        self.theta_offset = theta_offset

    def plot_from_file(self, file_path, save_dir="."):
        """
        Load data from a text file and plot the radiation pattern.

        Args:
            file_path (str or Path): Path to the file containing angles and powers.
            save_dir (str): Directory to save the output files.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Angles and powers.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist.")

        try:
            data = np.loadtxt(file_path)
        except Exception as e:
            raise ValueError(f"Failed to load data from {file_path}: {e}")

        angles = data[:, 0]
        powers = data[:, 1]

        powers_uncalib = None
        if data.shape[1] > 2:
            powers_uncalib = data[:, 2]
            print(f"Loaded uncalibrated data from {file_path}")

        print(f"Loaded data from {file_path}")

        plot_data = RadiationPatternData(
            angles=angles,
            powers=powers,
            powers_uncalib=powers_uncalib
        )

        return self.plot(plot_data, save_dir=save_dir)

    def plot(self, data: RadiationPatternData, save_dir="."):
        """
        Plot the polar radiation pattern.
        """
        # Prepare Data
        angles_np, powers_np, powers_norm, theta = self._prepare_data(data)

        # Calculate Simulation
        sim_af_db = self._pattern_sim(angles_np)

        # Setup Plot
        fig = plt.figure(figsize=(self.format.figSizeX, self.format.figSizeY))
        ax = plt.subplot(111, projection='polar')

        # Plot simulation results
        ax.plot(theta, sim_af_db, color='b', linestyle='--',
                linewidth=self.format.lineWidth, label='Simulated (Ideal)', zorder=1)
        # Plot calibrated measurement
        ax.plot(theta, powers_norm, color='g',
                linewidth=self.format.lineWidth, label='Measured (Calibrated)', zorder=3)
        # Plot uncalibrated measurement
        if data.angles_uncalib is None:
            angles_uncalib_np = angles_np + self.theta_offset
        else:
            angles_uncalib_np = np.array(
                data.angles_uncalib) + self.theta_offset

        theta_uncalib = np.deg2rad(angles_uncalib_np)
        powers_uncalib_np = np.array(data.powers_uncalib)
        # Normalize using the same shift as calibrated results
        powers_uncalib_norm = powers_uncalib_np - np.max(powers_np)

        ax.plot(theta_uncalib, powers_uncalib_norm, color='r', linestyle='-',
                linewidth=1, label='Measured (Uncalibrated)', zorder=2)

        # Configure Axes
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)  # Clockwise
        ax.set_thetamin(-90)
        ax.set_thetamax(90)
        ax.set_thetagrids(np.arange(-90, 91, 30))
        ax.grid(True, zorder=0)
        # Apply Tick Format
        ax.tick_params(axis='x', labelsize=self.format.fontLegend / 2)
        ax.tick_params(axis='y', labelsize=self.format.fontLegend / 2)
        # Dynamic Limits
        min_p = np.min(powers_norm)
        if powers_uncalib_norm is not None:
            min_p = min(min_p, np.min(powers_uncalib_norm))
        # Floor to nearest multiple of 10
        r_min = -40  # np.floor((min_p - 10) / 10) * 10
        r_max = 0
        ax.set_ylim(r_min, r_max)
        ax.set_yticks(np.arange(r_min, r_max + 1, 10))

        # ax.legend(loc='center', bbox_to_anchor=(0.5, -0.01),
        #           fontsize=self.format.fontLegend / 2, framealpha=1.0)

        # Save Results
        self._save_results(save_dir, angles_np,
                           powers_np, data.powers_uncalib)

        try:
            plt.show()
        except Exception:
            pass

        return angles_np, powers_np

    def _prepare_data(self, data: RadiationPatternData):
        angles_np = np.array(data.angles)
        powers_np = np.array(data.powers)
        # Normalize measured power
        powers_norm = powers_np - np.max(powers_np)
        # Convert to radians for polar plot
        theta = np.deg2rad(angles_np + self.theta_offset)
        return angles_np, powers_np, powers_norm, theta

    def _pattern_sim(self, angles_np):
        sim_bf = CharmBeamformer(num_chips=self.num_chips)
        sim_af = sim_bf.calculate_array_factor(
            steer_angle_deg=0, theta_scan_deg=angles_np, simulation=True)
        sim_af_norm = sim_af / np.max(sim_af)
        return 20 * np.log10(sim_af_norm + 1e-12)

    def _save_results(self, save_dir, angles_np, powers_np, powers_uncalib):
        save_path = Path(save_dir) / self.FILE_NAME

        plt.savefig(f"{save_path}_polar.png", dpi=300, bbox_inches='tight')

        if powers_uncalib is not None and len(powers_uncalib) == len(powers_np):
            saved_results = np.vstack((angles_np, powers_np, powers_uncalib)).T
        else:
            saved_results = np.vstack((angles_np, powers_np)).T

        np.savetxt(f"{save_path}.txt", saved_results)

        print(f"Saved plot to {save_path}_polar.png")
        print(f"Saved measurement data to {save_path}.txt")


def main():
    parser = argparse.ArgumentParser(
        description='Plot antenna radiation pattern from a file.')
    parser.add_argument('file_path', type=str,
                        help='Path to the file containing angles and powers.')
    parser.add_argument('--num_channels', type=int, default=4,
                        help='Number of transmitting channels (default: 4).')
    parser.add_argument('--save_dir', type=str, default='.',
                        help='Directory to save the output files (default: current directory).')
    args = parser.parse_args()

    plotter = RadiationPlotter(num_channels=args.num_channels)
    try:
        plotter.plot_from_file(
            args.file_path, save_dir=args.save_dir)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
