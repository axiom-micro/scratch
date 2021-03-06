#!/bin/env python3
from subprocess import check_output
from yaml import load
from time import sleep
from pll import optimal_pll_config
import sys

ar0330 = load(open("ar0330.yml"))

# extclk = 10000000
extclk = 24000000
i2c_bus = "0"
address = 16
ar0330_gpio_addr = 0x41200000

def gpio(addr, value=0xdeadbeef):
    cmd = "devmem2 0x%x w" % addr 
    if value != 0xdeadbeef:
        cmd += " 0x%x" % value

    check_output(cmd, shell=True)

ar0330_gpio = lambda value = 0xdeadbeef: gpio(ar0330_gpio_addr, value)

def i2ctransfer(cmd):
    output = check_output("i2ctransfer -y " + i2c_bus + " " + cmd, shell=True).decode("utf-8")

    if "error" in output:
        print("i2ctransfer errored: ", output)
        exit(-1)
    else:
        if output == '':
            return 0
        value = 0
        for (i, x) in enumerate(reversed(list(map(lambda x: int(x, 16), output.strip().split(' '))))):
            value += x * 256**i
            
        return value


def read(register_name, cam = ar0330):
    register = cam[register_name]
    addr = register["address"]
    count = register["width"]
    addr_high = addr >> 8
    addr_low = addr & 0xff
    transfer_cmd = "w2@%d %d %d r%d" % (address, addr_high, addr_low, count)
    return i2ctransfer(transfer_cmd)

def write(register_name, value, cam = ar0330):
    register = cam[register_name]
    addr = register["address"]
    count = register["width"]
    addr_high = addr >> 8
    addr_low = addr & 0xff
    write_value = []

    for v in range(1, count + 1):
        write_value.append("0x%x" % (value & 0xff))
        value >>= 8

    values = " ".join(reversed(write_value))
    transfer_cmd = "w%d@%d %d %d %s" % (2 + count, address, addr_high, addr_low, values)
    return(i2ctransfer(transfer_cmd))
    

# init 

# toggle reset (active low)
ar0330_gpio(0x7)
sleep(.1)
ar0330_gpio(0x0)
sleep(.1)
ar0330_gpio(0x7)
sleep(.1)
# magic init
write("magic_init_config", 0xa114)
write("magic_init_start", 0x0070)

# reset
# write("reset", 1)

sleep(.1)

# check chip_version 
chip_version = read("chip_version")
assert(chip_version == ar0330["chip_version"]["value"])

print("reserved_chiprev ", "0x%x" % read("reserved_chiprev"))
print("version ", "0x%x" % read("test_data_red"))

write("magic_patch1", 0x0146)
write("magic_patch2", 0x88bc)
write("magic_patch3", 0xaa63)
write("magic_patch4", 0x00a0)

# pll config for 12bit, 4 lane hispi
# vco_hispi_4lanes_12bit_clk = 588000000 # 588 MHz
vco_hispi_4lanes_12bit_clk = 588000000 # 588 MHz
# vco_hispi_4lanes_12bit_clk = 384000000 # 588 MHz
pll_config = optimal_pll_config(extclk, vco_hispi_4lanes_12bit_clk)
pre_pll_clk_div = pll_config["pre_pll_clk_div"] 
pll_multiplier = pll_config["pll_multiplier"] 

# taken from table in datasheet, no idea how to calculate on our own
vt_sys_clk_div =  1
vt_pix_clk_div =  6
op_sys_clk_div =  1
op_pix_clk_div = 12

write("vt_pix_clk_div", vt_pix_clk_div)
write("vt_sys_clk_div", vt_sys_clk_div)
write("pre_pll_clk_div", pre_pll_clk_div)
write("pll_multiplier", pll_multiplier)
write("op_pix_clk_div", op_pix_clk_div)
write("op_sys_clk_div", op_sys_clk_div)

# test lolol
# write("digital_test", 0x4000)

# pll lock time
sleep(.1)

# data format setting
## 0xc0c - 12bit raw uncompressed
write("data_format_bits", 0x0c0c)
# serial output format
## select hivcm (1V8)
write("datapath_select", 1 << 9);

