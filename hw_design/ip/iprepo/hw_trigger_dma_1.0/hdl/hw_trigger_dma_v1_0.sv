`timescale 1 ns / 1 ps
`include "fsm_def.sv"

module hw_trigger_dma_v1_0 #(
    // Users to add parameters here

    // User parameters ends
    // Do not modify the parameters beyond this line

    // Parameters of Axi Slave Bus Interface S_AXI
    parameter int C_S_AXI_DATA_WIDTH = 32,
    parameter int C_S_AXI_ADDR_WIDTH = 5,

    // Parameters of Axi Master Bus Interface M_AXIS
    parameter int C_M_AXIS_TDATA_WIDTH = 104,
    parameter int C_S_AXIS_TDATA_WIDTH = 8
) (
    // Users to add ports here

    output logic mm2s_halt,
    input  logic mm2s_halt_cmplt,
    output logic data_mover_aresetn,
    input  logic external_trig,
    input  logic mm2s_err,
    // User ports ends
    // Do not modify the ports beyond this line

    // Ports of Axi Slave Bus Interface S_AXI
    input  logic                              s_axi_aclk,
    input  logic                              s_axi_aresetn,
    input  logic [    C_S_AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    input  logic [                       2:0] s_axi_awprot,
    input  logic                              s_axi_awvalid,
    output logic                              s_axi_awready,
    input  logic [    C_S_AXI_DATA_WIDTH-1:0] s_axi_wdata,
    input  logic [(C_S_AXI_DATA_WIDTH/8)-1:0] s_axi_wstrb,
    input  logic                              s_axi_wvalid,
    output logic                              s_axi_wready,
    output logic [                       1:0] s_axi_bresp,
    output logic                              s_axi_bvalid,
    input  logic                              s_axi_bready,
    input  logic [    C_S_AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    input  logic [                       2:0] s_axi_arprot,
    input  logic                              s_axi_arvalid,
    output logic                              s_axi_arready,
    output logic [    C_S_AXI_DATA_WIDTH-1:0] s_axi_rdata,
    output logic [                       1:0] s_axi_rresp,
    output logic                              s_axi_rvalid,
    input  logic                              s_axi_rready,

    // Ports of AXI-Stream Master Bus Interface M_AXIS
    input  logic                            axis_aclk,
    input  logic                            axis_aresetn,
    output logic                            m_axis_tvalid,
    output logic [C_M_AXIS_TDATA_WIDTH-1:0] m_axis_tdata,
    input  logic                            m_axis_tready,

    // Ports of AXI-Stream Slave Bus Interface S_AXIS
    input  logic                            s_axis_tvalid,
    input  logic [C_S_AXIS_TDATA_WIDTH-1:0] s_axis_tdata,
    output logic                            s_axis_tready
);

  // Internal signals
  logic [C_S_AXI_DATA_WIDTH-1:0] command_o;
  logic [C_S_AXI_DATA_WIDTH-1:0] curr_state_i;
  logic [C_S_AXI_DATA_WIDTH-1:0] start_addr_upper_o, start_addr_lower_o;
  logic [C_S_AXI_DATA_WIDTH-1:0] byte_to_transfer_o;
  logic [C_S_AXI_DATA_WIDTH-1:0] end_addr_upper_o, end_addr_lower_o;
  logic [C_S_AXI_DATA_WIDTH-1:0] duty_cyc_target_o;

  state_t curr_state_o, next_state;
  logic [ 2:0] reset_counter;
  logic [23:0] duty_cyc_cnt;
  logic        axi_datamover_done;
  logic        external_trig_debounced;

  // Instantiation of Axi Bus Interface S_AXI
  hw_trigger_dma_v1_0_S_AXI #(
      .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
      .C_S_AXI_ADDR_WIDTH(C_S_AXI_ADDR_WIDTH)
  ) hw_trigger_dma_v1_0_S_AXI_inst (
      .command_o         (command_o),
      .start_addr_upper_o(start_addr_upper_o),
      .start_addr_lower_o(start_addr_lower_o),
      .byte_to_transfer_o(byte_to_transfer_o),
      .curr_state_i      (curr_state_i),
      .end_addr_upper_o  (end_addr_upper_o),
      .end_addr_lower_o  (end_addr_lower_o),
      .duty_cyc_target_o (duty_cyc_target_o),

      .S_AXI_ACLK   (s_axi_aclk),
      .S_AXI_ARESETN(s_axi_aresetn),
      .S_AXI_AWADDR (s_axi_awaddr),
      .S_AXI_AWPROT (s_axi_awprot),
      .S_AXI_AWVALID(s_axi_awvalid),
      .S_AXI_AWREADY(s_axi_awready),
      .S_AXI_WDATA  (s_axi_wdata),
      .S_AXI_WSTRB  (s_axi_wstrb),
      .S_AXI_WVALID (s_axi_wvalid),
      .S_AXI_WREADY (s_axi_wready),
      .S_AXI_BRESP  (s_axi_bresp),
      .S_AXI_BVALID (s_axi_bvalid),
      .S_AXI_BREADY (s_axi_bready),
      .S_AXI_ARADDR (s_axi_araddr),
      .S_AXI_ARPROT (s_axi_arprot),
      .S_AXI_ARVALID(s_axi_arvalid),
      .S_AXI_ARREADY(s_axi_arready),
      .S_AXI_RDATA  (s_axi_rdata),
      .S_AXI_RRESP  (s_axi_rresp),
      .S_AXI_RVALID (s_axi_rvalid),
      .S_AXI_RREADY (s_axi_rready)
  );

  // Convert state enum to 32-bit for AXI register
  assign curr_state_i  = {29'b0, curr_state_o};

  // S_AXIS ready signal - assuming always ready for now
  assign s_axis_tready = 1'b1;

  // External trigger debouncer
  ttl_capture #(
      .DEBOUNCE_COUNT(10)  // 10 clock cycles debounce
  ) u_ttl_capture (
      .clk       (axis_aclk),
      .aresetn   (axis_aresetn),
      .signal_in (external_trig),
      .signal_out(external_trig_debounced)
  );

  dma_fsm #(
      .RESET_TIME(7),
      .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
      .C_M_AXIS_TDATA_WIDTH(C_M_AXIS_TDATA_WIDTH)
  ) u_dma_fsm (
      .clk                     (axis_aclk),
      .resetn                  (axis_aresetn),
      // From AXI registers
      .command                 (command_o[CMD_WIDTH-1:0]),
      .start_addr_upper_i      (start_addr_upper_o),
      .start_addr_lower_i      (start_addr_lower_o),
      .byte_to_transfer_i      (byte_to_transfer_o),
      .end_addr_upper_i        (end_addr_upper_o),
      .end_addr_lower_i        (end_addr_lower_o),
      .duty_cyc_target_i       (duty_cyc_target_o),
      .external_trig_i         (external_trig_debounced),
      // Input/Output signals to AXI DataMover
      .mm2s_halt_cmplt_i       (mm2s_halt_cmplt),
      .axi_datamover_dma_done_i(s_axis_tready && s_axis_tvalid),
      .mm2s_err                (mm2s_err),
      .mm2s_halt               (mm2s_halt),
      .data_mover_aresetn      (data_mover_aresetn),
      // AXIS to AXI DataMover
      .m_axis_tdata            (m_axis_tdata),
      .m_axis_tvalid           (m_axis_tvalid),
      .m_axis_tready           (m_axis_tready),
      // Output signals
      .curr_state_o            (curr_state_o)
  );

endmodule




