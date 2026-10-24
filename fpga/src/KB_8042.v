//////////////////////////////////////////////////////////////////////////////////
//
// This file is part of the Next186 Soc PC project
// http://opencores.org/project,next186
//
// Filename: KB_8042.v
// Description: Part of the Next186 SoC PC project, keyboard/mouse PS2 controller
//		Simplified 8042 implementation
// Version 1.0
// Creation date: Jan2013
//
// Author: Nicolae Dumitrache 
// e-mail: ndumitrache@opencores.org
//
/////////////////////////////////////////////////////////////////////////////////
// 
// Copyright (C) 2013 Nicolae Dumitrache
// 
// This source file may be used and distributed without 
// restriction provided that this copyright statement is not 
// removed from the file and that any derivative work contains 
// the original copyright notice and the associated disclaimer.
// 
// This source file is free software; you can redistribute it 
// and/or modify it under the terms of the GNU Lesser General 
// Public License as published by the Free Software Foundation;
// either version 2.1 of the License, or (at your option) any 
// later version. 
// 
// This source is distributed in the hope that it will be 
// useful, but WITHOUT ANY WARRANTY; without even the implied 
// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
// PURPOSE. See the GNU Lesser General Public License for more 
// details. 
// 
// You should have received a copy of the GNU Lesser General 
// Public License along with this source; if not, download it 
// from http://www.opencores.org/lgpl.shtml 
// 
///////////////////////////////////////////////////////////////////////////////////
// Additional Comments: 
//
// http://www.computer-engineering.org/ps2keyboard/
// http://wiki.osdev.org/%228042%22_PS/2_Controller
// http://wiki.osdev.org/Mouse_Input
//
//	Primary connection
//		NET "PS2_CLK1" LOC = "W12" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW ;
//		NET "PS2_DATA1" LOC = "V11" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW ;
//	Secondary connection (requires Y-splitter cable)
//		NET "PS2_CLK2" LOC = "U11" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW ;
//		NET "PS2_DATA2" LOC = "Y12" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW ;
//////////////////////////////////////////////////////////////////////////////////
// 12Feb2018 - fix KB connection issue
//////////////////////////////////////////////////////////////////////////////////
`timescale 1ns / 1ps

module KB_Mouse_8042(
    input CS,
	 input WR,
    input cmd,			// 0x60 = data, 0x64 = cmd
	 input [7:0]din,
	 output [7:0]dout, 
	 input clk,			// cpu CLK
	 output I_KB,		// interrupt keyboard
	 output I_MOUSE,  // interrupt mouse
	 output reg CPU_RST = 0,
	 inout PS2_CLK1,
	 inout PS2_CLK2,
	 inout PS2_DATA1,
	 inout PS2_DATA2
    );
	 
//	status bit5 = MOBF (mouse to host buffer full - with OBF), bit4=INH, bit2(1-initialized ok), bit1(IBF-input buffer full - host to kb/mouse), bit0(OBF-output buffer full - kb/mouse to host)
	reg [3:0]cmdbyte = 4'b1100; // EN2,EN,INT2,INT
	reg wcfg = 1'b0;	// write config byte
	reg next_mouse = 1'b0;
	reg ctl_outb = 1'b0;
	reg [9:0]wr_data;
	reg [7:0]clkdiv128 = 0;
	reg [7:0]cnt100us = 0; // single delay counter for both kb and mouse
	reg wr_mouse = 1'b0;
	reg wr_kb = 1'b0;
	reg rd_kb = 1'b0;
	reg rd_mouse = 1'b0;
	reg OBF = 1'b0;
	reg MOBF = 1'b0;
	reg [7:0]s_data;

	wire [7:0]kb_data;
	wire [7:0]mouse_data;
	wire kb_data_out_ready;
	wire kb_data_in_ready;
	wire mouse_data_out_ready;
	wire mouse_data_in_ready;
	wire IBF = ((wr_kb | ~kb_data_in_ready) & ~cmdbyte[2]) | ((wr_mouse  | ~mouse_data_in_ready) & ~cmdbyte[3]);
	wire kb_shift;
	wire mouse_shift;
	
	assign dout = cmd ? {2'b00, MOBF, 1'b1, wcfg, 1'b1, IBF, OBF | MOBF | ctl_outb} : ctl_outb ? {2'b00, cmdbyte[3:2], 2'b00, cmdbyte[1:0]} : s_data; //MOBF ? mouse_data : kb_data;
	assign I_KB = OBF; 			// INT & OBF - always allow keyboard interrupts
	assign I_MOUSE = cmdbyte[1] & MOBF; 	// INT2 & MOBF
	
	PS2Interface Keyboard
	(
		.PS2_CLK(PS2_CLK1),
		.PS2_DATA(PS2_DATA1),
		.clk(clk),
		.rd(rd_kb),
		.wr(wr_kb),
		.data_in(wr_data[0]),
		.data_out(kb_data),
		.data_out_ready(kb_data_out_ready),
		.data_in_ready(kb_data_in_ready),
		.delay100us(cnt100us[7]),
		.data_shift(kb_shift),
		.clk_sample(clkdiv128[7])
	);

	PS2Interface #(.ENABLE(0)) Mouse	// mouse port not wired to any pin on Tang Nano 9K -> idle-high
	(
		.PS2_CLK(PS2_CLK2),
		.PS2_DATA(PS2_DATA2),
		.clk(clk),
		.rd(rd_mouse),
		.wr(wr_mouse),
		.data_in(wr_data[0]),
		.data_out(mouse_data),
		.data_out_ready(mouse_data_out_ready),
		.data_in_ready(mouse_data_in_ready),
		.delay100us(cnt100us[7]),
		.data_shift(mouse_shift),
		.clk_sample(clkdiv128[7])
	);
	
	always @(posedge clk) begin
		CPU_RST <= 0;
		if(~kb_data_in_ready) wr_kb <= 1'b0;
		if(~kb_data_out_ready) rd_kb <= 1'b0;
		if(~mouse_data_in_ready) wr_mouse <= 0;
		if(~mouse_data_out_ready) rd_mouse <= 1'b0;

		clkdiv128 <= clkdiv128[6:0] + 1'b1;
		if(CS & WR & ~cmd & ~wcfg) cnt100us <= 0; // reset 100us counter for PS2 writing
		else if(!cnt100us[7] & clkdiv128[7]) cnt100us <= cnt100us + 1'b1;
		
		
		if(~OBF & ~MOBF)
			if(kb_data_out_ready & ~rd_kb) begin	// keyboard always enabled
				OBF <= 1'b1;
				s_data <= kb_data;
			end else if(mouse_data_out_ready & ~rd_mouse & ~cmdbyte[3]) begin
				MOBF <= 1'b1;
				s_data <= mouse_data;
			end
		
		if(kb_shift | mouse_shift) wr_data <= {1'b1, wr_data[9:1]};
		
		if(CS) 
			if(WR)
				if(cmd)	// 0x64 write
					case(din)
						8'h20: ctl_outb <= 1'b1;	// read config byte
						8'h60: wcfg <= 1;			// write config byte
						8'ha7: cmdbyte[3] <= 1;	// disable mouse
						8'ha8: cmdbyte[3] <= 0;	// enable mouse
						8'had: cmdbyte[2] <= 0;	// keep kb always enabled
						8'hae: cmdbyte[2] <= 0;	// enable kb
						8'hd4: next_mouse <= 1;	//	write next byte to mouse
						/*8'hf0, 8'hf2, 8'hf4, 8'hf6, 8'hf8, 8'hfa, 8'hfc,*/ 8'hfe: CPU_RST <= 1; // CPU reset
					endcase 
				else begin	// 0x60 write
					if(wcfg) cmdbyte <= {din[5:4], din[1:0]};
					else begin
						next_mouse <= 0;
						wr_mouse <= next_mouse;
						wr_kb <= ~next_mouse;
						wr_data <= {~^din, din, 1'b0};
					end
					wcfg <= 0;
				end
			else 	// read data
				if(~cmd) begin	
					ctl_outb <= 1'b0;
					if(!ctl_outb) begin
						OBF <= 1'b0;
						MOBF <= 1'b0;
						rd_kb <= OBF;
						rd_mouse <= MOBF;
					end
				end
	end
endmodule


module PS2Interface #(parameter ENABLE = 1) (
	 inout PS2_CLK,
	 inout PS2_DATA,
	 input clk,
	 input rd,				// enable PS2 data reading
	 input wr,				// can write data from controller to PS2
	 input data_in,		// data from controller
	 input delay100us,
	 output [7:0]data_out,	// data from PS2
	 output reg data_out_ready = 0,	// PS2 received data ready
	 output reg data_in_ready = 1,	// PS2 sent data ready
	 output data_shift,
	 input clk_sample
	);
	
	assign PS2_CLK = 1'bz;	// Never pull lines low - host is pure receiver
	assign PS2_DATA = 1'bz;
	assign data_shift = 1'b0;

	reg [2:0] s_clk = 3'b111;
	reg [2:0] s_dat = 3'b111;
	reg [3:0] bit_cnt = 4'd0;
	reg [7:0] shift_reg = 8'd0;
	reg [7:0] rx_byte = 8'd0;
	reg [15:0] timeout_cnt = 16'd0;

	assign data_out = rx_byte;

	always @(posedge clk) begin
		if(rd) data_out_ready <= 1'b0;

		if(clk_sample) begin
			s_clk <= {s_clk[1:0], ENABLE ? PS2_CLK : 1'b1};
			s_dat <= {s_dat[1:0], ENABLE ? PS2_DATA : 1'b1};

			// Reset framing if clock line is idle HIGH for > 10ms
			// (4000 ticks * 2.56us = 10.24ms)
			if(s_clk[1]) begin
				if(timeout_cnt != 16'd4000)
					timeout_cnt <= timeout_cnt + 1'b1;
				else
					bit_cnt <= 4'd0;
			end else begin
				timeout_cnt <= 16'd0;
			end

			// Sample on falling edge of PS2_CLK (evaluated only on clk_sample!)
			if(s_clk[2:1] == 2'b10) begin
				timeout_cnt <= 16'd0;
				case(bit_cnt)
					4'd0: begin
						// Start bit (must be 0)
						if(~s_dat[1]) begin
							bit_cnt <= 4'd1;
						end
					end
					4'd1, 4'd2, 4'd3, 4'd4, 4'd5, 4'd6, 4'd7, 4'd8: begin
						// 8 data bits, LSB first
						shift_reg <= {s_dat[1], shift_reg[7:1]};
						bit_cnt <= bit_cnt + 1'b1;
					end
					4'd9: begin
						// Parity bit
						bit_cnt <= 4'd10;
					end
					4'd10: begin
						// Stop bit (must be 1)
						bit_cnt <= 4'd0;
						if(s_dat[1]) begin
							rx_byte <= shift_reg;
							data_out_ready <= 1'b1;
						end
					end
					default: bit_cnt <= 4'd0;
				endcase
			end
		end
	end
endmodule
