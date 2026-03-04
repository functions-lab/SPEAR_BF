import sys
import re
import os


def parse_tcl(file_path):
    info = {
        "design_name": "Unknown",
        "adc": {},
        "dac": {}
    }

    # Initialize structure
    for tile in range(4):
        info["adc"][tile] = {
            "Sampling_Rate": "N/A",
            "Multi_Tile_Sync": "N/A",
            "Refclk_Freq": "N/A",
            "Decimation_Mode": {}
        }
        info["dac"][tile] = {
            "Sampling_Rate": "N/A",
            "Multi_Tile_Sync": "N/A",
            "Refclk_Freq": "N/A",
            "Interpolation_Mode": {}
        }
        for block in range(4):
            info["adc"][tile]["Decimation_Mode"][block] = "N/A"
            info["dac"][tile]["Interpolation_Mode"][block] = "N/A"

    with open(file_path, 'r') as f:
        content = f.read()

    # Extract design name
    design_name_match = re.search(r'set design_name\s+(\S+)', content)
    if design_name_match:
        info["design_name"] = design_name_match.group(1)

    # Extract RFDC config block
    # We look for "set_property -dict [ list \" up to \" ] $usp_rf_data_converter"
    # Note: The variable name might vary but usually it is usp_rf_data_converter based on the example.
    # To be safe, we scan for CONFIG.* keys. The dict usually starts with set_property -dict [ list

    # Regex for configuration keys
    # CONFIG.ADC0_Sampling_Rate {2.4}
    # CONFIG.ADC0_Multi_Tile_Sync {true}
    # CONFIG.ADC_Decimation_Mode00 {4}

    # Generic pattern to capture CONFIG.Key {Value}
    # We assume the format is consistently CONFIG.KEY {VALUE} or CONFIG.KEY VALUE
    pattern = re.compile(r'CONFIG\.(\w+)\s+\{?([^}\\s]+)\}?')

    matches = pattern.findall(content)

    for key, value in matches:
        # ADC Tile configs
        # CONFIG.ADCx_...
        adc_tile_match = re.match(r'ADC(\d)_(\w+)', key)
        if adc_tile_match:
            tile_idx = int(adc_tile_match.group(1))
            param = adc_tile_match.group(2)
            if tile_idx in info["adc"]:
                if param in info["adc"][tile_idx]:
                    info["adc"][tile_idx][param] = value
            continue

        # DAC Tile configs
        dac_tile_match = re.match(r'DAC(\d)_(\w+)', key)
        if dac_tile_match:
            tile_idx = int(dac_tile_match.group(1))
            param = dac_tile_match.group(2)
            if tile_idx in info["dac"]:
                if param in info["dac"][tile_idx]:
                    info["dac"][tile_idx][param] = value
            continue

        # Decimation Mode (ADC)
        # CONFIG.ADC_Decimation_ModeXY
        adc_dec_match = re.match(r'ADC_Decimation_Mode(\d)(\d)', key)
        if adc_dec_match:
            tile_idx = int(adc_dec_match.group(1))
            block_idx = int(adc_dec_match.group(2))
            if tile_idx in info["adc"]:
                info["adc"][tile_idx]["Decimation_Mode"][block_idx] = value
            continue

        # Interpolation Mode (DAC)
        # CONFIG.DAC_Interpolation_ModeXY
        dac_inter_match = re.match(r'DAC_Interpolation_Mode(\d)(\d)', key)
        if dac_inter_match:
            tile_idx = int(dac_inter_match.group(1))
            block_idx = int(dac_inter_match.group(2))
            if tile_idx in info["dac"]:
                info["dac"][tile_idx]["Interpolation_Mode"][block_idx] = value
            continue

    return info


def generate_report(info, output_file=None):
    lines = []
    lines.append(f"Design Name: {info['design_name']}")
    lines.append("-" * 30)

    for tile in range(4):
        adc_info = info["adc"][tile]
        lines.append(f"ADC Tile {tile}:")
        # Assuming GSPS based on example "2.4"
        lines.append(f"  Sampling Rate: {adc_info['Sampling_Rate']} GSPS")
        lines.append(f"  Multi_Tile_Sync: {adc_info['Multi_Tile_Sync']}")
        lines.append(f"  Refclk_Freq: {adc_info['Refclk_Freq']} MHz")
        lines.append("  Decimation Modes (Block 0-3): " +
                     ", ".join([f"{b}:{m}" for b, m in adc_info['Decimation_Mode'].items()]))
        lines.append("")

    for tile in range(4):
        dac_info = info["dac"][tile]
        lines.append(f"DAC Tile {tile}:")
        lines.append(f"  Sampling Rate: {dac_info['Sampling_Rate']} GSPS")
        lines.append(f"  Multi_Tile_Sync: {dac_info['Multi_Tile_Sync']}")
        lines.append(f"  Refclk_Freq: {dac_info['Refclk_Freq']} MHz")
        lines.append("  Interpolation Modes (Block 0-3): " +
                     ", ".join([f"{b}:{m}" for b, m in dac_info['Interpolation_Mode'].items()]))
        lines.append("")

    report_content = "\n".join(lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_content)
        print(f"Report written to {output_file}")
    else:
        print(report_content)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rfdc_info.py <tcl_file>")
        sys.exit(1)

    tcl_file = sys.argv[1]
    if not os.path.exists(tcl_file):
        print(f"Error: File {tcl_file} not found.")
        sys.exit(1)

    info = parse_tcl(tcl_file)
    output_filename = f"{info['design_name']}_info.txt"
    generate_report(info, output_filename)
