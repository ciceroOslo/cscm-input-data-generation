import csv
import sys
import numpy as np
import pandas as pd


from interpolation_of_input import interpolate_data, interpolate_array_with_nans
from interpolation_of_input import interpolate_data_wconstant_start
from misc_utils import unit_conv_factor_long_name, initialise_empty_dictionaries, initialise_comp_unit_dict, component_renaming, lift_scenariolist_from_datafile, glue_scenario_to_historical

#component_dict = {"MAGICC AFOLU":"CO2_lu", "CFC113":"CFC-113", "CFC114":"CFC-114", "Sulfur":"SO2", "VOC":"NMVOC", "CFC11":"CFC-11", "CFC115":"CFC-115", "CFC12":"CFC-12", "HCFC141b":"HCFC-141b", "HCFC142b":"HCFC-142b", "HCFC22":"HCFC-22", "Halon1211":"H-1211", "Halon1301":"H-1301", "Halon2402":"H-2402","MAGICC Fossil and Industrial":"CO2"} # Halon1212, CH3Cl

def make_emissions_scenario_files(gaspam_file, iamc_data_file, historical=None, scenario_dict = None, glue_historical=False):
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file)
    if historical is not None:
        data_dict_historical, years_hist, refs = read_historical_emissions(components, units, historical)
        write_file_for_each_scenario(data_dict_historical, {"historical": "historical"}, units, components, years_hist, f"em_{gaspam_file.split('/')[-1].split('.')[0]}.txt", refs = refs)

    if scenario_dict is None:
        scenario_dict = lift_scenariolist_from_datafile(iamc_data_file, as_dict=True)
    ## Initialising dictionary to hold the data:
    full_data_dict, years = read_iamc_and_convert(components, units, scenario_dict, iamc_data_file)
    if historical is not None and glue_historical:
        full_data_dict, years = glue_scenario_to_historical(full_data_dict, data_dict_historical, years, years_hist)
    write_file_for_each_scenario(full_data_dict, scenario_dict, units, components, years, f"em_{gaspam_file.split('/')[-1].split('.')[0]}.txt")

def read_historical_emissions(components, units, iamc_data_file):
    full_data_dict = initialise_empty_dictionaries(["historical"], components)
    df = pd.read_csv(iamc_data_file)
    years = np.array(df.columns[6:], int)
    refs = initialise_empty_dictionaries(["historical"], components)
    for row, content in df.iterrows():
        comp_in = content["variable"].split("|")[-1]
        print(comp_in)
        if comp_in in components:
            comp = comp_in
        elif component_renaming(comp_in) in components:
            comp = component_renaming(comp_in)
            print(comp)
        else:
            print(f"Found no match for {comp_in}")
            continue
        unit_c = units[components.index(comp)]
        conv_factor = unit_conv_factor_long_name(unit_c, content["unit"], comp)
        #print(f"Component {comp} with unit_c {unit_c}, input unit {content['unit']} and conv_factor {conv_factor}")
        if len(full_data_dict["historical"][comp]) > 0:
            print("Multiple entries for data, why are we here")
            print(row)
            print(content)
            sys.exit(4)
        full_data_dict["historical"][comp] = conv_factor * interpolate_array_with_nans(np.array(content.iloc[6:],float),years)
        refs["historical"][comp] = content["model"]
    print(df.columns)
    print(df.head())
    return full_data_dict, years, refs

