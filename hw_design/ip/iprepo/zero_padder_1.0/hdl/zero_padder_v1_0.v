
`timescale 1 ns / 1 ps

module zero_padder_v1_0 #(

    // Parameters of AXI Stream Master/Slave Bus Interface S_AXIS
    parameter integer C_AXIS_TDATA_WIDTH = 128
) (

    input wire force_zero,

    // Ports of Axi Slave Bus Interface S_AXIS
    output reg s_axis_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_tdata,
    input wire s_axis_tvalid,

    // Ports of Axi Master Bus Interface M_AXIS
    input wire axis_aclk,
    input wire axis_aresetn,
    output reg m_axis_tvalid,
    output reg [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_tdata,
    input wire m_axis_tready
);

  always @(*) begin  // tdata
    if (force_zero) m_axis_tdata = {{C_AXIS_TDATA_WIDTH} {1'b0}};
    else m_axis_tdata = (s_axis_tvalid && m_axis_tready) ? s_axis_tdata : {{C_AXIS_TDATA_WIDTH} {1'b0}};
  end

  always @(*) begin  // tready tvalid
    s_axis_tready = (force_zero) ? 1'b0 : m_axis_tready;
    m_axis_tvalid = (force_zero) ? 1'b1 : s_axis_tvalid;
  end

endmodule