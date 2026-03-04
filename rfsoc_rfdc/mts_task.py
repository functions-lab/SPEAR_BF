import time
import logging
from rfsoc_rfdc.overlay_task import OverlayTask


class MtsTask(OverlayTask):

    def __init__(self, overlay, board="ZCU216", debug_mode=False):
        super().__init__(overlay, name="MtsTask")
        self.rfdc = self.ol.rfdc.usp_rf_data_converter
        self.mts_monitor = self.ol.MTS_block.MTS_clk_wiz
        self.debug_mode = debug_mode
        self.board = board
        self.CLOCKWIZARD_LOCK_ADDRESS = 0x0004
        self.CLOCKWIZARD_RESET_ADDRESS = 0x0000
        self.CLOCKWIZARD_RESET_TOKEN = 0x000A
        if self.board == "RFSoC4x2":
            # RFSoC4x2 has only 2 DAC and 2 ADC tiles
            self.ACTIVE_DAC_TILES = 0b0101
            self.ACTIVE_ADC_TILES = 0b0101
            self.DAC_REF_TILE = 2
            self.ADC_REF_TILE = 2
        else:
            self.ACTIVE_DAC_TILES = 0b1111
            self.ACTIVE_ADC_TILES = 0b1111
            self.DAC_REF_TILE = 1
            self.ADC_REF_TILE = 1
        # MTS related
        self.mts_latency_min = 16
        # DAC latency is fixed to 16, please refer to PG269 https://docs.amd.com/r/en-US/pg269-rf-data-converter/Deterministic-Multi-Tile-Synchronization-API-Use
        self.dac_latency_margin = 16
        # ADC latency must be a multiple of the number of FIFO read-words times the decimation factor, please refer to PG269 https://docs.amd.com/r/en-US/pg269-rf-data-converter/Deterministic-Multi-Tile-Synchronization-API-Use
        self.adc_latency_margin = 16

    def debug(self):
        """Print debug information"""
        mts_attr = ['RefTile', 'Tiles', 'Target_Latency',
                    'Offset', 'Latency', 'Marker_Delay', 'SysRef_Enable']

        for attr in mts_attr:
            val = getattr(self.rfdc.mts_dac_config, attr, None)
            if attr == "Offset" or attr == "Latency":
                for i in range(4):
                    logging.info(
                        f"DAC MTS {attr} Tile[{i}] : {val[i]}")
            else:
                logging.info(
                    f"DAC MTS {attr} : {val}")

        for attr in mts_attr:
            val = getattr(self.rfdc.mts_adc_config, attr, None)
            if attr == "Offset" or attr == "Latency":
                for i in range(4):
                    logging.info(
                        f"ADC MTS {attr} Tile[{i}] : {val[i]}")
            else:
                logging.info(
                    f"ADC MTS {attr} : {val}")

    def run(self):
        """Initialize MTS"""
        try:
            self.init_tile_sync()
        except ValueError as e:
            logging.warning(f"{e}")

        if self.debug_mode:
            self.debug()
        # Verify PL_CLK and PL_SYSREF are synced
        self.verify_clock_tree()

        # Get max latency for DACs and ADCs
        dac_max_latency, adc_max_latency = self.get_max_latency()
        # Add fixed margin for target latency
        dac_target = dac_max_latency + self.dac_latency_margin
        adc_target = adc_max_latency + self.adc_latency_margin

        logging.info(f"DAC target latency: {dac_target}")
        logging.info(f"ADC target latency: {adc_target}")
        # Sync to target latency
        self.sync_tiles(dac_target_latency=dac_target,
                        adc_target_latency=adc_target)

    def get_max_latency(self):
        # Calculate target latency
        dac_latencies = [self.rfdc.mts_dac_config.Latency[i] for i in range(4)]
        adc_latencies = [self.rfdc.mts_adc_config.Latency[i]
                         for i in range(4)]

        dac_max_latency = max(dac_latencies)
        adc_max_latency = max(adc_latencies)

        logging.info(f"DAC max latency: {dac_max_latency}")
        logging.info(f"ADC max latency: {adc_max_latency}")

        return dac_max_latency, adc_max_latency

    def sync_tiles(self, dac_target_latency=-1, adc_target_latency=-1):
        """ Configures RFSoC MTS alignment"""
        latency_min = self.mts_latency_min
        if dac_target_latency < latency_min and dac_target_latency != -1:
            raise RuntimeError(
                f"DAC target latency {dac_target_latency} shall be >= than {latency_min}.")
        if adc_target_latency < latency_min and adc_target_latency != -1:
            raise RuntimeError(
                f"ADC target latency {dac_target_latency} shall be >= than {latency_min}.")

        # Set which RF tiles use MTS and turn MTS off
        if self.ACTIVE_DAC_TILES > 0:
            self.rfdc.mts_dac_config.Tiles = self.ACTIVE_DAC_TILES
            self.rfdc.mts_dac_config.SysRef_Enable = 1
            self.rfdc.mts_dac_config.Target_Latency = dac_target_latency
            self.rfdc.mts_dac()
        else:
            self.rfdc.mts_dac_config.Tiles = 0x0
            self.rfdc.mts_dac_config.SysRef_Enable = 0

        if self.ACTIVE_ADC_TILES > 0:
            self.rfdc.mts_adc_config.Tiles = self.ACTIVE_ADC_TILES
            self.rfdc.mts_adc_config.SysRef_Enable = 1
            self.rfdc.mts_adc_config.Target_Latency = adc_target_latency
            self.rfdc.mts_adc()
        else:
            self.rfdc.mts_adc_config.Tiles = 0x0
            self.rfdc.mts_adc_config.SysRef_Enable = 0

    def init_tile_sync(self):
        """Resets the MTS alignment engine"""
        # Turn only one tile on first sync
        self.rfdc.mts_dac_config.RefTile = self.DAC_REF_TILE
        self.rfdc.mts_adc_config.RefTile = self.ADC_REF_TILE
        self.rfdc.mts_dac_config.Tiles = 0b0001
        self.rfdc.mts_adc_config.Tiles = 0b0001
        # DAC tile distributing reference clock
        self.rfdc.mts_dac_config.SysRef_Enable = 1
        self.rfdc.mts_adc_config.SysRef_Enable = 1
        self.rfdc.mts_dac_config.Target_Latency = -1
        self.rfdc.mts_adc_config.Target_Latency = -1
        self.rfdc.mts_dac()
        self.rfdc.mts_adc()
        time.sleep(0.1)

        # Reset MTS ClockWizard MMCM - refer to PG065
        self.mts_monitor.mmio.write_reg(
            self.CLOCKWIZARD_RESET_ADDRESS, self.CLOCKWIZARD_RESET_TOKEN)
        time.sleep(0.1)
        # Reset only user selected DAC tiles
        bitvector = self.ACTIVE_DAC_TILES
        for n in range(4):
            if (bitvector & 0x1):
                self.rfdc.dac_tiles[n].Reset()
            bitvector = bitvector >> 1
        # Reset ADC FIFO of only user selected tiles - restarts MTS engine
        for toggleValue in range(0, 1):
            bitvector = self.ACTIVE_ADC_TILES
            for n in range(4):
                if (bitvector & 0x1):
                    self.rfdc.adc_tiles[n].SetupFIFOBoth(toggleValue)
                bitvector = bitvector >> 1

    def verify_clock_tree(self):
        """ Verify the PL and PL_SYSREF clocks are active by verifying an MMCM is in the LOCKED state"""
        lock_status = self.mts_monitor.mmio.read(
            self.CLOCKWIZARD_LOCK_ADDRESS)  # reads the LOCK register
        # the ClockWizard AXILite registers are NOT fully mapped: refer to PG065
        if (lock_status != 1):
            raise Exception(
                "The MTS clock has failed to LOCK. Please verify MTS configuration")
        else:
            logging.info(f"The MTS clock is LOCK on successfully")
