import time
import numpy as np
import matplotlib.pyplot as plt
import logging
from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.transmitter.single_ch_tone_tx_task import SingleChToneTxTask
from rfsoc_rfdc.transmitter.multi_ch_tone_tx_task import MultiChToneTxTask

from rfsoc_rfdc.receiver.single_ch_rx_task import SingleChRxTask
from rfsoc_rfdc.receiver.single_ch_tone_rx_task import SingleChToneRxTask
from rfsoc_rfdc.receiver.multi_ch_tone_rx_task import MultiChToneRxTask
from rfsoc_rfdc.beamformer_task import BeamformerTxTask


class ArrayCalibTask(OverlayTask):
    """
    Task to perform array calibration for beamforming.
    Orchestrates SingleChToneTxTask, BeamformerTxTask, and SingleChRxTask/SingleChToneRxTask.
    """

    def __init__(self, overlay, num_tx_ch=1, num_dacs=4, num_rx_ch=1, num_adcs=1, save_dir="."):
        super().__init__(overlay, name="ArrayCalibTask")
        self.num_tx_ch = num_tx_ch  # Number of TX DSP
        self.num_dacs = num_dacs  # Number of DACs used
        self.num_rx_ch = num_rx_ch  # Number of RX DSP
        self.num_adcs = num_adcs  # Number of ADCs used
        self.save_dir = save_dir
        self.fine_search_method = "MIN"  # "MIN", "MAX"
        self.coarse_step = 15
        self.fine_step = 1
        self.target_tone_freq = 100  # Mhz

        # Beamforming
        self.tx_bf_task = BeamformerTxTask(
            overlay, num_channels=num_dacs)
        # TX tone generation
        if self.num_tx_ch > 1:
            self.tx_tone = MultiChToneTxTask(
                overlay, channel_count=self.num_tx_ch, dp_vect_dim=4, tone_freq_mhz=self.target_tone_freq)
            # dp_vect_dim = 4 only fits rfsoc_rfdc_v47_8t2r_bf design, set this value according to your hardware design
        else:
            self.tx_tone = SingleChToneTxTask(
                overlay, tone_freq_mhz=self.target_tone_freq)
        # RX tone measurement
        rx_tone_buff_size = 2**14
        if self.num_rx_ch > 1:
            self.tone_pwr_task = MultiChToneRxTask(
                overlay, channel_count=self.num_rx_ch,
                dp_vect_dim=4, buff_size=rx_tone_buff_size * self.num_rx_ch)
            # dp_vect_dim = 4 only fits rfsoc_rfdc_v47_8t2r_bf design, set this value according to your hardware design
            self.tone_pwr_task._channel_factory()
        else:
            self.tone_pwr_task = SingleChToneRxTask(
                overlay, buff_size=rx_tone_buff_size)

    def _get_power(self):
        """Helper to capture data and measure tone power."""
        avg_count = 5
        avg_pwr = []
        # Multiple captures to clear out FIFO from previous settings
        for i in range(2):
            self.tone_pwr_task.rx_ch.transfer()

        for _ in range(avg_count):
            self.tone_pwr_task.rx_ch.transfer()
            data = self.tone_pwr_task.rx_ch.data
            if self.num_rx_ch > 1:
                # Decompose multi-channel data and use the first channel (index 0)
                mch_data = self.tone_pwr_task.mch_mem_layout.dec_layout(data)
                ch_data = mch_data[0]
                pwr = self.tone_pwr_task.rx_analyzers.proc_rx(ch_data)
            else:
                pwr = self.tone_pwr_task.rx_analyzer.proc_rx(data)
            avg_pwr.append(pwr)

        return np.average(avg_pwr)

    def _get_target_ch_pwr(self, angle, calib_ch):
        """Helper to measure power for a specific angle and channel."""
        # Apply phase shift for calibration
        self.tx_bf_task.uncalib_steer(angle)

        # Block all channels except CH0 and the current calibration channel
        block_list = [True] * self.num_dacs
        block_list[0] = False
        block_list[calib_ch] = False
        self.tx_bf_task.block_channel(block_list)

        return self._get_power()

    def sweep_pattern(self, start_angle, end_angle, step, calibrated=True):
        """Sweep steering angles and measure power."""

        angles = range(start_angle, end_angle + 1, step)
        powers = []
        for angle in angles:
            if self._stop_event.is_set():
                break

            if calibrated:
                self.tx_bf_task.calib_steer(angle)
            else:
                self.tx_bf_task.uncalib_steer(angle)

            p = self._get_power()
            logging.info(f"Steering angle {angle}°, got power {p:.2f} dBm/MHz")
            powers.append(p)
        return list(angles), powers

    def run(self):
        logging.info("Starting Array Calibration Task...")

        # Start the TX tone generation (runs in its own thread)
        self.tx_tone.start()
        time.sleep(3)

        calib_results = {}

        for calib_ch in range(self.num_dacs):

            if self._stop_event.is_set():
                break

            # Channel 0 is the reference, so we calibrate others against it
            if calib_ch == 0:
                continue

            # Calibration warm up
            for i in range(5):
                p = self._get_target_ch_pwr(0, calib_ch)

            calib_results[calib_ch] = {'angles': [], 'powers': []}
            logging.info(
                f"Calibrating Channel {calib_ch} -> Channel 0")

            # Container for (angle, power) tuples
            # Using a set for angles to avoid re-measuring same points
            measurements = []
            visited_angles = set()

            def do_measure(a):
                """Measure at angle `a` unless already visited. Returns measured power or None."""
                norm_a = a % 360
                if norm_a in visited_angles:
                    return None

                p = self._get_target_ch_pwr(norm_a, calib_ch)
                logging.info(
                    f"Calib CH{calib_ch} Angle {norm_a}°: Measured Power = {p:.2f}")
                measurements.append((norm_a, p))
                visited_angles.add(norm_a)
                return p

            # --- Coarse Search ---
            # Sweep angles from 0 to 360 in steps of self.coarse_step
            for angle in range(0, 360, self.coarse_step):
                if self._stop_event.is_set():
                    break
                _ = do_measure(angle)

            # Find angle with maximum power from coarse search
            if not measurements:
                continue

            target_angle = None
            if self.fine_search_method == "MAX":
                best_pair = max(measurements, key=lambda x: x[1])
                target_angle = best_pair[0]
            elif self.fine_search_method == "MIN":
                best_pair = min(measurements, key=lambda x: x[1])
                target_angle = best_pair[0]

            if target_angle is not None:
                # --- Fine Search ---
                # Search +/- 30 degrees around target with step self.fine_step
                start_angle = target_angle - 30
                end_angle = target_angle + 30

                for angle in range(start_angle, end_angle + 1, self.fine_step):
                    if self._stop_event.is_set():
                        break
                    do_measure(angle)

            # Sort measurements by angle for correct plotting
            measurements.sort(key=lambda x: x[0])

            # Store results
            calib_results[calib_ch]['angles'] = [m[0] for m in measurements]
            calib_results[calib_ch]['powers'] = [m[1] for m in measurements]

        # Save results
        self.save_results(calib_results)

        logging.info("Array Calibration Task Finished.")
        self._stop_event.set()
        self.task_state = TASK_STATE["STOP"]

        # Stop the TX tone generation
        self.tx_tone.stop()
        del self.tx_bf_task
        del self.tx_tone
        del self.tone_pwr_task

    def save_results(self, calib_results):
        """Analyze results, save plots and the calibration npy file."""
        max_power_angles = np.zeros(self.num_dacs)
        min_power_angles = np.zeros(self.num_dacs)

        for ch, data in calib_results.items():
            angles = np.array(data['angles'])
            powers = np.array(data['powers'])

            plt.figure()
            plt.plot(angles, powers, marker='o')
            plt.title(f'Calibration CH {ch} to CH0')
            plt.xlabel('Angle (degrees)')
            # Add unit to label for clarity
            plt.ylabel('Measured Power (dBm/MHz)')
            plt.grid(True)

            # Find max power angle
            max_power_idx = np.argmax(powers)
            angle_at_max_power = angles[max_power_idx]
            max_power_value = powers[max_power_idx]

            # Find min power angle (Null point)
            min_power_idx = np.argmin(powers)
            angle_at_min_power = angles[min_power_idx]
            min_power_value = powers[min_power_idx]

            # Set fixed y-axis unit scale to 1
            # Determine the range for y-axis ticks
            y_min = np.floor(min(powers) - 1) if powers.size > 0 else 0
            y_max = np.ceil(max(powers) + 1) if powers.size > 0 else 1

            # Ensure a minimum range if all powers are very close
            if y_max - y_min < 2:
                y_max = y_min + 2

            plt.ylim(y_min, y_max)
            # +1 to include the max tick
            plt.yticks(np.arange(y_min, y_max + 1, 1))

            max_power_angles[ch] = angle_at_max_power
            min_power_angles[ch] = angle_at_min_power

            # Mark max and min on plot
            plt.scatter(angle_at_max_power, max_power_value, color='red', s=100, marker='X',
                        label=f'Max Power at {angle_at_max_power}°')
            plt.scatter(angle_at_min_power, min_power_value, color='blue', s=100, marker='X',
                        label=f'Min Power at {angle_at_min_power}°')
            plt.legend()

            # Save plot
            plot_path = f"{self.save_dir}/calib_result_{self.num_dacs}T_ch{ch}.png"
            plt.savefig(plot_path)
            plt.close()
            logging.info(f"Saved calibration plot for CH{ch} to {plot_path}")

        logging.info(
            "Angles corresponding to the largest power for each channel:")
        logging.info(max_power_angles)
        logging.info(
            "Angles corresponding to the smallest power for each channel:")
        logging.info(min_power_angles)

        # Save the calibration file (null angles)
        calib_fname = f"{self.save_dir}/bf_calib_max.txt"
        np.savetxt(calib_fname, max_power_angles)
        calib_fname = f"{self.save_dir}/bf_calib_min.txt"
        np.savetxt(calib_fname, min_power_angles)

        # Save the full calibration results dictionary
        full_calib_fname = f"{self.save_dir}/calib_result_{self.num_dacs}T.npy"
        np.save(full_calib_fname, calib_results, allow_pickle=True)
