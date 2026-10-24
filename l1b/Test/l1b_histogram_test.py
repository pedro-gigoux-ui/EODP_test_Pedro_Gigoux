# CHECK L1B OUTPUTS WITH REAL DATA (E2E)
# PLOT THE HISTOGRAM OF THE L1B TOA FOR EACH BAND, MINE VERSUS THE EXPECTED (l1b_out)

from common.io.writeToa import readToa
import numpy as np
import os
import matplotlib.pyplot as plt

bands = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]
base_dir = r"C:/Users/pedro/Documents/EODP/EODP-TS-E2E"
out_mine = os.path.join(base_dir, "myout_l1b")
out_expected = os.path.join(base_dir, "l1b_out")
fig_dir = os.path.join(out_mine, "figures")
os.makedirs(fig_dir, exist_ok=True)

n_bins = 400

toa_mine = {}
toa_expected = {}
for band in bands:
    file = "l1b_toa_" + band + ".nc"
    if not os.path.isfile(os.path.join(out_mine, file)):
        print("Missing in myout_l1b: " + file)
        continue
    toa_mine[band] = readToa(out_mine, file)
    if os.path.isfile(os.path.join(out_expected, file)):
        toa_expected[band] = readToa(out_expected, file)


#Plot code
# One histogram per band, mine and expected with the same bins
for band in toa_mine:

    values = [toa_mine[band].flatten()]
    if band in toa_expected:
        values.append(toa_expected[band].flatten())
    bins = np.histogram_bin_edges(np.concatenate(values), bins=n_bins)

    plt.figure(figsize=(12, 6))

    if band in toa_expected:
        plt.hist(toa_expected[band].flatten(), bins=bins, alpha=0.5, label="Expected (l1b_out)")
    plt.hist(toa_mine[band].flatten(), bins=bins, histtype='step', linewidth=1.5, label="Mine (myout_l1b)")

    plt.title(band + " - L1B TOA histogram")
    plt.xlabel("Pixel Value")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "l1b_histogram_" + band + ".png"))
    plt.show()

# All my bands in the same figure
plt.figure(figsize=(12, 6))

for band in toa_mine:
    plt.hist(toa_mine[band].flatten(), bins=n_bins, histtype='step', linewidth=1.5, label=band)

plt.title("L1B TOA histogram - all bands (mine)")
plt.xlabel("Pixel Value")
plt.ylabel("Frequency")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "l1b_histogram_all_bands.png"))
plt.show()


#Statistics
def stats(toa):
    return ("mean = " + format(np.mean(toa), ".3f") + ", std = " + format(np.std(toa), ".3f")
            + ", min = " + format(np.min(toa), ".3f") + ", max = " + format(np.max(toa), ".3f")
            + ", negatives = " + format(100 * np.mean(toa < 0), ".2f") + " %")

for band in toa_mine:
    print(band + " mine:     " + stats(toa_mine[band]))
    if band in toa_expected:
        print(band + " expected: " + stats(toa_expected[band]))
