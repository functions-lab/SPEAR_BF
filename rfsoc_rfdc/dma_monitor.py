from abc import ABC, abstractmethod
import pynq
from pynq import DefaultIP
import time
import logging


class DmaMonitor(ABC):
    def __init__(self, dma_ip, fifo_count_ip):
        # DMA IP core instance
        self.dma = dma_ip
        # Configure FIFO count IP core
        self.fifo_count = fifo_count_ip
        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

    def get_fifo_count(self):
        return self.fifo_count.read()

    def get_debug_info(self):
        return self.dma.register_map

    @abstractmethod
    def transfer(self, buffer):
        pass

    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class HwTriggerDmaBase(DefaultIP):

    MASK_32b = 0xFFFFFFFF  # 32-bit binary mask
    # Maximum allowed number of bytes (2^23B = 8MB) to transfer for AXI Data Mover
    AXI_DATA_MOVER_MAX_BTT = 2 ** 22  # BTT field can address at most 23 bits
    MAX_16b_ARR_SIZE = int(AXI_DATA_MOVER_MAX_BTT / 2)  # Given 16b = 2 bytes

    def __init__(self, description, fsm_lut, cmd_lut):
        super().__init__(description=description)
        self._FSM_LUT = fsm_lut
        self._CMD_LUT = cmd_lut

    @property
    def _cmd(self):
        return self.read(0x00)

    @_cmd.setter
    def _cmd(self, value):
        self.write(0x00, value)

    @property
    def _start_addr_upper(self):
        return self.read(0x04)

    @_start_addr_upper.setter
    def _start_addr_upper(self, value):
        self.write(0x04, value)

    @property
    def _start_addr_lower(self):
        return self.read(0x08)

    @_start_addr_lower.setter
    def _start_addr_lower(self, value):
        self.write(0x08, value)

    @property
    def _btt(self):
        return self.read(0x0C)

    @_btt.setter
    def _btt(self, value):
        self.write(0x0C, value)

    @property
    def _state(self):
        return self.read(0x10)

    def state(self):
        return self._FSM_LUT[self._state]

    @property
    def _end_addr_upper(self):
        return self.read(0x14)

    @_end_addr_upper.setter
    def _end_addr_upper(self, value):
        self.write(0x14, value)

    @property
    def _end_addr_lower(self):
        return self.read(0x18)

    @_end_addr_lower.setter
    def _end_addr_lower(self, value):
        self.write(0x18, value)

    @property
    def _duty_cyc_target(self):
        return self.read(0x1C)

    @_duty_cyc_target.setter
    def _duty_cyc_target(self, cycles):
        self.write(0x1C, cycles)

    def _config(self, start_addr, end_addr):
        saddr_lower, saddr_upper = start_addr & self.MASK_32b, (
            start_addr >> 32) & self.MASK_32b
        eaddr_lower, eaddr_upper = end_addr & self.MASK_32b, (
            end_addr >> 32) & self.MASK_32b
        memory_region = (end_addr - start_addr)
        fraction_btt = 2**22

        if memory_region > self.AXI_DATA_MOVER_MAX_BTT:
            # print(f"Mem size {self.AXI_DATA_MOVER_MAX_BTT} bytes, broken down into {fraction_btt} bytes chunks")
            btt = fraction_btt
        else:
            btt = memory_region

        self._start_addr_lower = saddr_lower
        self._start_addr_upper = saddr_upper
        self._end_addr_lower = eaddr_lower
        self._end_addr_upper = eaddr_upper
        self._btt = btt

    def get_debug_info(self):
        start_addr = ((self._start_addr_upper & self.MASK_32b) <<
                      32) | (self._start_addr_lower & self.MASK_32b)
        end_addr = ((self._end_addr_upper & self.MASK_32b) <<
                    32) | (self._end_addr_lower & self.MASK_32b)
        btt = self._btt
        duty_cyc = self._duty_cyc_target
        debug_info = f"start_addr = {start_addr}, btt = {btt}, end_addr = {end_addr}, duty_cyc_target = {duty_cyc}, state = {self.state()}"
        return debug_info

    def __del__(self):
        self.stop()


