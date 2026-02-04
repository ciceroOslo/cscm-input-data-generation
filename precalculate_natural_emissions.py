import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ciceroscm import concentrations_emissions_handler, input_handler

# Change data_dir to get inputs from somewhere else
data_dir = os.path.join(os.path.dirname(__file__), "..", "ciceroscm", "tests", "test-data")

# Change these years if you wish to adjust the estimated time range:
nyend = 2500
nyend_hist = 2023
nystart = 1750

# Choose the lifetime mode assumption for methane
# lifetime_modes = ["TAR", "CONSTANT_12", "CONSTANT_from_file", "WIGLEY"]
# Change this line to your preferred lifetime:
lf_mode = "TAR"
#lf_mode = "CONSTANT_12"
#lf_mode = "WIGLEY"

pamset = {"nyend": nyend_hist, "nystart": nystart, "lifetime_mode": lf_mode}
ih_temp = input_handler.InputHandler(pamset)

# If you want to fit from different data input files, then change these paths
#em_data = ih_temp.read_emissions(os.path.join(data_dir, "ssp245_em_RCMIP.txt"))
#conc_data =  input_handler.read_inputfile(os.path.join(data_dir, "ssp245_conc_RCMIP.txt"))
#gaspam_data = input_handler.read_components(os.path.join(data_dir, "gases_vupdate_2022_AR6.txt"))
em_data = ih_temp.read_emissions("../cscm-calibration/data/calibration_data_Sep2025/historical_em_gases_vupdate_2024_WMO_added_new.txt")
conc_data =  input_handler.read_inputfile("../cscm-calibration/data/calibration_data_Sep2025/igcc_historical_conc_gases_vupdate_2024_WMO_added_new.txt")
gaspam_data = input_handler.read_components(os.path.join(data_dir, "gases_vupdate_2024_WMO_added_new.txt"))

def get_lifetime(tracer, yr, ce_handler):
    """
    Get lifetime for tracer as calculated in the code
    """
    q = 1 / ce_handler.df_gas["TAU1"][tracer]
    if tracer != "CH4":
        return q
    if (yr-1) < ce_handler.conc_in.index[0]:
        q = ce_handler.methane_lifetime(q, ce_handler.conc_in[tracer][yr], yr)
    else:
        q = ce_handler.methane_lifetime(q, ce_handler.conc_in[tracer][yr-1], yr)
    return q

def ode_get_nat_em_timeseries(tau, beta, em_series, conc_series, ce_handler, sp="N2O"):
    """
    Use ode exact solution backwards to get natural emissions
    needed to match the concentrations from anthropogenic emissions
    series
    """
    lifetime_series = np.zeros(len(conc_series))
    conc_extended = np.concatenate(([conc_series[0]], conc_series), axis=0)
    if sp != "CH4":
        em_nat_hist = (
            beta
            / tau
            / (1 - np.exp(-1 / tau))
            * (conc_series - conc_extended[:-1] * np.exp(-1 / tau))
            - em_series[: len(conc_series)]
        )
    else:
        em_nat_hist = np.zeros(len(conc_series))
        for i in range(len(conc_series)):
            q = get_lifetime(sp, i + nystart, ce_handler)
            lifetime_series[i] = 1/q
            em_nat_hist[i] = (
                beta
                * q
                / (1 - np.exp(-q))
                * (conc_series[i] - conc_extended[i] * np.exp(-q))
                - em_series[i]
            )
    return em_nat_hist, lifetime_series


nat_ch4_data = pd.DataFrame(
    data={"CH4": np.ones(nyend - nystart + 1) * 242.09},
    index=np.arange(nystart, nyend + 1),
)
nat_n2o_data = pd.DataFrame(
    data={"N2O": np.ones(nyend - nystart + 1) * 11.7027},
    index=np.arange(nystart, nyend + 1),
)
print(pamset)
ce_handler = concentrations_emissions_handler.ConcentrationsEmissionsHandler(
    input_handler.InputHandler(
        {
            "gaspam_data": gaspam_data,
            "emissions_data": em_data,
            "concentrations_data": conc_data,
            "nat_ch4_data": nat_ch4_data,
            "nat_n2o_data": nat_n2o_data,
            "nystart": nystart,
            "nyend": nyend_hist,
        }
    ),
    pamset,
)
print(ce_handler.pamset)

ce_handler.reset_with_new_pams(ce_handler.pamset)
print(ce_handler.pamset)
#sys.exit(4)
conc_y0 = ce_handler.conc_in.index.values[0]

# In principle you could use this for other tracers as well or do just a single tracer at a time
fig, ax = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle("Natural emissions calculated from ODE solution with lifetime mode: " + lf_mode)

tracers = ["N2O", "CH4"]
year_out = range(nystart, nyend + 1)
for j, tracer in enumerate(tracers):
    tau = ce_handler.df_gas["TAU1"][tracer]
    beta = ce_handler.df_gas["BETA"][tracer]
    em_nat_const = ce_handler.df_gas["NAT_EM"][tracer]
    em_series = ce_handler.emis[tracer].values
    conc_series = ce_handler.conc_in[tracer][
        nystart - conc_y0 : nyend_hist + 1 - conc_y0
    ].values

    # Option for old version calculation (comment in next three lines for old version):
    # em_nat_hist_old = old_get_nat_em_timeseries(tau, beta, em_nat_const, em_series, conc_series, sp=tracer)
    # em_nat_out_old = np.concatenate((em_nat_hist_old,  np.full((len(year_out)-len(em_nat_hist_old)), np.mean(em_nat_hist_old[-11:]),np.double)), axis=0)
    # np.savetxt(f"natemis_{tracer}_old_method_from_rcmip.txt", em_nat_out_old,fmt='%1.4f')

    # Option for new (recommended) version calculation (comment out next three lines for old version):
    em_nat_hist_ode, lifetime_hist = ode_get_nat_em_timeseries(tau, beta, em_series, conc_series, ce_handler, sp=tracer)


    #print(len(year_out))
    #print(len(em_nat_hist_ode))
    em_nat_out_ode = np.concatenate((em_nat_hist_ode,  np.full((len(year_out)-len(em_nat_hist_ode)), np.mean(em_nat_hist_ode[-11:]),np.double)), axis=0)
     # Plot results
    ax[0, j].plot(year_out[:], em_nat_out_ode, label="Calculated natural emissions")
    ax[0, j].plot(year_out[:len(em_series)], em_series, label="Input anthropogenic emissions")
    ax[0,j].set_xlim(1850, year_out[len(em_nat_hist_ode) + 30])
    ax[0,j].set_title(f"Natural emissions {tracer}")
    ax[0, j].set_xlabel("Year")
    ax[0, j].set_ylabel(f"Natural emissions of {tracer} (Gt {tracer}/yr)")
    ax[0, j].legend()

    ax[1, j].plot(year_out[:len(lifetime_hist)], lifetime_hist, label=f"Lifetime {lf_mode}")
    ax[1,j].set_xlabel("Year")
    ax[1,j].set_xlim(1850, year_out[len(em_nat_hist_ode)])
    ax[1,j].set_ylabel(f"Lifetime of {tracer} (years)")
    ax[1, j].set_title(f"Lifetime {tracer}")

    #print(len(em_nat_out_ode))
    #print(em_nat_out_ode)
    np.savetxt(f"natemis_{tracer}_ode_method_from_Sep2025_updates.txt", em_nat_out_ode,fmt='%1.4f')

fig.tight_layout()
fig.savefig(f"natural_emissions_{lf_mode}_method_from_Sep2025_updates.png")


