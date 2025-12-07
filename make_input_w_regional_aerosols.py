import csv
import sys
import os
import numpy as np
import pandas as pd

from make_scenario_files_RCMIP import unit_name_converter, unit_conv_factor

scenario_list = ["ssp245"]

variables_aerosol = [
    'Emissions|BC', 
    'Emissions|OC', 
    'Emissions|Sulfur'

    ]
input_data_dir = "data/"
input_file = "rcmip-emissions-annual-means-v3-1-0.csv"
input_data = pd.read_csv(os.path.join(input_data_dir, input_file))

print(input_data["Variable"].unique())
#sys.exit(4)
keep_data =  []
keep_data_afolu =  []
for aervar in variables_aerosol:
    filtered_data = input_data[input_data["Variable"] == aervar]
    filtered_data_afolu = input_data[input_data["Variable"] == f"{aervar}|MAGICC AFOLU"]
    keep_data.append(filtered_data)
    keep_data_afolu.append(filtered_data_afolu)

input_data = pd.concat(keep_data)
input_data_afolu = pd.concat(keep_data_afolu)
print(input_data.columns)
print(input_data["Variable"].unique())
print(input_data["Region"].unique())
print(input_data["Scenario"].unique())
print(input_data.shape)

#sys.exit(4)
for scen in scenario_list:
    filtered_data = input_data[input_data["Scenario"] == scen]
    filtered_data_afolu = input_data_afolu[input_data_afolu["Scenario"] == scen]
    filtered_data = filtered_data[filtered_data["Region"] != "World"]
    print(filtered_data)
    print(filtered_data_afolu)
    #sys.exit(4)
    orig_f = f"{scen}_em_RCMIP.txt"
    orig_data = pd.read_csv(os.path.join(input_data_dir, orig_f), sep="\t", index_col=0)
    orig_data.rename(columns=lambda x: x.strip(), inplace=True)
    orig_data.rename(columns={"CO2 .1": "CO2"}, inplace=True)
    print(orig_data.shape)
    print(orig_data.head())
    #sys.exit(4)
    for index, row in filtered_data.iterrows():
        #print(row)
        chem = row['Variable'].split('|')[-1]
        if chem == "Sulfur":
            chem = "SO2"

        comp_name = f"{chem}_{row['Region'].split('2')[-1]}"
        print(orig_data.columns)
        #ssys.exit(4)
        start = orig_data[chem][:3].to_list()
        print(start)
        #sys.exit(4)
        targ_unit = start[0]
        in_unit = unit_name_converter(row["Unit"].split()[0])
        conv_factor = unit_conv_factor(targ_unit, in_unit, chem)
        print(conv_factor)
        print(start)
        print(targ_unit)
        print(in_unit)
        print(comp_name)
        data = conv_factor*(row[7:].astype(float).interpolate())
        if chem in ["BC", "OC"]:
            data_afolu_filt = filtered_data_afolu[
                (filtered_data_afolu["Variable"] == f"{row['Variable']}|MAGICC AFOLU") & 
                (filtered_data_afolu["Region"] == row["Region"])].iloc[0][7:].astype(float).interpolate()
            print(data_afolu_filt.shape)
            print(type(data_afolu_filt))
            print(data_afolu_filt)
            data_afolu = conv_factor*data_afolu_filt
            data = data - data_afolu
        start.extend(data)
        orig_data[comp_name] = start

    print(orig_data.shape)
    print(orig_data.head())
    print(orig_data.index)
    orig_data.to_csv(f"{scen}_with_regional_aerosols_em_RCMIP.txt", sep="\t", )
    
    