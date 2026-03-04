# TIQC Square Wave Pulse Generation

This module provides tools for generating phase-coherent square wave pulses Trapped Ion Quantum Control (TIQC) applications.

## Features

- **SquareWave**: Generate square wave pulses with precise phase alignment to a reference tone
- **Scheduler**: Schedule multiple pulses with padding
- **Digitizer**: Convert scheduled pulses into IQ waveforms for RF transmission

## Installation

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Run the demonstration program:

```bash
python3 demo_square_wave.py
```

This will:
1. Create multiple square wave pulses with different phases
2. Schedule them with proper timing separation
3. Generate IQ waveforms with carrier modulation
4. Display comprehensive plots showing magnitude, I/Q components, phase, and mixing results