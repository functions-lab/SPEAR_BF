`timescale 1 ns / 1 ps

module beamformer_channel #(
    parameter int AXIS_TDATA_WIDTH = 32  // Must be multiple of 32 (16-bit I + 16-bit Q)
) (
    // Clock and Reset
    input logic axis_aclk,
    input logic axis_aresetn,

    // Beamforming weight for this channel (32-bit: 16-bit I + 16-bit Q)
    input logic [31:0] bfw_weight,

    // AXI-Stream Slave Interface for Input IQ Samples
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis_tdata,
    input  logic                        s_axis_tvalid,
    output logic                        s_axis_tready,

    // AXI-Stream Master Interface for Output IQ Samples
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis_tdata,
    output logic                        m_axis_tvalid,
    input  logic                        m_axis_tready
);

  // Calculate number of IQ pairs per clock cycle
  localparam int NUM_IQ_PAIRS = AXIS_TDATA_WIDTH / 32;

  // Extract weight components (signed 16-bit)
  wire signed [15:0] weight_i = bfw_weight[15:0];
  wire signed [15:0] weight_q = bfw_weight[31:16];

  // Pipeline registers
  logic [AXIS_TDATA_WIDTH-1:0] output_data_r;
  logic output_valid_r;

  // Ready signals
  assign s_axis_tready = 1'b1;

  // Element-wise multiplication stage
  // I_out = I_in * W_I
  // Q_out = Q_in * W_Q

  always_ff @(posedge axis_aclk or negedge axis_aresetn) begin
    if (!axis_aresetn) begin
      output_data_r  <= '0;
      output_valid_r <= 1'b0;
    end else begin
      if (s_axis_tvalid && s_axis_tready && m_axis_tready) begin
        // Process all IQ pairs in parallel
        for (int i = 0; i < NUM_IQ_PAIRS; i++) begin
          logic signed [15:0] in_i, in_q;
          logic signed [31:0] out_i_full, out_q_full;
          logic signed [15:0] out_i, out_q;

          // Extract input I and Q (signed 16-bit)
          in_i = s_axis_tdata[i*32+:16];
          in_q = s_axis_tdata[i*32+16+:16];

          // Complex multiplication: (a + bi) * (c + di) = (ac - bd) + (ad + bc)i
          // I_out = I_in * W_I - Q_in * W_Q
          // Q_out = I_in * W_Q + Q_in * W_I
          out_i_full = (in_i * weight_i) - (in_q * weight_q);
          out_q_full = (in_i * weight_q) + (in_q * weight_i);

          // Scale down by 2^15 to maintain 16-bit output
          // (right shift 15 bits with rounding)
          out_i = out_i_full[30:15] + out_i_full[14];
          out_q = out_q_full[30:15] + out_q_full[14];

          // Pack output
          output_data_r[i*32+:16]    <= out_i;
          output_data_r[i*32+16+:16] <= out_q;
        end
        output_valid_r <= 1'b1;
      end else if (m_axis_tready) begin
        output_valid_r <= 1'b0;
      end
    end
  end

  // Output assignments
  assign m_axis_tdata  = output_data_r;
  assign m_axis_tvalid = output_valid_r;

endmodule
