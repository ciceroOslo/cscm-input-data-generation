import csv
import sys
import numpy as np
import pandas as pd

from make_scenario_files_RCMIP import unit_name_converter, unit_conv_factor

scenario_list = ["ssp245"]

variables_aerosol = ['Emissions|BC', 'Emissions|OC', 'Emissions|Sulfur']
input_file = "rcmip-emissions-annual-means-v3-1-0.csv"
input_data = pd.read_csv(input_file)

keep_data =  []
for aervar in variables_aerosol:
    filtered_data = input_data[input_data["Variable"] == aervar]
    keep_data.append(filtered_data)

input_data = pd.concat(keep_data)
print(input_data.columns)
print(input_data["Variable"].unique())
print(input_data["Region"].unique())
print(input_data["Scenario"].unique())
print(input_data.shape)

#sys.exit(4)
for scen in scenario_list:
    filtered_data = input_data[input_data["Scenario"] == scen]
    filtered_data = filtered_data[filtered_data["Region"] != "World"]
    print(filtered_data.shape)
    orig_f = f"{scen}_em_RCMIP.txt"
    orig_data = pd.read_csv(orig_f, sep="\t", index_col=0)
    orig_data.rename(columns=lambda x: x.strip(), inplace=True)
    orig_data.rename(columns={"CO2 .1": "CO2"}, inplace=True)
    print(orig_data.shape)
    print(orig_data.head())
    for index, row in filtered_data.iterrows():
        #print(row)
        chem = row['Variable'].split('|')[-1]
        if chem == "Sulfur":
            chem = "SO2"

        comp_name = f"{chem}_{row['Region'].split('2')[-1]}"
        print(orig_data.columns)
        #ssys.exit(4)
        start = orig_data[chem][:3].to_list()
        targ_unit = start[0]
        in_unit = unit_name_converter(row["Unit"].split()[0])
        conv_factor = unit_conv_factor(targ_unit, in_unit, chem)
        print(conv_factor)
        print(start)
        print(targ_unit)
        print(in_unit)
        print(comp_name)
        data = conv_factor*(row[7:].astype(float).interpolate())
        start.extend(data)
        orig_data[comp_name] = start

    print(orig_data.shape)
    print(orig_data.head())
    print(orig_data.index)
    orig_data.to_csv(f"{scen}_with_regional_aerosols_em_RCMIP.txt", sep="\t", )
    
    