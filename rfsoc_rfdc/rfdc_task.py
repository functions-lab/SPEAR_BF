from rfsoc_rfdc.clocks import LMK04828ClkConfig, LMX2594ClkConfig, find_and_program_clocks
from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.rfdc import MyRFdc
import os
import logging
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class RfdcTask(OverlayTask):
    """Task for configuring RF data converters."""

    def __init__(self, overlay, debug_mode=False, board="ZCU216"):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.debug_mode = debug_mode
        rfdc_ip = overlay.rfdc.usp_rf_data_converter
        self.my_rfdc = MyRFdc(rfdc_ip, debug_mode=debug_mode)
        self.board = board
        self.set_board_rules()

    def set_board_rules(self):
        if self.board == "RFSoC4x2":
            # Mask out DAC tile #1 and #3
            self.my_rfdc.rfdc_status.dac_tile_mask_out[1] = True
            self.my_rfdc.rfdc_status.dac_tile_mask_out[3] = True
            # Mask out ADC tile #1 and #3
            self.my_rfdc.rfdc_status.adc_tile_mask_out[1] = True
            self.my_rfdc.rfdc_status.adc_tile_mask_out[3] = True

    def set_external_clocks(self):
        if self.board == "ZCU216":
            # LMK clock config
            lmk_config = LMK04828ClkConfig(
                chip="LMK04828", freq_in=10.0, freq_out=250.0, mts_pl_clk_freq=300.0, mts_pl_sysref_freq=10.0)
            # LMX clock config
            lmx_config = LMX2594ClkConfig(
                chip="LMX2594", freq_in=250.0, freq_out=ZCU216_CONFIG['RefClockForPLL'])
            # Locate clock config file directory
            config_dir = os.getcwd()
            for sub_dir in ["rfsoc_rfdc", "xrfclk", "ZCU216"]:
                config_dir = os.path.join(config_dir, sub_dir)
        elif self.board == "RFSoC4x2":
            # LMK clock config
            lmk_config = LMK04828ClkConfig(
                chip="LMK04828", freq_in=10.0, freq_out=250.0, mts_pl_clk_freq=300.0, mts_pl_sysref_freq=10.0)
            # LMX clock config
            lmx_config = LMX2594ClkConfig(
                chip="LMX2594", freq_in=250.0, freq_out=ZCU216_CONFIG['RefClockForPLL'])
            # Locate clock config file directory
            config_dir = os.getcwd()
            for sub_dir in ["rfsoc_rfdc", "xrfclk", "RFSoC4x2"]:
                config_dir = os.path.join(config_dir, sub_dir)
        else:
            raise RuntimeError(f"RFSoC board {self.board} unsupported.")

        # Program clocks
        _lmk_prop, _lmx_prop = find_and_program_clocks(
            lmk_config, lmx_config, config_dir)
        # Debug clock properties
        if self.debug_mode:
            for prop in [_lmk_prop, _lmx_prop]:
                logging.info(
                    f"{prop['chip']} freq_in {prop['freq_in']} MHz freq_out {prop['freq_out']} MHz ")
                try:
                    logging.info(
                        f"{prop['chip']} mts_pl_clk_freq {prop['mts_pl_clk_freq']} MHz mts_pl_sysref_freq {prop['mts_pl_sysref_freq']} MHz ")
                except:
                    pass

    def set_nco(self):
        # Set all DACs to DACNCO
        dac_nco_mhz = ZCU216_CONFIG['DACNCO']
        for tile in self.my_rfdc.dac_tiles:
            if self.my_rfdc.rfdc_status.get_dac_tile_enb(tile.tile_id):
                for block_id, block in enumerate(tile.blocks):
                    self.my_rfdc.config_dac_nco(tile, block_id, dac_nco_mhz)
        # Set all ADCs to ADCNCO
        adc_nco_mhz = ZCU216_CONFIG['ADCNCO']
        for tile in self.my_rfdc.adc_tiles:
            if self.my_rfdc.rfdc_status.get_adc_tile_enb(tile.tile_id):
                for block_id, block in enumerate(tile.blocks):
                    self.my_rfdc.config_adc_nco(tile, block_id, adc_nco_mhz)

    # TODO: Find a better way to handle this
    def set_tiqc_demo_freq(self):
        logging.info(f"Overwrite NCO frequency for TIQC application.")
        # Set DAC NCOs to TIQC spec
        t0 = self.my_rfdc.dac_tiles[0]
        self.my_rfdc.config_dac_nco(t0, 0, 153)
        self.my_rfdc.config_dac_nco(t0, 1, 153)
        self.my_rfdc.config_dac_nco(t0, 2, 153)
        self.my_rfdc.config_dac_nco(t0, 3, 153)

    def run(self):
        """Run the task."""
        if not self.my_rfdc.is_ready():
            # Configure external PLL clocks
            self.set_external_clocks()
            # Initialize RF data converters
            self.my_rfdc.init()
        # Config DAC/ADC to target samping rate and interp/decim factor
        self.my_rfdc.setup()
        # Set DAC/ADC NCOs
        self.set_nco()


class RfdcMultiBandTask(RfdcTask):

    def set_nco(self):
        # Additional configuration for DAC NCO
        dac_nco_mhz = ZCU216_CONFIG['DACNCO']
        dac_nco_offset = ZCU216_CONFIG['DACSampleRate'] / \
            ZCU216_CONFIG['DACInterpolationRate'] + 50
        tile = self.rfdc.dac_tiles[2]  # Use 2nd tile only
        self.rfdc.config_dac_nco(tile, 0, dac_nco_mhz)  # Set 1st DAC NCO
        for block_id in [1, 2, 3]:
            dac_nco_mhz += dac_nco_offset
            self.rfdc.config_dac_nco(tile, block_id, dac_nco_mhz)
        # Additional configuration for ADC NCO
        adc_nco_mhz = ZCU216_CONFIG['ADCNCO']
        adc_nco_offset = ZCU216_CONFIG['ADCSampleRate'] / \
            ZCU216_CONFIG['ADCInterpolationRate'] - 50
        tile = self.rfdc.adc_tiles[2]  # Use 2nd tile only
        self.rfdc.config_adc_nco(tile, 0, adc_nco_mhz)  # Set 1st ADC NCO
        for block_id in [1, 2, 3]:
            adc_nco_mhz -= adc_nco_offset
            self.rfdc.config_adc_nco(tile, block_id, adc_nco_mhz)

    def run(self):
        super().run()
        # Customly set DAC/ADC NCO
        self.set_nco()
