`timescale 1ns / 1ps

module bios_ram (
    input clk,
    input ce,
    input [3:0] we,
    input [10:0] addr,
    input [31:0] din,
    output reg [31:0] dout
);

    (* ram_style = "block" *) reg [7:0] ram0 [0:2047];
    (* ram_style = "block" *) reg [7:0] ram1 [0:2047];
    (* ram_style = "block" *) reg [7:0] ram2 [0:2047];
    (* ram_style = "block" *) reg [7:0] ram3 [0:2047];

    always @(posedge clk) begin
        if (ce) begin
            if (we[0]) ram0[addr] <= din[7:0];
            if (we[1]) ram1[addr] <= din[15:8];
            if (we[2]) ram2[addr] <= din[23:16];
            if (we[3]) ram3[addr] <= din[31:24];
            dout[7:0]   <= ram0[addr];
            dout[15:8]  <= ram1[addr];
            dout[23:16] <= ram2[addr];
            dout[31:24] <= ram3[addr];
        end
    end

    initial begin
        $readmemh("bios0.hex", ram0);
        $readmemh("bios1.hex", ram1);
        $readmemh("bios2.hex", ram2);
        $readmemh("bios3.hex", ram3);
    end

endmodule
