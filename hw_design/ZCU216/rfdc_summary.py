import os
import glob
import rfdc_info


def calculate_iq_rate(sampling_rate_str, mode_str):
    try:
        sr = float(sampling_rate_str)
        mode = float(mode_str)
        if mode <= 0:
            return "N/A"
        return f"{sr/mode:.4g}"
    except (ValueError, TypeError):
        return "N/A"


def generate_markdown_summary(all_info):
    lines = []
    lines.append("# RFDC Configuration Summary")
    lines.append("")

    # Sort designs by name
    sorted_designs = sorted(all_info, key=lambda x: x['design_name'])

    for info in sorted_designs:
        design_name = info['design_name']
        lines.append(f"## Design: {design_name}")
        lines.append("")

        lines.append("### ADC Configuration")
        lines.append(
            "| Tile | Sampling Rate (GSPS) | Multi-Tile Sync | Refclk (MHz) | Decimation Modes (Block 0-3) | IQ Bandwidth (GHz) (Block 0-3) |")
        lines.append("|---|---|---|---|---|---|")
        for tile in range(4):
            adc = info['adc'][tile]
            decim_modes = adc['Decimation_Mode']
            sampling_rate = adc['Sampling_Rate']

            decim_str = ", ".join([f"{b}:{decim_modes[b]}" for b in range(4)])

            iq_rates = []
            for b in range(4):
                rate = calculate_iq_rate(sampling_rate, decim_modes[b])
                iq_rates.append(f"{b}:{rate}")
            iq_rate_str = ", ".join(iq_rates)

            lines.append(
                f"| {tile} | {sampling_rate} | {adc['Multi_Tile_Sync']} | {adc['Refclk_Freq']} | {decim_str} | {iq_rate_str} |")
        lines.append("")

        lines.append("### DAC Configuration")
        lines.append(
            "| Tile | Sampling Rate (GSPS) | Multi-Tile Sync | Refclk (MHz) | Interpolation Modes (Block 0-3) | IQ Bandwidth (GHz) (Block 0-3) |")
        lines.append("|---|---|---|---|---|---|")
        for tile in range(4):
            dac = info['dac'][tile]
            interp_modes = dac['Interpolation_Mode']
            sampling_rate = dac['Sampling_Rate']

            interp_str = ", ".join([f"{b}:{interp_modes[b]}" for b in range(4)])

            iq_rates = []
            for b in range(4):
                rate = calculate_iq_rate(sampling_rate, interp_modes[b])
                iq_rates.append(f"{b}:{rate}")
            iq_rate_str = ", ".join(iq_rates)

            lines.append(
                f"| {tile} | {sampling_rate} | {dac['Multi_Tile_Sync']} | {dac['Refclk_Freq']} | {interp_str} | {iq_rate_str} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    root_dir = "./block_designs"
    # Find all .tcl files recursively
    tcl_files = sorted(glob.glob(os.path.join(
        root_dir, "**/*.tcl"), recursive=True))

    all_design_info = []

    print(f"Found {len(tcl_files)} TCL files. Processing...")

    for tcl_file in tcl_files:
        try:
            info = rfdc_info.parse_tcl(tcl_file)
            # Only include if we found a valid design name
            if info['design_name'] != "Unknown":
                all_design_info.append(info)
            else:
                pass
        except Exception as e:
            print(f"Error parsing {tcl_file}: {e}")

    summary_content = generate_markdown_summary(all_design_info)

    with open("SUMMARY.md", "w") as f:
        f.write(summary_content)

    print(f"SUMMARY.md generated with {len(all_design_info)} designs.")


if __name__ == "__main__":
    main()