class HwTriggerDmaV1(HwTriggerDmaBase):
    """
    Hardware Trigger DMA driver v1.0 allows user to set the start and end address of a large DMA transfer. The DMA transfer will be broke down into BTT bytes triggered by an external TTL signal until the end address is reached.
    """

    def __init__(self, description):
        self.iq_samples_per_cyc = 8
        super().__init__(description, fsm_lut=['S_IDLE', 'S_HALT', 'S_HALT_RST', 'S_ERROR', 'S_DMA_AXIS',
                                               'S_DMA_WAIT', 'S_EXT_TRIG', 'S_DMA_DONE', 'S_DUTY', 'S_CHECK'], cmd_lut={'IDLE': 0x0, 'EXT_TRIG': 0x1, 'DMA': 0x2, 'STREAM': 0x3, 'DUTY': 0x4, 'RST': 0x5})

    bindto = ['user.org:user:hw_trigger_dma:1.0']

    def transfer(self, buffer):
        start_addr = buffer.physical_address
        end_addr = start_addr + buffer.nbytes
        self._config(start_addr=start_addr, end_addr=end_addr)
        self._cmd = self._CMD_LUT['DMA']
        while True:
            if self.state() == 'S_DMA_DONE':
                break
            else:
                time.sleep(1)
        self._cmd = self._CMD_LUT['IDLE']

    def ttl_transfer(self, buffer):
        start_addr = buffer.physical_address
        end_addr = start_addr + buffer.nbytes

        self._start_addr_lower = start_addr & self.MASK_32b
        self._start_addr_upper = (start_addr >> 32) & self.MASK_32b
        self._end_addr_lower = end_addr & self.MASK_32b
        self._end_addr_upper = (end_addr >> 32) & self.MASK_32b
        self._btt = buffer.nbytes

        self._cmd = self._CMD_LUT['EXT_TRIG']
        while True:
            if self.state() == 'S_DMA_DONE':
                break
            else:
                time.sleep(1)
        self._cmd = self._CMD_LUT['IDLE']

    def stream(self, buffer, duty_cycle=100):
        start_addr = buffer.physical_address
        end_addr = start_addr + buffer.nbytes
        self._config(start_addr=start_addr, end_addr=end_addr)
        if duty_cycle != 100:  # Duty cycling
            ratio_fp = (100 - duty_cycle) / duty_cycle
            dma_time_in_cyc = int(buffer.size / self.iq_samples_per_cyc)
            self._duty_cyc_target = int(ratio_fp * dma_time_in_cyc)
            self._cmd = self._CMD_LUT['DUTY']
        else:
            self._cmd = self._CMD_LUT['STREAM']

    def stop(self):
        self._config(0, 0)  # Reset address
        self._cmd = self._CMD_LUT['RST']
        self._cmd = self._CMD_LUT['IDLE']


class StreamingDmaBase(DefaultIP):
    """
    This class serves as a base class for StreamingDma. StreamingDma uses a custom IP to control the Xilins's AXI Data Mover IP.
    """
    MASK_32b = 0xFFFFFFFF  # 32-bit binary mask
    # Maximum allowed number of bytes (2^23B = 8MB) to transfer for AXI Data Mover
    MAX_BTT = 0x7FFFFF

    def __init__(self, description, fsm_lut):
        super().__init__(description=description)
        self._FSM_LUT = fsm_lut

    @property
    def _cmd(self):
        return self.read(0x00)

    @_cmd.setter
    def _cmd(self, value):
        self.write(0x00, value)

    @property
    def _base_addr_upper(self):
        return self.read(0x04)

    @_base_addr_upper.setter
    def _base_addr_upper(self, value):
        self.write(0x04, value)

    @property
    def _base_addr_lower(self):
        return self.read(0x08)

    @_base_addr_lower.setter
    def _base_addr_lower(self, value):
        self.write(0x08, value)

    @property
    def _btt(self):
        return self.read(0x0C)

    @_btt.setter
    def _btt(self, value):
        self.write(0x0C, value)

    @property
    def _state(self):
        return self.read(0x10)

    def state(self):
        return self._FSM_LUT[self._state]

    def _config(self, addr, nbytes):
        self._base_addr_lower = addr & self.MASK_32b
        self._base_addr_upper = (addr >> 32) & self.MASK_32b
        if nbytes > self.MAX_BTT:
            raise ValueError(
                f"Number of bytes to transfer: {nbytes} bytes is too large. Shall be smaller than {self.MAX_BTT} bytes")
        self._btt = nbytes & self.MAX_BTT

    def get_debug_info(self):
        base_addr = ((self._base_addr_upper & self.MASK_32b) <<
                     32) | (self._base_addr_lower & self.MASK_32b)
        debug_info = f"start = {self._cmd}, btt = {self._btt}, base_addr = {base_addr}, state = {self.state()}"
        return debug_info

    def __del__(self):
        self.stop()


