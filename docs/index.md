# SPEAR-BF: RFSoC RFDC Documentation

Welcome to the API documentation for **SPEAR-BF** (Software-defined Python-Enhanced RFSoC Beamformer).

SPEAR-BF provides complete software and hardware designs for a real-time wideband D-band beamforming testbed built on the [Xilinx RFSoC](https://www.amd.com/en/products/adaptive-socs-and-fpgas/soc/zynq-ultrascale-plus-rfsoc.html) platform and the [CHARM D-band frontend](https://ieeexplore.ieee.org/abstract/document/10873811).

## Overview

SPEAR-BF bridges the gap in sub-THz spectrum research by providing a flexible, real-time, wideband experimental system. It supports:

- **Real-Time Wideband Streaming:** Up to 1.2 GHz aggregated bandwidth via custom Hardware-Assisted StreamingDMA.
- **Digital Beamforming:** Dedicated hardware IP for multi-channel phase and amplitude control.
- **Scalable Architecture:** 1T1R, 4T1R, and 8T1R configurations, expandable to 16T16R.
- **Pythonic Interface:** High-level PYNQ-based API for rapid prototyping.

## Package Structure

The `rfsoc_rfdc` package is organized into the following modules:

| Module | Description |
|--------|-------------|
| `rfdc` | RF Data Converter hardware control |
| `rfdc_config` | Board configuration dictionaries |
| `rfdc_task` | High-level RFDC task orchestration |
| `overlay_task` | Abstract base classes for overlay tasks |
| `rfsoc_overlay` | PYNQ overlay management |
| `clocks` | Clock source configuration |
| `dma_monitor` | DMA throughput monitoring |
| `dsp/` | DSP algorithms: OFDM, FMCW, beamforming |
| `receiver/` | Receiver channel management and analysis pipelines |
| `transmitter/` | Transmitter channel management |
| `plotter/` | Visualization utilities |
| `measurement/` | Link quality metrics |
| `tiqc/` | Transmon qubit control utilities |

## Quick Start

```python
from rfsoc_rfdc import RfsocOverlay
from rfsoc_rfdc.rfdc_task import RfdcTask

# Load the overlay
overlay = RfsocOverlay("path/to/bitfile.bit")

# Configure the RF data converter
rfdc_task = RfdcTask(overlay)
rfdc_task.run()
```

## Experimental Configurations

| Config | Setup | Carrier Frequency | Connection |
|--------|-------|-------------------|------------|
| **C1** | 1T1R | 700 MHz | Wired Loopback |
| **C2** | 1T1R | 700 MHz | OTA (Sub-6 GHz) |
| **C3** | 1T1R | 135 GHz | CHARM OTA |
| **C4** | 4T1R | 135 GHz | CHARM OTA |
| **C5** | 8T1R | 135 GHz | CHARM OTA |

## Source Repository

The source code is available on GitHub. See the [repository README](https://github.com/spear-bf/rfsoc_rfdc) for hardware setup instructions, bitstream preparation, and Jupyter Notebook examples.
