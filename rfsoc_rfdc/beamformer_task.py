from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.dsp.charm_beamformer import CharmBeamformer
import numpy as np
import logging
from pynq import allocate

"""
The spacing between the elements on the same chip is 1.08mm, while the spacing between neighboring elements on different chips is 1.62mm. 
"""


class BeamformerTask(OverlayTask):
    """Base task for beam sweeping with beamforming weights on the FPGA."""

    def __init__(self, overlay, num_channels, element_spacing=1.08e-3,
                 carrier_freq=135e9, debug_mode=False):
        """
        Initialize the BeamformerTask.

        Parameters
        ----------
        overlay : RFSoCOverlay
            The RFSoC overlay instance to operate on.
        num_channels : int
            Number of beamforming elements.
        element_spacing : float
            Spacing between adjacent elements in meters.
        carrier_freq : float
            Carrier frequency in Hz.
        debug_mode : bool
            Enable debug logging.
        """
        super().__init__(overlay, name="BeamformerTask")
        self.debug_mode = debug_mode
        self.num_channels = num_channels

        # Create beamformer instance
        num_chips = int(np.ceil(num_channels / 4))
        self.beamformer = CharmBeamformer(num_chips=num_chips)

        # DMA and buffer to be set by child classes
        self.bfw_dma = None
        self.bfw_buff = allocate(shape=(
            num_channels * 2,), dtype=np.int16, target=self.ol.PSDDR)  # I and Q for each channel

    def block_channel(self, block_list):
        if len(block_list) != self.num_channels:
            logging.warning(
                f"block_list length {len(block_list)} truncated to match num_channels ({self.num_channels})")
            block_list = block_list[0:self.num_channels]

        # Get current weights
        bfw_buff_new = allocate(shape=(
            self.num_channels * 2,), dtype=np.int16, target=self.ol.PSDDR)

        try:
            bfw_buff_new[:] = self.bfw_buff[:]

            # Block out specific channels
            for ch_id in range(self.num_channels):
                if block_list[ch_id]:
                    bfw_buff_new[2 * ch_id] = 0
                    bfw_buff_new[2 * ch_id + 1] = 0

            bfw_real = bfw_buff_new[::2]
            bfw_imag = bfw_buff_new[1::2]

            if self.debug_mode:
                for ch_idx, blocked in enumerate(block_list):
                    if blocked:
                        logging.info(f"Blocking channel {ch_idx}")

            self.__write_bfw(bfw_real, bfw_imag)
        finally:
            bfw_buff_new.close()

    def close(self):
        """Release beamforming weights buffer"""
        if hasattr(self, 'bfw_buff') and self.bfw_buff is not None:
            if hasattr(self.bfw_buff, 'close'):
                self.bfw_buff.close()
            self.bfw_buff = None

    def __del__(self):
        self.close()

    def calib_steer(self, steering_angle_deg):
        """
        Update beamforming weights to FPGA for the specified steering angle (with calibration).
        """
        bfw_real, bfw_imag = self.beamformer.get_bfw_fixpt(
            steering_angle_deg=steering_angle_deg
        )
        if self.debug_mode:
            logging.info(f"Update weights for {steering_angle_deg}° steering")

        self.__write_bfw(bfw_real, bfw_imag)

    def uncalib_steer(self, angle):
        """
        Steer the beamformer to a specified angle without calibration.
        """
        ang2phase = angle / 180 * np.pi
        phase = np.zeros(self.num_channels) + ang2phase
        phase[0] = 0
        weights = np.exp(1j * phase)

        w_real, w_imag = self.beamformer.convert_to_fix_pt(weights=weights)

        if self.debug_mode:
            logging.info(f"Update weights for relative shift at {angle}°")

        self.__write_bfw(w_real, w_imag)

    def __bfw_truncated(self, bfw_real, bfw_imag):
        if len(bfw_real) > self.num_channels:
            logging.warning(
                f"bfw_real length {len(bfw_real)} truncated to match num_channels ({self.num_channels})")
            bfw_real = bfw_real[0:self.num_channels]
            bfw_imag = bfw_imag[0:self.num_channels]

        return bfw_real, bfw_imag

    def __write_bfw(self, bfw_real, bfw_imag):
        if self.bfw_dma is None:
            raise RuntimeError(
                "bfw_dma is not initialized. Use BeamformerTxTask or BeamformerRxTask.")

        bfw_real, bfw_imag = self.__bfw_truncated(bfw_real, bfw_imag)

        if self.debug_mode:
            logging.info(
                f"  Real (float): {[float(w) for w in bfw_real]}")
            logging.info(
                f"  Imag (float): {[float(w) for w in bfw_imag]}")
            logging.info(
                f"  Real (hex): {['0x{:04X}'.format(int(w) & 0xFFFF) for w in bfw_real]}")
            logging.info(
                f"  Imag (hex): {['0x{:04X}'.format(int(w) & 0xFFFF) for w in bfw_imag]}")

        self.bfw_buff[::2] = bfw_real
        self.bfw_buff[1::2] = bfw_imag

        self.bfw_dma.transfer(self.bfw_buff)

    def run(self):
        """
        Run the beamformer task (performs a default sweep).
        """
        if self.debug_mode:
            logging.info(f"Running {self.name}")

        for angle in range(-90, 91, 5):
            self.calib_steer(angle)

        if self.debug_mode:
            logging.info(f"{self.name} completed")

    def __repr__(self):
        return f"{self.name}({self.beamformer})"


class BeamformerTxTask(BeamformerTask):
    """Beamformer task for TX."""

    def __init__(self, overlay, num_channels=4, element_spacing=1.08e-3, carrier_freq=135e9, debug_mode=False):
        super().__init__(overlay, num_channels, element_spacing, carrier_freq, debug_mode)
        self.name = "BeamformerTxTask"
        self.bfw_dma = self.ol.tx_bfw_dma.sendchannel


class BeamformerRxTask(BeamformerTask):
    """Beamformer task for RX."""

    def __init__(self, overlay, num_channels=4, element_spacing=1.08e-3, carrier_freq=135e9, debug_mode=False):
        super().__init__(overlay, num_channels, element_spacing, carrier_freq, debug_mode)
        self.name = "BeamformerRxTask"
        self.bfw_dma = self.ol.rx_bfw_dma.sendchannel
