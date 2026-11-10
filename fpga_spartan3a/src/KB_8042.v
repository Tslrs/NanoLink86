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
`timescale 1ns / 1ps

module KB_Mouse_8042(
    input CS,
	 input WR,
    input cmd,			// 0x60 = data, 0x64 = cmd
	 input [7:0]din,
	 output OE,
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
	parameter XLAT = 1;		// 1 = translate keyboard scan code set 2 -> set 1 (like a PC/AT 8042); the BIOS must then not switch the keyboard to set 1
	parameter KB_NOINHIBIT = 1;	// 1 = never hold the keyboard clock low while idle (transmit-only, push-pull keyboard such as NanoLink86)
	 
//	status bit5 = MOBF (mouse to host buffer full - with OBF), bit4=INH, bit2(1-initialized ok), bit1(IBF-input buffer full - host to kb/mouse), bit0(OBF-output buffer full - kb/mouse to host)
	reg [3:0]cmdbyte = 4'b1100; // EN2,EN,INT2,INT
	reg wcfg = 0;	// write config byte
	reg next_mouse = 0;
	reg ctl_outb = 0;
	reg [9:0]wr_data;
	reg [14:0]cnt100us = 0; // single delay counter for both kb and mouse
	reg wr_mouse = 0;
	reg wr_kb = 0;
	reg rd_kb = 0;
	reg rd_mouse = 0;
	reg OBF = 0;
	reg MOBF = 0;

	wire [7:0]kb_data;
	wire [7:0]mouse_data;
	wire kb_data_out_ready;
	wire kb_data_in_ready;
	wire mouse_data_out_ready;
	wire mouse_data_in_ready;
	wire IBF = ((wr_kb | ~kb_data_in_ready) & ~cmdbyte[2]) | ((wr_mouse  | ~mouse_data_in_ready) & ~cmdbyte[3]);
	reg kb_brk = 0;			// set 2 break prefix (F0) seen
	reg [7:0]xlat_s1;
	always @(*) begin
		case(kb_data[6:0])
			7'h00: xlat_s1 = 8'hff;
			7'h01: xlat_s1 = 8'h43;
			7'h02: xlat_s1 = 8'h41;
			7'h03: xlat_s1 = 8'h3f;
			7'h04: xlat_s1 = 8'h3d;
			7'h05: xlat_s1 = 8'h3b;
			7'h06: xlat_s1 = 8'h3c;
			7'h07: xlat_s1 = 8'h58;
			7'h08: xlat_s1 = 8'h64;
			7'h09: xlat_s1 = 8'h44;
			7'h0a: xlat_s1 = 8'h42;
			7'h0b: xlat_s1 = 8'h40;
			7'h0c: xlat_s1 = 8'h3e;
			7'h0d: xlat_s1 = 8'h0f;
			7'h0e: xlat_s1 = 8'h29;
			7'h0f: xlat_s1 = 8'h59;
			7'h10: xlat_s1 = 8'h65;
			7'h11: xlat_s1 = 8'h38;
			7'h12: xlat_s1 = 8'h2a;
			7'h13: xlat_s1 = 8'h70;
			7'h14: xlat_s1 = 8'h1d;
			7'h15: xlat_s1 = 8'h10;
			7'h16: xlat_s1 = 8'h02;
			7'h17: xlat_s1 = 8'h5a;
			7'h18: xlat_s1 = 8'h66;
			7'h19: xlat_s1 = 8'h71;
			7'h1a: xlat_s1 = 8'h2c;
			7'h1b: xlat_s1 = 8'h1f;
			7'h1c: xlat_s1 = 8'h1e;
			7'h1d: xlat_s1 = 8'h11;
			7'h1e: xlat_s1 = 8'h03;
			7'h1f: xlat_s1 = 8'h5b;
			7'h20: xlat_s1 = 8'h67;
			7'h21: xlat_s1 = 8'h2e;
			7'h22: xlat_s1 = 8'h2d;
			7'h23: xlat_s1 = 8'h20;
			7'h24: xlat_s1 = 8'h12;
			7'h25: xlat_s1 = 8'h05;
			7'h26: xlat_s1 = 8'h04;
			7'h27: xlat_s1 = 8'h5c;
			7'h28: xlat_s1 = 8'h68;
			7'h29: xlat_s1 = 8'h39;
			7'h2a: xlat_s1 = 8'h2f;
			7'h2b: xlat_s1 = 8'h21;
			7'h2c: xlat_s1 = 8'h14;
			7'h2d: xlat_s1 = 8'h13;
			7'h2e: xlat_s1 = 8'h06;
			7'h2f: xlat_s1 = 8'h5d;
			7'h30: xlat_s1 = 8'h69;
			7'h31: xlat_s1 = 8'h31;
			7'h32: xlat_s1 = 8'h30;
			7'h33: xlat_s1 = 8'h23;
			7'h34: xlat_s1 = 8'h22;
			7'h35: xlat_s1 = 8'h15;
			7'h36: xlat_s1 = 8'h07;
			7'h37: xlat_s1 = 8'h5e;
			7'h38: xlat_s1 = 8'h6a;
			7'h39: xlat_s1 = 8'h72;
			7'h3a: xlat_s1 = 8'h32;
			7'h3b: xlat_s1 = 8'h24;
			7'h3c: xlat_s1 = 8'h16;
			7'h3d: xlat_s1 = 8'h08;
			7'h3e: xlat_s1 = 8'h09;
			7'h3f: xlat_s1 = 8'h5f;
			7'h40: xlat_s1 = 8'h6b;
			7'h41: xlat_s1 = 8'h33;
			7'h42: xlat_s1 = 8'h25;
			7'h43: xlat_s1 = 8'h17;
			7'h44: xlat_s1 = 8'h18;
			7'h45: xlat_s1 = 8'h0b;
			7'h46: xlat_s1 = 8'h0a;
			7'h47: xlat_s1 = 8'h60;
			7'h48: xlat_s1 = 8'h6c;
			7'h49: xlat_s1 = 8'h34;
			7'h4a: xlat_s1 = 8'h35;
			7'h4b: xlat_s1 = 8'h26;
			7'h4c: xlat_s1 = 8'h27;
			7'h4d: xlat_s1 = 8'h19;
			7'h4e: xlat_s1 = 8'h0c;
			7'h4f: xlat_s1 = 8'h61;
			7'h50: xlat_s1 = 8'h6d;
			7'h51: xlat_s1 = 8'h73;
			7'h52: xlat_s1 = 8'h28;
			7'h53: xlat_s1 = 8'h74;
			7'h54: xlat_s1 = 8'h1a;
			7'h55: xlat_s1 = 8'h0d;
			7'h56: xlat_s1 = 8'h62;
			7'h57: xlat_s1 = 8'h6e;
			7'h58: xlat_s1 = 8'h3a;
			7'h59: xlat_s1 = 8'h36;
			7'h5a: xlat_s1 = 8'h1c;
			7'h5b: xlat_s1 = 8'h1b;
			7'h5c: xlat_s1 = 8'h75;
			7'h5d: xlat_s1 = 8'h2b;
			7'h5e: xlat_s1 = 8'h63;
			7'h5f: xlat_s1 = 8'h76;
			7'h60: xlat_s1 = 8'h55;
			7'h61: xlat_s1 = 8'h56;
			7'h62: xlat_s1 = 8'h77;
			7'h63: xlat_s1 = 8'h78;
			7'h64: xlat_s1 = 8'h79;
			7'h65: xlat_s1 = 8'h7a;
			7'h66: xlat_s1 = 8'h0e;
			7'h67: xlat_s1 = 8'h7b;
			7'h68: xlat_s1 = 8'h7c;
			7'h69: xlat_s1 = 8'h4f;
			7'h6a: xlat_s1 = 8'h7d;
			7'h6b: xlat_s1 = 8'h4b;
			7'h6c: xlat_s1 = 8'h47;
			7'h6d: xlat_s1 = 8'h7e;
			7'h6e: xlat_s1 = 8'h7f;
			7'h6f: xlat_s1 = 8'h6f;
			7'h70: xlat_s1 = 8'h52;
			7'h71: xlat_s1 = 8'h53;
			7'h72: xlat_s1 = 8'h50;
			7'h73: xlat_s1 = 8'h4c;
			7'h74: xlat_s1 = 8'h4d;
			7'h75: xlat_s1 = 8'h48;
			7'h76: xlat_s1 = 8'h01;
			7'h77: xlat_s1 = 8'h45;
			7'h78: xlat_s1 = 8'h57;
			7'h79: xlat_s1 = 8'h4e;
			7'h7a: xlat_s1 = 8'h51;
			7'h7b: xlat_s1 = 8'h4a;
			7'h7c: xlat_s1 = 8'h37;
			7'h7d: xlat_s1 = 8'h49;
			7'h7e: xlat_s1 = 8'h46;
			7'h7f: xlat_s1 = 8'h54;
		endcase
		if(kb_data[7]) xlat_s1 = kb_data == 8'h83 ? 8'h41 : kb_data == 8'h84 ? 8'h54 : kb_data;
	end
	wire [7:0]kb_xdata = XLAT ? {kb_brk | xlat_s1[7], xlat_s1[6:0]} : kb_data;
	wire [7:0]inb = ctl_outb ? {2'b00, cmdbyte[3:2], 2'b00, cmdbyte[1:0]} : MOBF ? mouse_data : kb_xdata;
	wire kb_shift;
	wire mouse_shift;
	
	assign OE = CS & ~WR;
	assign dout = cmd ? {2'b00, MOBF, 1'b1, wcfg, 1'b1, IBF, OBF | MOBF | ctl_outb} : inb;
	assign I_KB = cmdbyte[0] & OBF; 			// INT & OBF
	assign I_MOUSE = cmdbyte[1] & MOBF; 	// INT2 & MOBF
	
	PS2Interface #(.NOINHIBIT(KB_NOINHIBIT)) Keyboard
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
		.delay100us(cnt100us[14]),
		.data_shift(kb_shift)
	);

	PS2Interface Mouse
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
		.delay100us(cnt100us[14]),
		.data_shift(mouse_shift)
	);
	
	always @(posedge clk) begin
		CPU_RST <= 0;
		if(~kb_data_in_ready) wr_kb <= 0;
		if(~kb_data_out_ready) rd_kb <= 1'b0;
		if(~mouse_data_in_ready) wr_mouse <= 0;
		if(~mouse_data_out_ready) rd_mouse <= 1'b0;

		if(CS & WR & ~cmd & ~wcfg) cnt100us <= 0; // reset 100us counter for PS2 writing
		else if(!cnt100us[14]) cnt100us <= cnt100us + 1;
		
		if(~OBF & ~MOBF)
			if(kb_data_out_ready & ~rd_kb & ~cmdbyte[2]) begin
				if(XLAT && kb_data == 8'hf0) begin	// swallow the break prefix, flag the next code as a break code
					kb_brk <= 1'b1;
					rd_kb <= 1'b1;
				end else OBF <= 1'b1;
			end
			else MOBF <= mouse_data_out_ready & ~rd_mouse & ~cmdbyte[3];
		
		if(kb_shift | mouse_shift) wr_data <= {1'b1, wr_data[9:1]};
		
		if(CS) 
			if(WR)
				if(cmd)	// 0x64 write
					case(din)
						8'h20: ctl_outb <= 1;	// read config byte
						8'h60: wcfg <= 1;			// write config byte
						8'ha7: cmdbyte[3] <= 1;	// disable mouse
						8'ha8: cmdbyte[3] <= 0;	// enable mouse
						8'had: cmdbyte[2] <= 1;	// disable kb
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
//						cnt100us <= 0;	// reset 100us counter for PS2 writing
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
						if(OBF) kb_brk <= 1'b0;
					end
				end
	end
endmodule


module PS2Interface(
	 inout PS2_CLK,
	 inout PS2_DATA,
	 input clk,
	 input rd,				// enable PS2 data reading
	 input wr,				// can write data from controller to PS2
	 input data_in,		// data from controller
	 input delay100us,
	 output [7:0]data_out,	// data from PS2
	 output reg data_out_ready = 1,	// PS2 received data ready
	 output reg data_in_ready = 1,	// PS2 sent data ready
	 output data_shift
	);
	parameter NOINHIBIT = 0;
	reg [1:0]s_clk = 2'b11;
	reg [9:0]data = 0;
	reg rd_progress = 0;
	
	assign PS2_CLK = (((~data_out_ready | NOINHIBIT) & data_in_ready) | (~data_in_ready & delay100us)) ? 1'bz : 1'b0;
	assign PS2_DATA = (data_in_ready | data_in | ~delay100us) ? 1'bz : 1'b0;
	assign data_out = data[7:0];
	assign data_shift = ~data_in_ready && delay100us && s_clk == 2'b10;

	always @(posedge clk) begin
		s_clk <= {s_clk[0], PS2_CLK};
		if(data_out_ready) rd_progress <= 1'b0;

		if(~data_in_ready) begin	// send data to PS2
			if(data_shift) data_in_ready <= data_in ^ PS2_DATA;
		end else if(wr && ~rd_progress) begin	// initiate data sending to PS2
			data_in_ready <= 1'b0;
		end else if(~data_out_ready) begin	// receive data from PS2
			if(s_clk == 2'b10) begin
				rd_progress <= 1'b1;
				if(!rd_progress) data <= 10'b1111111111;
			end
			if(s_clk == 2'b01 && rd_progress) {data, data_out_ready} <= {PS2_DATA, data[9:1], ~data[0]}; // receive is ended by the stop bit
		end else if(rd) begin	// initiate data receiving from PS2
//			data <= 10'b1111111111;	
			data_out_ready <= 1'b0;
		end	
	end
endmodule
