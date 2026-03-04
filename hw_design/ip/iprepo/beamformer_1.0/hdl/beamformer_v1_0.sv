`timescale 1 ns / 1 ps

module beamformer_v1_0 #(
    // Parameters
    parameter int NUM_CH = 16,  // Number of channels (fixed)
    parameter int AXIS_TDATA_WIDTH = 32  // Data width for I/Q samples per channel
) (
    // Clock and Reset
    input logic axis_aclk,
    input logic axis_aresetn,

    // AXI-Stream Slave Interface for Beamforming Weights (S_AXIS_BFW)
    // 512 bits = 16 channels x 32 bits per weight (16-bit I + 16-bit Q)
    input  logic [NUM_CH*32-1:0] s_axis_bfw_tdata,
    input  logic                 s_axis_bfw_tvalid,
    output logic                 s_axis_bfw_tready,

    // AXI-Stream Slave Interface for Input IQ Samples (S_AXIS) - 16 Channels
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis0_tdata,
    input  logic                        s_axis0_tvalid,
    output logic                        s_axis0_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis1_tdata,
    input  logic                        s_axis1_tvalid,
    output logic                        s_axis1_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis2_tdata,
    input  logic                        s_axis2_tvalid,
    output logic                        s_axis2_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis3_tdata,
    input  logic                        s_axis3_tvalid,
    output logic                        s_axis3_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis4_tdata,
    input  logic                        s_axis4_tvalid,
    output logic                        s_axis4_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis5_tdata,
    input  logic                        s_axis5_tvalid,
    output logic                        s_axis5_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis6_tdata,
    input  logic                        s_axis6_tvalid,
    output logic                        s_axis6_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis7_tdata,
    input  logic                        s_axis7_tvalid,
    output logic                        s_axis7_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis8_tdata,
    input  logic                        s_axis8_tvalid,
    output logic                        s_axis8_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis9_tdata,
    input  logic                        s_axis9_tvalid,
    output logic                        s_axis9_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis10_tdata,
    input  logic                        s_axis10_tvalid,
    output logic                        s_axis10_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis11_tdata,
    input  logic                        s_axis11_tvalid,
    output logic                        s_axis11_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis12_tdata,
    input  logic                        s_axis12_tvalid,
    output logic                        s_axis12_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis13_tdata,
    input  logic                        s_axis13_tvalid,
    output logic                        s_axis13_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis14_tdata,
    input  logic                        s_axis14_tvalid,
    output logic                        s_axis14_tready,
    input  logic [AXIS_TDATA_WIDTH-1:0] s_axis15_tdata,
    input  logic                        s_axis15_tvalid,
    output logic                        s_axis15_tready,

    // AXI-Stream Master Interface for Output IQ Samples (M_AXIS) - 16 Channels
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis0_tdata,
    output logic                        m_axis0_tvalid,
    input  logic                        m_axis0_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis1_tdata,
    output logic                        m_axis1_tvalid,
    input  logic                        m_axis1_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis2_tdata,
    output logic                        m_axis2_tvalid,
    input  logic                        m_axis2_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis3_tdata,
    output logic                        m_axis3_tvalid,
    input  logic                        m_axis3_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis4_tdata,
    output logic                        m_axis4_tvalid,
    input  logic                        m_axis4_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis5_tdata,
    output logic                        m_axis5_tvalid,
    input  logic                        m_axis5_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis6_tdata,
    output logic                        m_axis6_tvalid,
    input  logic                        m_axis6_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis7_tdata,
    output logic                        m_axis7_tvalid,
    input  logic                        m_axis7_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis8_tdata,
    output logic                        m_axis8_tvalid,
    input  logic                        m_axis8_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis9_tdata,
    output logic                        m_axis9_tvalid,
    input  logic                        m_axis9_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis10_tdata,
    output logic                        m_axis10_tvalid,
    input  logic                        m_axis10_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis11_tdata,
    output logic                        m_axis11_tvalid,
    input  logic                        m_axis11_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis12_tdata,
    output logic                        m_axis12_tvalid,
    input  logic                        m_axis12_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis13_tdata,
    output logic                        m_axis13_tvalid,
    input  logic                        m_axis13_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis14_tdata,
    output logic                        m_axis14_tvalid,
    input  logic                        m_axis14_tready,
    output logic [AXIS_TDATA_WIDTH-1:0] m_axis15_tdata,
    output logic                        m_axis15_tvalid,
    input  logic                        m_axis15_tready
);

  // Internal signals for beamforming weights storage
  logic [NUM_CH-1:0][31:0] bfw_weights;

  // Internal arrays to collect individual channel signals
  logic [NUM_CH-1:0][AXIS_TDATA_WIDTH-1:0] s_axis_tdata_array;
  logic [NUM_CH-1:0] s_axis_tvalid_array;
  logic [NUM_CH-1:0] s_axis_tready_array;
  logic [NUM_CH-1:0][AXIS_TDATA_WIDTH-1:0] m_axis_tdata_array;
  logic [NUM_CH-1:0] m_axis_tvalid_array;
  logic [NUM_CH-1:0] m_axis_tready_array;

  // Map individual input channels to arrays
  assign s_axis_tdata_array[0] = s_axis0_tdata;
  assign s_axis_tvalid_array[0] = s_axis0_tvalid;
  assign s_axis0_tready = s_axis_tready_array[0];
  assign s_axis_tdata_array[1] = s_axis1_tdata;
  assign s_axis_tvalid_array[1] = s_axis1_tvalid;
  assign s_axis1_tready = s_axis_tready_array[1];
  assign s_axis_tdata_array[2] = s_axis2_tdata;
  assign s_axis_tvalid_array[2] = s_axis2_tvalid;
  assign s_axis2_tready = s_axis_tready_array[2];
  assign s_axis_tdata_array[3] = s_axis3_tdata;
  assign s_axis_tvalid_array[3] = s_axis3_tvalid;
  assign s_axis3_tready = s_axis_tready_array[3];
  assign s_axis_tdata_array[4] = s_axis4_tdata;
  assign s_axis_tvalid_array[4] = s_axis4_tvalid;
  assign s_axis4_tready = s_axis_tready_array[4];
  assign s_axis_tdata_array[5] = s_axis5_tdata;
  assign s_axis_tvalid_array[5] = s_axis5_tvalid;
  assign s_axis5_tready = s_axis_tready_array[5];
  assign s_axis_tdata_array[6] = s_axis6_tdata;
  assign s_axis_tvalid_array[6] = s_axis6_tvalid;
  assign s_axis6_tready = s_axis_tready_array[6];
  assign s_axis_tdata_array[7] = s_axis7_tdata;
  assign s_axis_tvalid_array[7] = s_axis7_tvalid;
  assign s_axis7_tready = s_axis_tready_array[7];
  assign s_axis_tdata_array[8] = s_axis8_tdata;
  assign s_axis_tvalid_array[8] = s_axis8_tvalid;
  assign s_axis8_tready = s_axis_tready_array[8];
  assign s_axis_tdata_array[9] = s_axis9_tdata;
  assign s_axis_tvalid_array[9] = s_axis9_tvalid;
  assign s_axis9_tready = s_axis_tready_array[9];
  assign s_axis_tdata_array[10] = s_axis10_tdata;
  assign s_axis_tvalid_array[10] = s_axis10_tvalid;
  assign s_axis10_tready = s_axis_tready_array[10];
  assign s_axis_tdata_array[11] = s_axis11_tdata;
  assign s_axis_tvalid_array[11] = s_axis11_tvalid;
  assign s_axis11_tready = s_axis_tready_array[11];
  assign s_axis_tdata_array[12] = s_axis12_tdata;
  assign s_axis_tvalid_array[12] = s_axis12_tvalid;
  assign s_axis12_tready = s_axis_tready_array[12];
  assign s_axis_tdata_array[13] = s_axis13_tdata;
  assign s_axis_tvalid_array[13] = s_axis13_tvalid;
  assign s_axis13_tready = s_axis_tready_array[13];
  assign s_axis_tdata_array[14] = s_axis14_tdata;
  assign s_axis_tvalid_array[14] = s_axis14_tvalid;
  assign s_axis14_tready = s_axis_tready_array[14];
  assign s_axis_tdata_array[15] = s_axis15_tdata;
  assign s_axis_tvalid_array[15] = s_axis15_tvalid;
  assign s_axis15_tready = s_axis_tready_array[15];

  // Map arrays to individual output channels
  assign m_axis0_tdata = m_axis_tdata_array[0];
  assign m_axis0_tvalid = m_axis_tvalid_array[0];
  assign m_axis_tready_array[0] = m_axis0_tready;
  assign m_axis1_tdata = m_axis_tdata_array[1];
  assign m_axis1_tvalid = m_axis_tvalid_array[1];
  assign m_axis_tready_array[1] = m_axis1_tready;
  assign m_axis2_tdata = m_axis_tdata_array[2];
  assign m_axis2_tvalid = m_axis_tvalid_array[2];
  assign m_axis_tready_array[2] = m_axis2_tready;
  assign m_axis3_tdata = m_axis_tdata_array[3];
  assign m_axis3_tvalid = m_axis_tvalid_array[3];
  assign m_axis_tready_array[3] = m_axis3_tready;
  assign m_axis4_tdata = m_axis_tdata_array[4];
  assign m_axis4_tvalid = m_axis_tvalid_array[4];
  assign m_axis_tready_array[4] = m_axis4_tready;
  assign m_axis5_tdata = m_axis_tdata_array[5];
  assign m_axis5_tvalid = m_axis_tvalid_array[5];
  assign m_axis_tready_array[5] = m_axis5_tready;
  assign m_axis6_tdata = m_axis_tdata_array[6];
  assign m_axis6_tvalid = m_axis_tvalid_array[6];
  assign m_axis_tready_array[6] = m_axis6_tready;
  assign m_axis7_tdata = m_axis_tdata_array[7];
  assign m_axis7_tvalid = m_axis_tvalid_array[7];
  assign m_axis_tready_array[7] = m_axis7_tready;
  assign m_axis8_tdata = m_axis_tdata_array[8];
  assign m_axis8_tvalid = m_axis_tvalid_array[8];
  assign m_axis_tready_array[8] = m_axis8_tready;
  assign m_axis9_tdata = m_axis_tdata_array[9];
  assign m_axis9_tvalid = m_axis_tvalid_array[9];
  assign m_axis_tready_array[9] = m_axis9_tready;
  assign m_axis10_tdata = m_axis_tdata_array[10];
  assign m_axis10_tvalid = m_axis_tvalid_array[10];
  assign m_axis_tready_array[10] = m_axis10_tready;
  assign m_axis11_tdata = m_axis_tdata_array[11];
  assign m_axis11_tvalid = m_axis_tvalid_array[11];
  assign m_axis_tready_array[11] = m_axis11_tready;
  assign m_axis12_tdata = m_axis_tdata_array[12];
  assign m_axis12_tvalid = m_axis_tvalid_array[12];
  assign m_axis_tready_array[12] = m_axis12_tready;
  assign m_axis13_tdata = m_axis_tdata_array[13];
  assign m_axis13_tvalid = m_axis_tvalid_array[13];
  assign m_axis_tready_array[13] = m_axis13_tready;
  assign m_axis14_tdata = m_axis_tdata_array[14];
  assign m_axis14_tvalid = m_axis_tvalid_array[14];
  assign m_axis_tready_array[14] = m_axis14_tready;
  assign m_axis15_tdata = m_axis_tdata_array[15];
  assign m_axis15_tvalid = m_axis_tvalid_array[15];
  assign m_axis_tready_array[15] = m_axis15_tready;

  // Beamforming weight capture
  always_ff @(posedge axis_aclk or negedge axis_aresetn) begin
    if (!axis_aresetn) begin
      bfw_weights <= '0;
    end else begin
      if (s_axis_bfw_tvalid && s_axis_bfw_tready) begin
        // Capture weights: I0, Q0, I1, Q1, ..., I15, Q15
        for (int i = 0; i < NUM_CH; i++) begin
          bfw_weights[i] <= s_axis_bfw_tdata[i*32+:32];
        end
      end
    end
  end

  // Always ready to accept beamforming weights
  assign s_axis_bfw_tready = 1'b1;

  // Generate beamformer instances for each channel using a for loop
  genvar ch;
  generate
    for (ch = 0; ch < NUM_CH; ch++) begin : gen_beamformer_ch
      beamformer_channel #(
          .AXIS_TDATA_WIDTH(AXIS_TDATA_WIDTH)
      ) u_beamformer_ch (
          .axis_aclk    (axis_aclk),
          .axis_aresetn (axis_aresetn),
          // Beamforming weight for this channel
          .bfw_weight   (bfw_weights[ch]),
          // Input IQ samples from array
          .s_axis_tdata (s_axis_tdata_array[ch]),
          .s_axis_tvalid(s_axis_tvalid_array[ch]),
          .s_axis_tready(s_axis_tready_array[ch]),
          // Output IQ samples to array
          .m_axis_tdata (m_axis_tdata_array[ch]),
          .m_axis_tvalid(m_axis_tvalid_array[ch]),
          .m_axis_tready(m_axis_tready_array[ch])
      );
    end
  endgenerate

endmodule
