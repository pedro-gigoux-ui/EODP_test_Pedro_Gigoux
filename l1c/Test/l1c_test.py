# CROSS VALIDATE L1C OUTPUTS

# PLOT L1B grids geometry and on top of that the L1C grid
# Cut in the central row and column
# PLOT GSD ACT
# PLOT GSD ALT


from common.io.l1cProduct import readL1c
from common.io.readGeodetic import readGeodetic
from config.l1cConfig import l1cConfig
import numpy as np
import os
import matplotlib.pyplot as plt

bands = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]
base_dir = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021"
test_dir = os.path.join(base_dir, "EODP-TS-L1C")
gm_dir = os.path.join(test_dir, "input", "gm_alt100_act_150")
out_mine = os.path.join(test_dir, "myout")
out_expected = os.path.join(test_dir, "output")
fig_dir = os.path.join(out_mine, "figures")
os.makedirs(fig_dir, exist_ok=True)

tolerance = 0.00001  # Relative differences shall be lower than 1e-3%


def relative_difference(mine, expected):
    difference = np.abs(mine - expected)
    scale = np.abs(expected)
    return np.where(scale > 0, difference / np.where(scale > 0, scale, 1), difference)


def ground_distance(lat1, lon1, lat2, lon2):
    R = 6371008.8
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# L1C files to compare: every l1c_toa_*.nc present in both output folders
files_expected = sorted(f for f in os.listdir(out_expected) if f.startswith("l1c_toa_") and f.endswith(".nc"))
files_mine = [f for f in os.listdir(out_mine) if f.endswith(".nc")]

toa_mine = {}
lat_mine = {}
lon_mine = {}
toa_expected = {}
lat_expected = {}
lon_expected = {}
for file in files_expected:
    if file not in files_mine:
        print("Missing in myout: " + file)
        continue
    toa_mine[file], lat_mine[file], lon_mine[file] = readL1c(out_mine, file)
    toa_expected[file], lat_expected[file], lon_expected[file] = readL1c(out_expected, file)

# L1B geometry (GM output)
lat_l1b, lon_l1b = readGeodetic(gm_dir, "geolocation.nc")


#Plot code
# L1B grid (red) and L1C grid (blue), central row and column of the L1B highlighted
first_file = list(toa_mine.keys())[0]
row = int(lat_l1b.shape[0] / 2)
col = int(lat_l1b.shape[1] / 2)

plt.figure(figsize=(12, 6))

plt.plot(lon_l1b.flatten(), lat_l1b.flatten(), '.r', markersize=1, label="L1B grid")
plt.plot(lon_mine[first_file], lat_mine[first_file], '.b', markersize=2, label="L1C grid (MGRS)")
plt.plot(lon_l1b[row, :], lat_l1b[row, :], '-k', label="L1B central row (ALT=" + str(row) + ")")
plt.plot(lon_l1b[:, col], lat_l1b[:, col], '--k', label="L1B central column (ACT=" + str(col) + ")")

plt.title("L1B and L1C grids")
plt.xlabel("Longitude [deg]")
plt.ylabel("Latitude [deg]")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "l1b_l1c_grids.png"))
plt.show()

# GSD ACT along the central row and GSD ALT along the central column
# gsd_act = ground_distance(lat_l1b[row, :-1], lon_l1b[row, :-1], lat_l1b[row, 1:], lon_l1b[row, 1:])
# gsd_alt = ground_distance(lat_l1b[:-1, col], lon_l1b[:-1, col], lat_l1b[1:, col], lon_l1b[1:, col])

nact=lat_l1b.shape[1] - 1
gsd_act = np.zeros(nact)
ialt = lat_l1b.shape[0] // 2
for ii in range(nact):
    gsd_act[ii] = ground_distance(lat_l1b[ialt,ii], lon_l1b[ialt,ii], lat_l1b[ialt,ii+1], lon_l1b[ialt,ii+1])


nalt = lat_l1b.shape[0] - 1
gsd_alt = np.zeros(nalt)
iact = lat_l1b.shape[1] // 2
for ii in range(nalt):
    gsd_alt[ii] = ground_distance(lat_l1b[ii,iact], lon_l1b[ii,iact], lat_l1b[ii+1,iact], lon_l1b[ii+1,iact])




mgrs_size = l1cConfig().mgrs_tile_size

for name, gsd, xlabel in [("GSD ACT", gsd_act, "Act_Columns"), ("GSD ALT", gsd_alt, "Alt_Lines")]:

    plt.figure(figsize=(12, 6))

    plt.plot(gsd, label=name + " (L1B)")
    #plt.axhline(mgrs_size, color='r', linestyle='--', label="L1C MGRS grid (" + str(mgrs_size) + " m)")

    plt.title(name)
    plt.xlabel(xlabel)
    plt.ylabel("GSD [m]")
    # Show the full GSD value on the axis (no "+4.51e1" offset on top)
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.5f'))
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, name.replace(" ", "_").lower() + ".png"))
    plt.show()

    print(name + ": mean = " + format(np.mean(gsd), ".2f") + " m, min = " + format(np.min(gsd), ".2f")
          + " m, max = " + format(np.max(gsd), ".2f") + " m")


#Cross Validation code
# The L1C points are not ordered (python set), so they are sorted by (lat, lon) before comparing
x = 0
for file in toa_mine:
    order_mine = np.lexsort((lon_mine[file], lat_mine[file]))
    order_expected = np.lexsort((lon_expected[file], lat_expected[file]))
    for var, mine, expected in [("toa", toa_mine[file], toa_expected[file]),
                                ("lat", lat_mine[file], lat_expected[file]),
                                ("lon", lon_mine[file], lon_expected[file])]:
        if mine.shape != expected.shape:
            print(file + " [" + var + "]: different size " + str(mine.shape) + " vs " + str(expected.shape) + " -> Not Equal")
            x = 1
            continue
        rel_diff = relative_difference(mine[order_mine], expected[order_expected])
        n_fail = np.sum(rel_diff > tolerance)
        if n_fail > 0:
            x = 1
        print(file + " [" + var + "]: max rel diff = " + format(np.max(rel_diff) * 100, ".3e") + " %, points out of tolerance = "
              + str(n_fail) + "/" + str(rel_diff.size) + " -> " + ("Not Equal" if n_fail > 0 else "Equal"))

if x == 1:
    print("Not Equal")
else:
    print("Equal")
