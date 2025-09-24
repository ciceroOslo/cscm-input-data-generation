import csv
import sys
import numpy as np
import pandas as pd
from interpolation_of_input import interpolate_data
from interpolation_of_input import interpolate_data_wconstant_start
from misc_utils import unit_conv_factor_long_name, initialise_empty_dictionaries, initialise_comp_unit_dict, component_renaming, lift_scenariolist_from_datafile
##Initialising list of scenarios components and units
#
#scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
scenarios_vanilla =[ "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460",  "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585"]# "ssp370-lowNTCF-aerchemmip","ssp370-lowNTCF-gidden"]
scenarios_extendconstant=["1pctCO2", "1pctCO2-4xext", "abrupt-0p5xCO2", "abrupt-2xCO2", "abrupt-4xCO2", "piControl"]
#scenarios_hist=["historical","historical-cmip5","rcp60","rcp26", "rcp85", "rcp45"]
#scenario_list = ["ssp370-lowNTCF-aerchemmip","ssp370-lowNTCF-gidden" ]
#scenario_list = np.concatenate([scenarios_vanilla, scenarios_extendconstant, scenarios_hist])
#print(scenario_list)
components = []
units = []
#ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt","esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
#NBNB!! Check mappings for last four

# Start by getting the list of gas components and units
# from the gases file:

def make_concentrations_scenario_files(gaspam_file, rcmip_datafile, scenario_list = None):
    print("Starting")
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file, emissions=False)
    print("Done components and units")
    if scenario_list is None:
        scenario_list = lift_scenariolist_from_datafile(rcmip_datafile)
    print("Done finding scenarios_list")
    print(scenario_list)
    full_data_dict, years = read_concentrations_datafile(rcmip_datafile, components, units, scenario_list)
    print("Done getting data")
    write_concentration_file_for_each_scenario(full_data_dict, components, units, years, fname_end=f"conc_{gaspam_file.split('/')[-1].split('.')[0]}.txt")
    print("Done writing to files")

#print(components)
#print(units)
# #sys.exit(4)
def get_start_values_from_piControl(df, components, picontrol = "piControl"):
    print(df.columns)
    print(df.shape)
    short_scen_names = df[["Scenario"]].drop_duplicates()
    print(short_scen_names)
    df_picontrol = df.loc[(df["Scenario"] == picontrol) & (df["Region"] == "World")]

    print(df_picontrol.shape)
    sval ={}
    for row, content in df_picontrol.iterrows():
        comp_in = content["Variable"].split("|")[-1]
        if comp_in in components:
            comp = comp_in
        elif component_renaming(comp_in) in components:
            comp = component_renaming(comp_in)
        else:
            #print(f"Found no match for {comp_in}")
            continue
        sval[comp] = content.values[157]
    return sval



def read_concentrations_datafile(rcmip_datafile, components, units, scenario_list):
    full_data_dict = initialise_empty_dictionaries(scenario_list, components)
    #sys.exit(4)    
    counter = 0
    readfirstline = 0
    sval = {}
    years = []
    df = pd.read_csv(rcmip_datafile)
    print(df.columns)
    print(df["Scenario"].drop_duplicates())
    sval = get_start_values_from_piControl(df, components)
    #for scen in scenario_list:
        

    #with open('rcmip-concentrations-annual-means-v3-1-0.csv', 'rb') as csv_ssp_file:
    with open(rcmip_datafile, 'r') as csv_ssp_file:
        datareader = csv.reader(csv_ssp_file, delimiter=',')
        for line in datareader:
            if readfirstline == 0:
                years = np.array(line[7:], int)
                readfirstline = 1
            
            #Skip the lines we are not interested in:
            if line[2] != "World":
                continue
            if line[1] not in scenario_list:
                continue
            #Pick out the scenarios, components and units from the 
            # line:
            s = line[1]
            c = line[3].split("|")[-1]
            #print(line)
            if c not in components:
                if component_renaming(c) in components:
                    c = component_renaming(c)
                else:
                
                    #print c
                    #sys.exit(4)
                    continue
            counter = counter +1      
            #Find the unit and the original unit
            u = line[4]
            proper_unit = units[components.index(c)]
            #Getting units on the same form T/g
            if u != proper_unit:
                print("Unit: %s vs proper unit %s for component %s"%(u,proper_unit,c))
                sys.exit(4)

            # Pick out the data and convert it to floats
            #Then make the whole thing a numpy array for easy
            # addition
            if s in scenarios_vanilla:
                data = np.array(list(map(float,interpolate_data(line[7:]))))
            elif s in scenarios_extendconstant:
                data = np.array(list(map(float,interpolate_data_wconstant_start(line[7:], startval=sval[c]))))
                #print(data)
                #print(line[150])
                #sys.exit(4)
            else:
                #print(line[72])
                #print(s)
                data = np.array(list(map(float,interpolate_data_wconstant_start(line[7:],start=65))))
            #print(data)
            #sys.exit(4)

            conv_factor = 1
            # Check if the units match original
            # and save them:
            if u != proper_unit:
                #            print "Unit mismatch between proper unit: %s and unit %s"%(proper_unit, u)
                sys.exit(4)
                #conv_factor = unit_conv_factor(proper_unit, u, c)   

            #First entry of scenario and component is
            # used to initialise
            if len(full_data_dict[s][c]) == 0:
                full_data_dict[s][c] = data*conv_factor
            else:
                full_data_dict[s][c] = full_data_dict[s][c] + conv_factor*data
    return full_data_dict, years
            
            #print "Success " + (',').join(line)
#print counter
#print years
#sys.exit(4)
#print full_data_dict["SSP2-45"]
#print unit_dict

##Now printing the data to scenario files file:

def write_concentration_file_for_each_scenario(full_data_dict, components, units, years, fname_end = "conc_RCMIP.txt",):
    for s in full_data_dict.keys():

        """
        #Initialising a dictionary to hold rcp data where missing
        sfile = "../input_RCP/%s"%ssp_rcp_dict[s]
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
                    if len(full_data_dict[s][c])> 0:
                        line = line + "\t" + str(full_data_dict[s][c][i])
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

    make_concentrations_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/rcmip-concentrations-annual-means-v3-1-0.csv")#, scenario_list=["abrupt-4xCO2"])         
            
