#!/bin/python3

from sys import argv
from pll import optimal_pll_config
from yaml import load
from subprocess import check_output

ar0330 = load(open("ar0330.yml"))

gain_settings = [
    [1, 0, 0],
    [1.03, 0, 1],
    [1.07, 0, 2],
    [1.1, 0, 3],
    [1.14, 0, 4],
    [1.19, 0, 5],
    [1.23, 0, 6],
    [1.28, 0, 7],
    [1.33, 0, 8],
    [1.39, 0, 9],
    [1.45, 0, 10],
    [1.52, 0, 11],
    [1.6, 0, 12],
    [1.68, 0, 13],
    [1.78, 0, 14],
    [1.88, 0, 15],
    [2, 1, 0],
    [2.13, 1, 2],
    [2.29, 1, 4],
    [2.46, 1, 6],
    [2.67, 1, 8],
    [2.91, 1, 10],
    [3.2, 1, 12],
    [3.56, 1, 14],
    [4, 2, 0],
    [4.57, 2, 4],
    [5.33, 2, 8],
    [6.4, 2, 12],
    [8, 3, 0]
]

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

def get_close(desired):
    for (gain, coarse, fine) in gain_settings:
        if gain > desired:
            return (gain, coarse, fine)

if __name__ == "__main__":
    desired_gain = float(argv[1])
    actual, coarse, fine = get_close(desired_gain)
    write("analog_gain",  int(format(fine, '04b') + format(coarse, '02b'), base=2)
    print(actual)
