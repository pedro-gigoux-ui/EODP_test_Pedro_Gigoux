# CROSS VALIDATE L1B OUTPUTS EQUALIZED
from bdb import Breakpoint

# PLOT FROM YOUR OUTPUTS THE EQUALISED OUTPUT VERSUS NOT EQUALISED VERSUS THE TRUTH
# TRUTH = EODP-TS-L1B\input\ism_toa_isrf_VNIR-0.nc

from common.io.writeToa import writeToa, readToa
import numpy as np
import os
import matplotlib.pyplot as plt

bands = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]
truth_line = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1B/input"
toa_truth = []
for band in bands:
    toa_truth.append(readToa(truth_line, "ism_toa_isrf_" + band + '.nc'))
out_eq = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1B/myout"
toa_eq = []
for band in bands:
    toa_eq.append(readToa(out_eq, "l1b_toa_" + band + '.nc'))

out_not_eq = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1B/myout_not_equalizer"
toa_not_eq = []
for band in bands:
    toa_not_eq.append(readToa(out_not_eq, "l1b_toa_" + band + '.nc'))

out_expected  = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1B/output"
toa_expected = []
for band in bands:
    toa_expected.append(readToa(out_expected, "l1b_toa_" + band + '.nc'))

for i, band in enumerate(bands):

    plt.figure(figsize=(12, 6))

    plt.plot(toa_truth[i][10], label="Truth")
    plt.plot(toa_eq[i][10], label="Equalizer")
    plt.plot(toa_not_eq[i][10], label="Not Equalizer")


    plt.title(band)
    plt.xlabel("Act_Columns")
    plt.ylabel("TOA")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

x=0
for i, band in enumerate(bands):
    for j in range(len(toa_expected[i])):
        for k in range(len(toa_expected[i][j])):
            difference = toa_eq[i][j][k] - toa_expected[i][j][k]
            #print(toa_eq[i][j][k])
            #print(toa_expected[i][j][k])
            if difference < 0:
                difference = -difference
            if (difference > 0.00001 * toa_expected[i][j][k]):
                x = 1
            if x == 1:
                break
        if x == 1:
            break
    if x == 1:
        break
if x == 1:
    print("Not Equal")
else:
    print("Equal")
