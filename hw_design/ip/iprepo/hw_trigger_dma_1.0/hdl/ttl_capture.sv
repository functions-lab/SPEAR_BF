/**
 * @brief TTL Signal Capture Module with Debouncing
 * 
 * This module provides TTL signal capture functionality with configurable debouncing
 * for multiple signal bits. It instantiates individual single-bit capture modules
 * for each bit of the input signal bus.
 * 
 * @param DEBOUNCE_COUNT Configurable debounce factor (default: 10)
 *                       Controls the number of clock cycles for debouncing
 * @param SIGNAL_WIDTH   Width of the signal bus (default: 1)
 *                       Determines how many signal bits to process
 * 
 * @port clk         Clock input signal
 * @port aresetn     Active-low asynchronous reset
 * @port signal_in   Input signal bus [SIGNAL_WIDTH-1:0]
 * @port signal_out  Output signal bus [SIGNAL_WIDTH-1:0] with debouncing applied
 * 
 * @details
 * - Uses generate blocks to create multiple instances of ttl_capture_1b
 * - Each bit of the input signal is processed independently
 * - Debouncing helps eliminate signal noise and false triggers
 * - Parameterizable design allows customization for different applications
 * 
 * @dependencies
 * - Requires ttl_capture_1b module implementation
 */

`timescale 1ns / 1ps

module ttl_capture #(
    parameter DEBOUNCE_COUNT = 10,  // Tunable debounce factor
    parameter SIGNAL_WIDTH   = 1    // Width of the signal bus
) (
    input logic clk,
    input logic aresetn,
    input logic [SIGNAL_WIDTH-1:0] signal_in,
    output logic [SIGNAL_WIDTH-1:0] signal_out
);

  // Generate ttl_capture_1b instances for each signal bit
  genvar i;
  generate
    for (i = 0; i < SIGNAL_WIDTH; i = i + 1) begin : gen_ttl_counter
      ttl_capture_1b #(
          .DEBOUNCE_COUNT(DEBOUNCE_COUNT)
      ) u_ttl_counter (
          .clk(clk),
          .aresetn(aresetn),
          .signal_in(signal_in[i]),
          .signal_out(signal_out[i])
      );
    end
  endgenerate

endmodule
