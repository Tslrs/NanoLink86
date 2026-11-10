`timescale 1ns / 1ps

module bios_rom (
    input clk,
    input ce,
    input [10:0] addr,
    output reg [31:0] dout
);

    (* ram_style = "block" *) reg [31:0] mem [0:2047];

    initial begin
        $readmemh("bios.hex", mem);
    end

    always @(posedge clk) begin
        if (ce) begin
            dout <= mem[addr];
        end
    end

endmodule
