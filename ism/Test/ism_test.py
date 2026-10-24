# CROSS VALIDATE ISM OUTPUTS
#include the MTF plot (system MTF, and all the 6 MTFs), and specify which is the defining MTF for our system.


from common.io.writeToa import readToa
from common.io.readMat import readMat
from common.src.auxFunc import getIndexBand
from config.ismConfig import ismConfig
from ism.src.mtf import mtf
import numpy as np
import os
import logging
import io
import contextlib
import matplotlib.pyplot as plt

bands = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]
base_dir = r"C:/Users/pedro/Documents/EODP/EODP_TER_2021"
test_dir = os.path.join(base_dir, "EODP-TS-ISM")
out_mine = os.path.join(test_dir, "myout")
out_expected = os.path.join(test_dir, "output")
fig_dir = os.path.join(out_mine, "figures")
os.makedirs(fig_dir, exist_ok=True)

tolerance = 0.00001  # Relative differences shall be lower than 1e-3%

# ISM stages in processing order (prefix of the output files)
stages = ["ism_toa_isrf_", "ism_toa_optical_", "ism_toa_e_", "ism_toa_prnu_", "ism_toa_ds_",
          "ism_toa_detection_", "ism_toa_"]
mtf_names = ["Hdiff", "Hdefoc", "Hwfe", "Hdet", "Hsmear", "Hmotion", "Hsys"]


def relative_difference(mine, expected):
    # Where the reference is 0 the absolute difference is used
    difference = np.abs(mine - expected)
    scale = np.abs(expected)
    return np.where(scale > 0, difference / np.where(scale > 0, scale, 1), difference)


def quiet(read_function, directory, file):
    # Reads the file without printing the "Reading ..." / "Size of matrix ..." messages
    with contextlib.redirect_stdout(io.StringIO()):
        return read_function(directory, file)


# TOA files to compare: every ism_toa_*.nc present in both output folders
files_expected = [f for f in os.listdir(out_expected) if f.startswith("ism_toa_") and f.endswith(".nc")]
files_mine = [f for f in os.listdir(out_mine) if f.endswith(".nc")]
files_expected.sort(key=lambda f: (bands.index(f[-9:-3]), [f.startswith(s) for s in stages].index(True)))

toa_mine = {}
toa_expected = {}
for file in files_expected:
    if file not in files_mine:
        print("Missing in myout: " + file)
        continue
    toa_mine[file] = quiet(readToa, out_mine, file)
    toa_expected[file] = quiet(readToa, out_expected, file)

# MTFs: recomputed with my mtf class (they are not saved in myout) and compared with the H*.nc of the output
config = ismConfig()
myMtf = mtf(logging.getLogger("ism_test"), out_mine)
H_mine = {}
H_expected = {}
fn_act = {}
fn_alt = {}
for band in bands:
    nlines, ncolumns = toa_expected["ism_toa_" + band + ".nc"].shape
    lambd = config.wv[getIndexBand(band)]
    fn2D, fr2D, fn_act[band], fn_alt[band] = myMtf.freq2d(nlines, ncolumns, config.D, lambd, config.f, config.pix_size)
    H = {"Hdiff": myMtf.mtfDiffract(fr2D),
         "Hdefoc": myMtf.mtfDefocus(fr2D, config.defocus, config.f, config.D),
         "Hwfe": myMtf.mtfWfeAberrations(fr2D, lambd, config.kLF, config.wLF, config.kHF, config.wHF),
         "Hdet": myMtf.mtfDetector(fn2D),
         "Hsmear": myMtf.mtfSmearing(fn_alt[band], ncolumns, config.ksmear),
         "Hmotion": myMtf.mtfMotion(fn2D, config.kmotion)}
    H["Hsys"] = H["Hdiff"] * H["Hdefoc"] * H["Hwfe"] * H["Hdet"] * H["Hsmear"] * H["Hmotion"]
    for name in mtf_names:
        file = name + "_" + band + ".nc"
        H_mine[file] = H[name]
        if os.path.isfile(os.path.join(out_expected, file)):
            H_expected[file] = quiet(readMat, out_expected, file)


#Plot code
# MTF cuts ACT/ALT in the central position. The MTF is symmetric, so only [0, Nyquist] is plotted:
# the negative half of the frequencies is used because it includes -0.5 (the +0.5 is not sampled)
print("Defining MTF (lowest MTF at Nyquist)")
for i, band in enumerate(bands):
    ialt0 = np.argmin(np.abs(fn_alt[band]))
    iact0 = np.argmin(np.abs(fn_act[band]))
    cut_act = slice(0, iact0 + 1)
    cut_alt = slice(0, ialt0 + 1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    for name in mtf_names:
        H = H_mine[name + "_" + band + ".nc"]
        style = '-k' if name == "Hsys" else '-'
        axes[0].plot(np.abs(fn_act[band][cut_act]), H[ialt0, cut_act], style, label=name)
        axes[1].plot(np.abs(fn_alt[band][cut_alt]), H[cut_alt, iact0], style, label=name)

    for ax, cut in zip(axes, ["ACT", "ALT"]):
        ax.axvline(0.5, color='r', linestyle='--', label="Nyquist")
        ax.set_title(band + " - MTF cut " + cut)
        ax.set_xlabel("Normalised frequency f/(1/w) [-]")
        ax.set_ylabel("MTF")
        ax.grid(True)
        ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "mtf_cuts_" + band + ".png"))
    plt.show()

    # Defining MTF: the contributor (not Hsys) with the lowest value at Nyquist
    nyq_act = {name: H_mine[name + "_" + band + ".nc"][ialt0, 0] for name in mtf_names}
    nyq_alt = {name: H_mine[name + "_" + band + ".nc"][0, iact0] for name in mtf_names}
    defining_act = min(mtf_names[:-1], key=lambda name: nyq_act[name])
    defining_alt = min(mtf_names[:-1], key=lambda name: nyq_alt[name])
    print(band + ": ACT -> " + defining_act + ", ALT -> " + defining_alt)

# Final ISM TOA, central ALT line: mine versus expected
for i, band in enumerate(bands):
    file = "ism_toa_" + band + ".nc"
    if file not in toa_mine:
        continue
    idalt = int(toa_mine[file].shape[0] / 2)

    plt.figure(figsize=(12, 6))

    plt.plot(toa_expected[file][idalt], label="Expected (output)")
    plt.plot(toa_mine[file][idalt], '--', label="Mine (myout)")

    plt.title(band + " - ISM TOA, ALT=" + str(idalt))
    plt.xlabel("Act_Columns")
    plt.ylabel("TOA [DN]")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "ism_toa_" + band + "_alt" + str(idalt) + ".png"))
    plt.show()


#Cross Validation code
print("\nCross validation")
x = 0
for file, mine, expected in [(f, toa_mine[f], toa_expected[f]) for f in toa_mine] + \
                            [(f, H_mine[f], H_expected[f]) for f in H_expected]:
    if mine.shape != expected.shape:
        print(file + ": Not Equal (different size)")
        x = 1
        continue
    rel_diff = relative_difference(mine, expected)
    n_fail = np.sum(rel_diff > tolerance)
    if n_fail > 0:
        x = 1
    print(file + ": " + ("Not Equal" if n_fail > 0 else "Equal"))

if x == 1:
    print("\nRESULT: Not Equal")
else:
    print("\nRESULT: Equal")
