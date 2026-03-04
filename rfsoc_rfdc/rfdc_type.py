import numpy as np


class MyRFdcType:

    DATA_PATH_DTYPE = np.int16

    DAC_MAX_SCALE = 2**13

    # Power-on Sequence Steps from page 163 of PG269: Zynq UltraScale+ RFSoC RF Data Converter v2.4 Gen 1/2/3
    POWER_ON_STATES = [
        "[Device Power-up and Configuration]",
        "[Power Supply Adjustment]",
        "[Clock Configuration]",
        "[Converter Calibration (ADC only)]",
        "[Wait for deassertion of AXI4-Stream reset]",
        "[Done]"
    ]

    POWER_ON_DESC = [
        "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]",
        "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]",
        "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]",
        "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]",
        "[The AXI4-Stream reset for the tile should be asserted until the AXI4-Stream clocks are stable. For example, if the clock is provided by a MMCM, the reset should be held until it has achieved lock. The state machine waits in this state until the reset is deasserted.]",
        "[The state machine has completed the power-up sequence.]"
    ]

    POWER_ON_SEQUENCE_STEPS = [
        {
            "Sequence Number": 0,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 1,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 2,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 3,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 4,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 5,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 6,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 7,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 8,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 9,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 10,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 11,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 12,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 13,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 14,
            "State": POWER_ON_STATES[4],
            "Description": POWER_ON_DESC[4]
        },
        {
            "Sequence Number": 15,
            "State": POWER_ON_STATES[5],
            "Description": POWER_ON_DESC[5]
        }
    ]

    def __init__(self):
        pass