def read_iamc_and_convert(components, units, scenario_dict, iamc_data_file):
    full_data_dict = initialise_empty_dictionaries(scenario_dict, components)
    df = pd.read_csv(iamc_data_file)
    years = np.array(df.columns[6:], int)
    for scen_short, scen_details in scenario_dict.items():
        data = df.loc[(df["region"] == "World") & (df["scenario"]==scen_details[1]) & (df["model"] == scen_details[0])]

        for row, content in data.iterrows():
            comp_in = content["variable"].split("|")[-1]
            print(comp_in)
            if comp_in in components:
                comp = comp_in
            elif component_renaming(comp_in) in components:
                comp = component_renaming(comp_in)
                print(comp)
            else:
                print(f"Found no match for {comp_in}")
                continue
            unit_c = units[components.index(comp)]
            #print(content)
            #print(comp)
            #print(f"Starting point is input unit {content['unit']} and desired unit {unit_c} for {comp}")
            conv_factor = unit_conv_factor_long_name(unit_c, content["unit"], comp)
            #print(f"Component {comp} with unit_c {unit_c}, input unit {content['unit']} and conv_factor {conv_factor}")
            full_data_dict[scen_short][comp] = conv_factor * interpolate_array_with_nans(np.array(content.iloc[6:],float),years)
        for c in components:
            if len(full_data_dict[scen_short][c]) < len(years):
                print(f"Found no data for {c}")
                full_data_dict[scen_short][c] = np.zeros(len(years))
    return full_data_dict, years

def make_ref_line(full_data_dict, components, scenario, refs = None):
    refline = ("Reference")
    for c in components:
        if refs is not None:
            if len(refs[scenario][c]) > 0:
                refline =  refline + "\t" + refs[scenario][c]
            else: 
                refline =  refline + "\t" + "No data"
        else:
            if len(full_data_dict[scenario][c])> 0:
                refline =  refline + "\t" + scenario
            else:
                refline =  refline + "\t" + "No data"

    return refline                

def write_file_for_each_scenario(full_data_dict, scenario_dict, units, components, years, fname_end = "em_RCMIP.txt", refs = None):
    for s in scenario_dict:
        """
        if s in ssp_rcp_dict:
            #Initialising a dictionary to hold rcp data where missing
            sfile = "../../input_RCP/%s"%ssp_rcp_dict[s]
            with open(sfile, 'r') as f:
                rcpreader = csv.reader(f, delimiter = '\t')
                for line in rcpreader:
                    if line[0] not in years:
                        continue
                    else:
                        for i in range(len(components)):
                            data_from_rcp[s][components[i]].append(line[i+1])
                        
        """        
        #    fname =  "%s_%s.%s_em_RCMIP.txt"%(s[0:4],s[5], s[6])
        #fname =  "%smethane_em_RCMIP.txt"%(s)
        fname =  f"{s}_{fname_end}"
        refline = make_ref_line(full_data_dict, components, scenario=s, refs=refs)
        with open(fname, 'w') as f:
            f.write("Component \t CO2 \t CO2 \t %s \n"%("\t".join(str(c) for c in components[2:])))
            f.write("Unit \t %s\n"%("\t".join(str(u) for u in units)))
            f.write("Description \t fossil_fuel \t landuse %s\n"%("\t total"*(len(components)-2)))
            lines = []
            #Finding each of the lines to print for each year:
            # And what to write on the reference line (ssp or rcp)
            print(full_data_dict.keys())
            for keys, dicts in full_data_dict.items():
                print(dicts.keys())
            #sys.exit(4)
            for i in range(len(years)):
                line = years[i] 
                for c in components:
                    print(c)
                    if len(full_data_dict[s][c])> 0:
                        line = "%s \t %.8f"%(line, full_data_dict[s][c][i])
                    else:
                        #print(c)
                        line = "%s \t %.8f"%(line, 0.)
                        #line = line + "\t" +  str(data_from_rcp[s][c][i])
                        #Noting in the reference line that missing data was
                        #taken from the rcp
                        full_data_dict[s][c] = np.zeros(len(years))

                line = line + "\n"
                lines.append(line)
                        
            refline = refline + "\n"
            #Writing out the reference line:
            f.write(refline)
            #Writing out all the finished lines:
            for l in lines:
                f.write(l)

if __name__ == "__main__":
    make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv", historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv")
            
            #print "Success " + (',').join(line)
    #print counter
    #print years
    #sys.exit(4)
    #print full_data_dict["SSP2-45"]
    #print unit_dict

    ##Now printing the data to scenario files file:
    

        
                
                
