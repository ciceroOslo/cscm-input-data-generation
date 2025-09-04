import csv
import sys
import numpy as np
import pandas as pd

from misc_utils import initialise_empty_dictionaries, rf_component_renaming

##Initialising list of scenarios components and units
#
#scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
#scenario_list = ["historical-cmip5", "rcp60", "rcp26", "rcp85", "rcp45", "esm-pi-CO2pulse", "esm-pi-cdr-pulse", "esm-piControl", "esm-bell-1000PgC", "esm-bell-2000PgC", "esm-bell-750PgC" 
scenario_list = ["historical-cmip6", "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460", "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585", "rcp60", "rcp85", "rcp45", "rcp26","constant_zero"]
#scenario_list = ["ssp370-lowNTCF-aerchemmip", "ssp370-lowNTCF-gidden", "constant_zero"]
#scenario_list = ["historical", "constant_zero"]

#components = ["Albedo Change"]
ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt"}#"esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
#NBNB!! Check mappings for last four
comp_dict ={"Solar":"solar_RCMIP", "Volcanic":"VOLC_RCMIP", "Albedo Change":"LUCalbedo_RCMIP"}
#sys.exit(4)
years = []


def make_forcing_files(data_file, end_name="IGCC", components = None, scenario_list = None):
    if components is None:
        components = ["Solar", "Volcanic", "Albedo Change"]
    if scenario_list is None:
        scenario_list = ["IGCC"]
    full_data_dict = initialise_empty_dictionaries(scenario_dict=scenario_list, components=components)

    print(components)
    print(full_data_dict.keys())
    full_data_dict, years = get_forcing_data_from_file(data_file, full_data_dict)
    write_out_cscm_forcing_files(full_data_dict, years)


def get_forcing_data_from_file(data_file, full_data_dict):
    data = pd.read_csv(data_file)
    print(data.columns)
    print(data.index)
    print(data.head())
    years = data.iloc[:, 0].values
    print(years)
    for scen in full_data_dict.keys():
        for comp_o in full_data_dict[scen].keys():
            if comp_o in data.columns:
                comp = comp_o
            elif rf_component_renaming(comp_o) in data.columns:
                comp = rf_component_renaming(comp_o)
            else:
                print(f"No match found for component {comp_o}")
                continue 
            full_data_dict[scen][comp_o] = data[comp].values

    return full_data_dict, years


##Now printing the data to scenario files file:
def write_out_cscm_forcing_files(full_data_dict, years):
    for s in full_data_dict.keys():

        for c in full_data_dict[s].keys():
            fname =  "%s_%s.txt"%(comp_dict[c],s)
            with open(fname, 'w') as f:
                if len(full_data_dict[s][c])<1:
                    print("Scenario: %s Compontent: %s"%(s,c))
                    continue
                if c == 'Volcanic':
                    for i in range(len(years)):
                        line = ""
                        value = full_data_dict[s][c][i]
                        for i in range(12):
                            line = "%s%.6f \t"%(line,value)
                        f.write("%s \n"%line)
                    
                else:
                    for i in range(len(years)):
                        line = years[i] 
                        f.write("%s \n"%full_data_dict[s][c][i])
#shutil.copy('./VOLC_RCMIP_ssp119.txt', '../../input_RF/RFVOLC/VOLC_RCMIP_monavg_NH.txt')
#shutil.copy('./VOLC_RCMIP_ssp119.txt', '../../input_RF/RFVOLC/VOLC_RCMIP_monavg_SH.txt')
    
            
if __name__ == "__main__":
    make_forcing_files("data/ERF_best_1750-2024.csv")            
