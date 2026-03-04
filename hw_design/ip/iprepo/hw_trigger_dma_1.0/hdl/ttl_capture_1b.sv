/**
 * @module ttl_capture_1b
 * @brief TTL signal capture module with debouncing and edge detection
 * 
 * This module captures TTL input signals and generates a single-cycle pulse output
 * when a specific pattern is detected. The pattern consists of DEBOUNCE_COUNT
 * consecutive zeros followed by DEBOUNCE_COUNT consecutive ones, providing
 * debouncing functionality for noisy input signals.
 * 
 * @param DEBOUNCE_COUNT Number of consecutive samples required for pattern detection
 *                       (default: 10). Total shift register width is 2*DEBOUNCE_COUNT.
 * 
 * @input clk           System clock
 * @input aresetn       Active-low asynchronous reset
 * @input signal_in     Input TTL signal to be captured and debounced
 * 
 * @output signal_out   Single-cycle pulse output generated on rising edge of pattern detection
 * 
 * @functionality
 * - Maintains a shift register of size 2*DEBOUNCE_COUNT to track signal_in history
 * - Detects pattern: first half all zeros, second half all ones
 * - Generates single-cycle pulse on pattern detection rising edge
 * - Provides debouncing by requiring sustained signal levels
 * 
 * @timing
 * - Pattern detection requires 2*DEBOUNCE_COUNT clock cycles
 * - Output pulse is exactly one clock cycle wide
 * - Reset behavior: all internal state cleared, output driven low
 */

`timescale 1ns / 1ps

module ttl_capture_1b #(
    parameter DEBOUNCE_COUNT = 10
) (
    input  logic clk,
    input  logic aresetn,
    input  logic signal_in,
    output logic signal_out
);
  // Internal signals
  logic [2*DEBOUNCE_COUNT-1:0] shift_register;
  logic pattern_detected;
  logic prev_pattern_detected;

  // Shift register to capture signal_in history
  always_ff @(posedge clk or negedge aresetn) begin
    if (!aresetn) begin
      shift_register <= '0;
      prev_pattern_detected <= 1'b0;
      signal_out <= 1'b0;
    end else begin
      // Shift in new bit from signal_in
      shift_register <= {shift_register[2*DEBOUNCE_COUNT-2:0], signal_in};

      // Store previous pattern detection state
      prev_pattern_detected <= pattern_detected;

      // Generate single cycle pulse on rising edge of pattern detection
      signal_out <= pattern_detected & ~prev_pattern_detected;
    end
  end

  // Pattern detection logic
  always_comb begin
    logic first_half_all_zeros, second_half_all_ones;

    // Check if first half (MSBs) are all zeros
    first_half_all_zeros = (shift_register[2*DEBOUNCE_COUNT-1:DEBOUNCE_COUNT] == '0);

    // Check if second half (LSBs) are all ones
    second_half_all_ones = (shift_register[DEBOUNCE_COUNT-1:0] == {DEBOUNCE_COUNT{1'b1}});

    // Pattern is detected when both conditions are met
    pattern_detected = first_half_all_zeros & second_half_all_ones;
  end

endmodule
