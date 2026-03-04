// fsm_def.sv
`timescale 1ns / 1ps
`ifndef FSM_DSF_SV
`define FSM_DSF_SV

// Command width constant
parameter int CMD_WIDTH = 3;

typedef enum logic [2:0] {
  CMD_IDLE     = 3'b000,
  CMD_EXT_TRIG = 3'b001,
  CMD_DMA      = 3'b010,
  CMD_STREAM   = 3'b011,
  CMD_DUTY     = 3'b100,
  CMD_RST      = 3'b101
} command_t;


typedef enum logic [3:0] {
  S_IDLE     = 4'h0,
  S_HALT     = 4'h1,
  S_HALT_RST = 4'h2,
  S_ERROR    = 4'h3,
  S_DMA_AXIS = 4'h4,
  S_DMA_WAIT = 4'h5,
  S_EXT_TRIG = 4'h6,
  S_DMA_DONE = 4'h7,
  S_DUTY     = 4'h8,
  S_CHECK    = 4'h9
} state_t;

`endif
