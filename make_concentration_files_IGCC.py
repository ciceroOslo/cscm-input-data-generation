import csv
import sys
import numpy as np
import pandas as pd
from interpolation_of_input import interpolate_data
from interpolation_of_input import interpolate_data_wconstant_start
from misc_utils import unit_conv_factor_long_name, initialise_empty_dictionaries, initialise_comp_unit_dict, component_renaming, lift_scenariolist_from_datafile


def make_single_IGCC_concentrations_file(gaspam_file, igcc_file, ssp_fudge_file=None):


    print("Starting")
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file, emissions=False)
    print("Done components and units")
    if ssp_fudge_file is None:
        full_data_dict, years = read_concentrations_datafile(igcc_file, components, units)
    else:
        ssp_name = ssp_fudge_file.split("/")[-1].split("_")[0]
        full_data_dict, years = read_concentrations_datafile(igcc_file, components, units, scen=f"igcc_historical_fudge_w_{ssp_name}")

        full_data_dict, years = fudge_with_ssp(full_data_dict, years, ssp_fudge_file)
    print("Done getting data")
    write_concentration_file_for_each_scenario(full_data_dict, components, units, years, f"conc_{gaspam_file.split('/')[-1].split('.')[0]}.txt")
    print("Done writing to files")

def fudge_with_ssp(full_data_dict, years, ssp_fudge_file):
    ssp_df = pd.read_csv(ssp_fudge_file, delimiter = '\t', index_col= 0, skiprows=[1,2,3])
    ssp_df.columns = ssp_df.columns.str.strip()
    print(ssp_df.head())
    print(ssp_df.columns)
    print("Fudging with ssp-file is currently unimplemented")
    year_start_fudge_index = years[-1] - ssp_df.index[0] + 1 
    years = np.append(years, ssp_df.index[year_start_fudge_index:].values)
    
    for scen in full_data_dict.keys():
        print(len(full_data_dict[scen]["HCFC-123"]))
        for comp in full_data_dict[scen].keys():
            if comp in ssp_df.columns:
                if len(full_data_dict[scen][comp]) < 1:
                    continue
                full_data_dict[scen][comp] = np.append(full_data_dict[scen][comp], ssp_df[comp].values[year_start_fudge_index:])
    print(len(years))
    return full_data_dict, years


def read_concentrations_datafile(igcc_file, components, units, scen = "igcc_historical"):

    full_data_dict = initialise_empty_dictionaries([scen], components)
    #sys.exit(4)    

    df = pd.read_csv(igcc_file)
    print(df.columns)
    print(df.head())
    years_vals = df["timebound_lower"].values
    years = np.arange(years_vals[0], years_vals[-1] +1)
    #print(years_vals)
    #print(years)
    for comp_in in df.columns:
        if comp_in in components:
            comp = comp_in
        elif comp_in in component_renaming(comp_in):
            comp = component_renaming(comp_in)
        else:
            continue
        full_data_dict[scen][comp] = np.interp(years, years_vals, df[comp_in].values)
    return full_data_dict, years

##Now printing the data to scenario files file:

def write_concentration_file_for_each_scenario(full_data_dict, components, units, years, fname_end="conc_RCMIP.txt"):
    for s in full_data_dict.keys():
        fname =  f"{s}_{fname_end}"
        with open(fname, 'w') as f:
            f.write("Component\tCO2 \t %s \n"%("\t".join(str(c) for c in components[1:])))
            f.write("Unit \t %s\n"%("\t".join(str(u) for u in units)))
            f.write("Description \t fossil_fuel \t landuse %s\n"%("\t total"*(len(components)-2)))
            refline = ("Reference")
            lines = []
            #Finding each of the lines to print for each year:
            # And what to write on the reference line (ssp or rcp)
            #print(full_data_dict)
            #sys.exit(4)
            for i in range(len(years)):
                line = f"{years[i]}"
                if years[i] < 1750:
                    continue
                for c in components:
                    print(c)
                    if len(full_data_dict[s][c])> 0:
                        line = line + "\t" + f"{full_data_dict[s][c][i]:.6f}"
                        #Noting in the reference line that there is
                        #data from the ssp
                        if i == 0:
                            refline = refline + "\t" + s
                    elif 'BMB_AEROS' in c:
                        line = line + "\t" + "0.0"
                    else:
                        #print(c)
                        line = line + "\t" + "0.0"
                        #line = line + "\t" +  str(data_from_rcp[s][c][i])
                        #Noting in the reference line that missing data was
                        #taken from the rcp
                        if i == 0:
                            refline = refline + "\t" + "No data"

                line = line + "\n"
                lines.append(line)
                        
            refline = refline + "\n"
            #Writing out the reference line:
            f.write(refline)
            #Writing out all the finished lines:
            for l in lines:
                f.write(l)

    
if __name__ == "__main__":

    make_single_IGCC_concentrations_file("data/gases_vupdate_2024_WMO_added_new.txt", "data/ghg_concentrations_igcc.csv")#, ssp_fudge_file="data/ssp245_conc_RCMIP.txt")#, scenario_list=["abrupt-4xCO2"])         
            