class StreamingDmaV1(StreamingDmaBase):
    """
    Streaming DMA driver v1.0 allows user to start and stop continuously DMA transfer by slipping self._cmd between 0 (stop) and 1 (start).
    """

    def __init__(self, description):
        super().__init__(description, fsm_lut=['S_IDLE', 'S_STREAM', 'S_ERROR'])

    bindto = ['user.org:user:data_mover_ctrl:1.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = 1

    def stop(self):
        self._cmd = 0


class StreamingDmaV2(StreamingDmaBase):
    """
    Streaming DMA driver v2.0 allows user to start and stop continuously DMA transfer by slipping self._cmd between 0 (stop) and 1 (start).
    """

    def __init__(self, description):
        super().__init__(description, fsm_lut=[
            'S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR'])

    bindto = ['user.org:user:data_mover_ctrl:2.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = 1

    def stop(self):
        self._cmd = 0


class StreamingDmaV3(StreamingDmaBase):
    """
    Streaming DMA driver v3.0 allows users to send the following commands. 

    1) IDLE: DMA goes to IDLE state 
    2) SINGLE: DMA make a single data transfer
    3) STREAM: DMA stream data continuously
    """
    _CMD_LUT = {'IDLE': 0x0, 'SINGLE': 0x1, 'STREAM': 0x2}

    def __init__(self, description):
        super().__init__(description, fsm_lut=[
            'S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR', 'S_SINGLE'])

    bindto = ['user.org:user:data_mover_ctrl:3.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = self._CMD_LUT['SINGLE']
        while True:
            if self.state() == 'S_IDLE':
                break  # CPU polling the FSM state
            else:
                time.sleep(0.01)
        self._cmd = self._CMD_LUT['IDLE']

    def stream(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = self._CMD_LUT['STREAM']

    def stop(self):
        self._cmd = self._CMD_LUT['IDLE']


class StreamingDmaV4(StreamingDmaBase):
    """
    Streaming DMA driver v4.0 allows users to send the following commands. 

    1) IDLE: DMA goes to IDLE state 
    2) SINGLE: DMA make a single data transfer
    3) STREAM: DMA stream data continuously
    4) DUTY: DMA stream data continuously with duty cycling
    """
    _CMD_LUT = {'IDLE': 0x0, 'SINGLE': 0x1, 'STREAM': 0x2, 'DUTY': 0x3}

    def __init__(self, description):
        super().__init__(description, fsm_lut=[
            'S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR', 'S_SINGLE', 'S_WAIT', 'S_DUTY', 'S_SING_WAIT'])
        self.iq_samples_per_cyc = 8
    bindto = ['user.org:user:data_mover_ctrl:4.0']

    @property
    def _duty_cyc_target(self):
        return self.read(0x14)

    @_duty_cyc_target.setter
    def _duty_cyc_target(self, cycles):
        """The number of cycles to be waited"""
        self.write(0x14, cycles)

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = self._CMD_LUT['SINGLE']
        # Trigger FSM to jump from S_SING_WAIT to S_IDLE
        self._cmd = self._CMD_LUT['IDLE']
        while True:
            if self.state() == 'S_IDLE':
                break  # CPU polling the FSM state
            else:
                time.sleep(0.01)

    def stream(self, buffer, duty_cycle=100):
        if duty_cycle != 100:  # Duty cycling
            ratio_fp = (100 - duty_cycle) / duty_cycle
            dma_time_in_cyc = int(buffer.size / self.iq_samples_per_cyc)
            self._duty_cyc_target = int(ratio_fp * dma_time_in_cyc)
            self._config(buffer.physical_address, buffer.nbytes)
            self._cmd = self._CMD_LUT['DUTY']
        else:
            self._config(buffer.physical_address, buffer.nbytes)
            self._cmd = self._CMD_LUT['STREAM']

    def stop(self):
        self._cmd = self._CMD_LUT['IDLE']


class TxDmaMonitor(DmaMonitor):
    """
    This is the Tx DMA driver for Xilinx's DMA IP
    """

    def transfer(self, buffer):
        self.dma.sendchannel.transfer(buffer)

    def wait(self):
        self.dma.sendchannel.wait()

    def stop(self):
        pass


class RxDmaMonitor(DmaMonitor):
    """
    This is the Rx DMA driver for Xilinx's DMA IP
    """

    def transfer(self, buffer):
        self.dma.recvchannel.transfer(buffer)

    def wait(self):
        self.dma.recvchannel.wait()

    def stop(self):
        pass
