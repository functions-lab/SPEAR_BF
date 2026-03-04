from rfsoc_rfdc.dsp.detection import Detection
import numpy as np
import logging


class RadarDetection(Detection):
    """
    Child class of Detection to support returning packet indices for radar applications.
    """

    def proc_rx(self, wave_rx):
        """
        Detects preamble in the received packet and returns the packet
        along with its absolute start and end indices in the input waveform.
        """
        # Call the parent's proc_rx method to perform the detection logic
        # and store the relevant internal attributes.
        packet_rx, snr, cfo = super().proc_rx(wave_rx)

        # Check if detection was successful
        if packet_rx is None:
            return None, np.nan, np.nan, -1, -1

        # Retrieve the internal attributes stored by the parent proc_rx
        # These attributes (_last_offset_packet, _last_search_len) were added
        # to the parent Detection class specifically for this purpose.
        offset_packet = self._last_offset_packet
        search_len = self._last_search_len

        # Calculate absolute indices based on the original wave_rx length
        # and the search_len (which was the length of wave_rx_search)
        abs_start_index = len(wave_rx) - search_len + offset_packet
        abs_end_index = abs_start_index + self.packet_len

        return packet_rx, snr, cfo, abs_start_index, abs_end_index
