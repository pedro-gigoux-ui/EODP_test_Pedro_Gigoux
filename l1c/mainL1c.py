
# MAIN FUNCTION TO CALL THE L1C MODULE

from l1c.src.l1c import l1c

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = r'C:/Users/pedro/Documents/EODP/EODP_test_Pedro_Gigoux/auxiliary'
# GM dir + L1B dir
indir = r'C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1C/input/gm_alt100_act_150,C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1C/input/l1b_output'
#indir = r'C:/Users/pedro/Documents/EODP/EODP-TS-E2E/gm_out,C:/Users/pedro/Documents/EODP/EODP-TS-E2E/myout_l1b'
outdir = r'C:/Users/pedro/Documents/EODP/EODP_TER_2021/EODP-TS-L1C/myout'
#outdir = r'C:/Users/pedro/Documents/EODP/EODP-TS-E2E/myout_l1c'

# Initialise the ISM
myL1c = l1c(auxdir, indir, outdir)
myL1c.processModule()