## 0x0202 - 2 lane mipi
## 0x0304 - 4 lane hispi


# write("frame_preamble", 36);
# write("line_preamble", 12);
# write("mipi_timing_0", 0X2643);
# write("mipi_timing_1", 0X114e);
# write("mipi_timing_2", 0X2048);
# write("mipi_timing_3", 0X0186);
# write("mipi_timing_4", 0X8005);
# write("mipi_config_status", 0x2003);

# hispi enable, test pattern all ones 
# write("hispi_control_status", int("0000 0011 1101 0100".replace(' ', ''), 2))
# !!!! IMPORTANT  !!!! the 0x0400 bit toggles streaming s -> packetized sp
write("hispi_control_status", int("1000 0100 0000 0000".replace(' ', ''), 2))
write("mipi_config_status", 0xc)
#write("hispi_control_status", 0x8004)

write("serial_format", 0x0304)

# write("reset", 0)
# write("reset", int("0000 0000 0100 0000".replace(' ', ''), 2))


# set window
x_start = 6
y_start = 6
# 2304 × 1296
width = 2304
height = 1296

# write("x_addr_start", x_start)
# write("x_addr_end", x_start + width)
# write("y_addr_start", y_start)
# write("y_addr_end", y_start + height)
# write("line_length_pck", max(width, 1242))
# write("frame_length_lines", height + 12)

# walking one's
# write("test_pattern_mode", 3)
# solid color

# write("test_data_red", 0b111111111111)
# write("test_data_blue", 0b101010101010)
# write("test_data_greenb", 0b000000000000)
# write("test_data_greenr", 0b101010101010)

# write("test_data_red", 0b010101101010)
# write("test_data_blue", 0b010101101010)
# write("test_data_greenb", 0b010101101010)
# write("test_data_greenr", 0b010101101010)

if len(sys.argv) == 5:
    write("test_data_red", int(sys.argv[1], 0))
    write("test_data_blue", int(sys.argv[2], 0))
    write("test_data_greenb", int(sys.argv[3], 0))
    write("test_data_greenr", int(sys.argv[4], 0))
    write("test_pattern_mode", 1)
else:
    write("test_data_red", 0b111000011111)
    write("test_data_blue", 0b110001000111)
    write("test_data_greenb", 0b110100001111)
    write("test_data_greenr", 0b110100011111)
    write("test_pattern_mode", 1)

# enable streaming 
# write("reset", int("0000 0000 0000 0100".replace(' ', ''), 2))
write("hispi_timing", int("1 000 000 000 000 000".replace(' ', ''), 2))
sleep(.1)

# write("x_addr_start", 10)
# write("x_addr_end", 20)
# write("y_addr_start", 10)
# write("y_addr_end", 20)

write("mode_select", 1)

print("x_start", "%d" % read("x_addr_start"))
print("x_end", "%d" % read("x_addr_end"))
print("y_start", "%d" % read("y_addr_start"))
print("y_end", "%d" % read("y_addr_end"))
print("line_length_pck", "%d" % read("line_length_pck"))
print("frame_length_lines", "%d" % read("frame_length_lines"))
print("hispi_control_status", "0x%x" % read("hispi_control_status"))
print("hispi_timing", "0x%x" % read("hispi_timing"))
print("hispi_sync_patt", "0x%x" % read("hispi_sync_patt"))

while 1:
#    print("reset", "0x%x" % read("reset"))
#    print("control_status", "0x%x" % read("hispi_control_status"))
    print("hispi_timing", "0x%x" % read("hispi_timing"))
    print("frame_count", "%d" % read("frame_count"), end='\r')
#    print("frame_status", "0x%x" % read("frame_status"))
    sleep(1)


#define AR0330_VT_PIX_CLK_DIV				0x302a
#define AR0330_VT_SYS_CLK_DIV				0x302c
#define AR0330_PRE_PLL_CLK_DIV				0x302e
#define AR0330_PLL_MULTIPLIER				0x3030
#define AR0330_OP_PIX_CLK_DIV				0x3036
#define AR0330_OP_SYS_CLK_DIV				0x3038
#define AR0330_FRAME_COUNT				    0x303a

