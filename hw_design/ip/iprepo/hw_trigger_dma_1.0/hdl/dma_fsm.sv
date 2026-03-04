// dma_fsm.sv
`timescale 1ns / 1ps
`include "fsm_def.sv"

module dma_fsm #(
    // how many cycles to wait in HALT_RST
    parameter int RESET_TIME           = 7,
    parameter int C_S_AXI_DATA_WIDTH   = 32,
    parameter int C_M_AXIS_TDATA_WIDTH = 104
) (
    input logic clk,
    input logic resetn,

    // From AXI registers
    input command_t                          command,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] start_addr_upper_i,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] start_addr_lower_i,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] byte_to_transfer_i,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] end_addr_upper_i,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] end_addr_lower_i,
    input logic                              external_trig_i,
    input logic     [C_S_AXI_DATA_WIDTH-1:0] duty_cyc_target_i,   // for duty cycling

    // Input/Output signals to AXI DataMover
    input  logic                            mm2s_halt_cmplt_i,
    input  logic                            axi_datamover_dma_done_i,
    input  logic                            mm2s_err,
    output logic                            mm2s_halt,
    output logic                            data_mover_aresetn,
    // AXIS to AXI DataMover
    output logic [C_M_AXIS_TDATA_WIDTH-1:0] m_axis_tdata,
    output logic                            m_axis_tvalid,
    input  logic                            m_axis_tready,

    // Output signals
    output state_t curr_state_o
);

  localparam BTT_WIDTH = 23, DUTY_COUNT_WIDTH = 24;
  state_t                 next_state;
  logic   [          2:0] reset_counter;
  logic   [BTT_WIDTH-1:0] byte_to_transfer_r;
  logic [2*C_S_AXI_DATA_WIDTH - 1:0] curr_addr, start_addr, end_addr;
  logic dma_addr_error;

  // For streaming and duty cycling
  logic [DUTY_COUNT_WIDTH-1:0] duty_cyc_cnt;
  logic [DUTY_COUNT_WIDTH-1:0] duty_cyc_target;
  assign duty_cyc_target = duty_cyc_target_i[DUTY_COUNT_WIDTH-1:0];

  assign start_addr = {start_addr_upper_i, start_addr_lower_i};
  assign end_addr = {end_addr_upper_i, end_addr_lower_i};

  // state register
  always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) curr_state_o <= S_IDLE;
    else curr_state_o <= next_state;
  end

  // reset counter
  always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) reset_counter <= '0;
    else if (curr_state_o == S_HALT_RST) reset_counter <= reset_counter + 1;
    else reset_counter <= '0;
  end

  // counters
  always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) begin
      curr_addr <= '0;
      byte_to_transfer_r <= '0;
      duty_cyc_cnt <= '0;
    end else begin
      case (curr_state_o)
        S_IDLE: begin
          curr_addr <= start_addr;
          byte_to_transfer_r <= byte_to_transfer_i[BTT_WIDTH-1:0];
          duty_cyc_cnt <= '0;
        end
        S_DMA_AXIS: begin
          if (m_axis_tready && m_axis_tvalid) begin
            curr_addr <= curr_addr + byte_to_transfer_r;
            byte_to_transfer_r <= byte_to_transfer_r;
            duty_cyc_cnt <= '0;
          end
        end
        S_DUTY: begin
          if (m_axis_tready && m_axis_tvalid) begin
            curr_addr <= curr_addr + byte_to_transfer_r;
            byte_to_transfer_r <= byte_to_transfer_r;
          end
          duty_cyc_cnt <= duty_cyc_cnt + 1;
        end
        default: begin
          curr_addr <= curr_addr;
          byte_to_transfer_r <= byte_to_transfer_r;
          duty_cyc_cnt <= '0;
        end  // Hold current address
      endcase
    end
  end

  assign dma_addr_error = (start_addr > end_addr);
  // next-state logic
  always_comb begin
    next_state = S_IDLE;
    case (curr_state_o)
      S_IDLE: begin
        case (command)
          CMD_STREAM:   next_state = S_CHECK;
          CMD_DUTY:     next_state = S_CHECK;
          CMD_DMA:      next_state = S_CHECK;
          CMD_EXT_TRIG: next_state = S_CHECK;
          CMD_RST:      next_state = S_HALT;
          default:      next_state = S_IDLE;
        endcase
      end

      S_CHECK: begin
        case (command)
          CMD_STREAM:   next_state = (dma_addr_error) ? S_ERROR : S_DMA_AXIS;
          CMD_DUTY:     next_state = (dma_addr_error) ? S_ERROR : S_DUTY;
          CMD_DMA:      next_state = (dma_addr_error) ? S_ERROR : S_DMA_AXIS;
          CMD_EXT_TRIG: next_state = (dma_addr_error) ? S_ERROR : S_EXT_TRIG;
          CMD_RST:      next_state = S_HALT;
          default:      next_state = S_IDLE;
        endcase
      end

      S_DUTY: begin
        if (duty_cyc_cnt >= duty_cyc_target) next_state = S_DMA_AXIS;
        else next_state = S_DUTY;

        if (command == CMD_RST) next_state = S_HALT;
      end

      S_EXT_TRIG: begin
        next_state = (external_trig_i) ? S_DMA_AXIS : S_EXT_TRIG;
        if (command == CMD_RST) next_state = S_HALT;
      end

      S_DMA_AXIS: begin
        if (m_axis_tvalid && m_axis_tready) begin
          next_state = S_DMA_WAIT;
        end else next_state = S_DMA_AXIS;

        if (command == CMD_RST) next_state = S_HALT;
      end

      S_DMA_WAIT: begin
        if (axi_datamover_dma_done_i) begin

          case (command)
            CMD_DMA: next_state = (curr_addr >= end_addr) ? S_DMA_DONE : S_DMA_AXIS;
            CMD_EXT_TRIG: next_state = (curr_addr >= end_addr) ? S_IDLE : S_EXT_TRIG;
            CMD_DUTY: next_state = (curr_addr >= end_addr) ? S_IDLE : S_DUTY;
            default: next_state = S_IDLE;
          endcase
        end else next_state = S_DMA_WAIT;

        if (command == CMD_STREAM)
          next_state = (curr_addr >= end_addr) ? S_IDLE : S_DMA_AXIS;  // bypass axi_datamover_dma_done_i
        if (command == CMD_RST) next_state = S_HALT;
      end

      S_DMA_DONE: next_state = (command == CMD_IDLE) ? S_IDLE : S_DMA_DONE;
      S_HALT:     next_state = (mm2s_halt_cmplt_i) ? S_HALT_RST : S_HALT;
      S_HALT_RST: next_state = (reset_counter == RESET_TIME) ? S_IDLE : S_HALT_RST;
      S_ERROR:    next_state = S_HALT;

      default: next_state = S_IDLE;
    endcase

    // Check mm2s_err at the end, override next_state if asserted
    if (mm2s_err) next_state = S_ERROR;
  end

  // control outputs
  assign mm2s_halt          = (curr_state_o == S_HALT);
  assign data_mover_aresetn = (curr_state_o == S_HALT_RST) ? 1'b0 : 1'b1;

  // output logic: AXI-Stream interface
  always_comb begin
    if (curr_state_o == S_DMA_AXIS && byte_to_transfer_r != '0) begin
      m_axis_tvalid = 1'b1;
      m_axis_tdata = {
        8'h00,
        curr_addr[2*C_S_AXI_DATA_WIDTH-1:C_S_AXI_DATA_WIDTH],  // upper 32
        curr_addr[C_S_AXI_DATA_WIDTH-1:0],  // lower 32
        1'b0,  // DRR
        1'b0,  // EOF
        6'b000000,  // DSA
        1'b1,  // INCR
        byte_to_transfer_r  // BTT[22:0]
      };
    end else begin
      m_axis_tvalid = 1'b0;
      m_axis_tdata  = '0;
    end
  end

endmodule




