// external_debounce.sv
`timescale 1ns / 1ps

module external_debounce #(
    parameter DEBOUNCE_COUNT = 10,  // Tunable debounce factor
    parameter SIGNAL_WIDTH   = 1    // Width of the signal bus
) (
    input logic clk,
    input logic aresetn,
    input logic [SIGNAL_WIDTH-1:0] signal_in,
    output logic [SIGNAL_WIDTH-1:0] signal_out
);

  // Internal signals
  logic [$clog2(DEBOUNCE_COUNT)-1:0] counter[SIGNAL_WIDTH-1:0];
  logic [SIGNAL_WIDTH-1:0] signal_in_prev;
  logic [SIGNAL_WIDTH-1:0] debounced_state;  // Tracks if signal has been debounced

  // Generate debounce logic for each signal
  genvar i;
  generate
    for (i = 0; i < SIGNAL_WIDTH; i++) begin : gen_debounce
      // Counter and debounce logic for each signal bit
      always_ff @(posedge clk or negedge aresetn) begin
        if (!aresetn) begin
          counter[i] <= '0;
          signal_in_prev[i] <= 1'b0;
          signal_out[i] <= 1'b0;
          debounced_state[i] <= 1'b0;
        end else begin
          signal_in_prev[i] <= signal_in[i];

          // Default: signal_out is low (one-cycle pulse)
          signal_out[i] <= 1'b0;

          if (signal_in[i]) begin
            if (counter[i] == DEBOUNCE_COUNT - 1) begin
              // Signal has been high for DEBOUNCE_COUNT cycles
              if (!debounced_state[i]) begin
                // First time reaching debounced condition - generate pulse
                signal_out[i] <= 1'b1;
                debounced_state[i] <= 1'b1;
              end
              counter[i] <= counter[i];  // Hold counter at max
            end else begin
              counter[i] <= counter[i] + 1;
            end
          end else begin
            // Signal is low, reset counter and debounced state
            counter[i] <= '0;
            debounced_state[i] <= 1'b0;
          end
        end
      end
    end
  endgenerate

endmodule
