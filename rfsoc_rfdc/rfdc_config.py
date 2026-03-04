from rfsoc_rfdc.txt_logger import TxtLogger


def merge_dict(dict1, dict2):
    dict2.update(dict1)
    return dict2


ZCU216_MIN_MAX_CONFIG = {
    "RefClockForPLLMin": 102.40625,
    "RefClockForPLLMax": 615.0,
    "RefClockNoPLLDacMin": 500.0,
    "RefClockNoPLLDacMax": 10000.0,
    "RefClockNoPLLAdcMin": 500.0,
    "RefClockNoPLLAdcMax": 2500.0
}

ZCU216_DEMO3_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 4000.0,
    "DACInterpolationRate": 4,
    "DACNCO": 1000,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 2,
    "ADCNCO": -1000
}

ZCU216_DEMO2_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 5000.0,
    "DACInterpolationRate": 20,
    "DACNCO": 425,
    "ADCSampleRate": 2500.0,
    "ADCInterpolationRate": 10,
    "ADCNCO": -425
}

ZCU216_DEMO1_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 4000.0,
    "DACInterpolationRate": 40,
    "DACNCO": 350,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 20,
    "ADCNCO": -350
}

ZCU216_DEFAULT_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 2000.0,
    "DACInterpolationRate": 2,
    "DACNCO": 0,
    "DACNyquistZone": 1,
    "InvSincFIR": 1,  # 0: Disable, 1: 1st Nyquist, 2: 2nd Nyquist
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 2,
    "ADCNCO": -0,
    "ADCNyquistZone": 1
}

# Initialize Logger (defaults to wave_files in current dir)
_logger = TxtLogger(log_dir="wave_files")

GLOBAL_VAR = {
    "CONFIG_NAME": "default_config",
    "BB_GAIN": 1.0,  # Baseband gain
    "LOGGER": _logger  # Store logger in config
}

EXP_CONFIG = {
    "QAM": "16QAM",
    "OFDM_ATTEN_DB": 0,
    "UsrpNameIfAny": "X310_322A005",
    "UsrpRx": "RFA_RX2",
    "ExternalAtten": 0.0,
    "UseSplitter": False,
    "SplitterType": "1-to-2",
    "BalunMode": "BALH0006",
    "BalunMin": 0.2,
    "BalunMax": 60,
}

ZCU216_CONFIG = merge_dict(ZCU216_MIN_MAX_CONFIG, ZCU216_DEFAULT_CONFIG)
ZCU216_CONFIG = merge_dict(ZCU216_CONFIG, GLOBAL_VAR)
ZCU216_CONFIG = merge_dict(ZCU216_CONFIG, EXP_CONFIG)
