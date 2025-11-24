import csv
import sys, shutil
import numpy as np

from misc_utils import initialise_empty_dictionaries

##Initialising list of scenarios components and units
#
#scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
#scenario_list = ["historical-cmip5", "rcp60", "rcp26", "rcp85", "rcp45", "esm-pi-CO2pulse", "esm-pi-cdr-pulse", "esm-piControl", "esm-bell-1000PgC", "esm-bell-2000PgC", "esm-bell-750PgC" 
scenario_list = ["historical", "historical-cmip6", "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460", "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585", "rcp60", "rcp85", "rcp45", "rcp26","constant_zero"]
#scenario_list = ["ssp370-lowNTCF-aerchemmip", "ssp370-lowNTCF-gidden", "constant_zero"]
#scenario_list = ["historical", "constant_zero"]
components = ["Solar", "Volcanic", "Albedo Change"]
#components = ["Albedo Change"]
ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt"}#"esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
#NBNB!! Check mappings for last four
comp_dict ={"Solar":"solar_RCMIP", "Volcanic":"VOLC_RCMIP", "Albedo Change":"LUCalbedo_RCMIP"}
#sys.exit(4)
years = []

#print(components)
#print(units)
#sys.exit(4)

def get_full_data_dict_from_file(filepath = 'data/rcmip-radiative-forcing-annual-means-v3-1-0.csv'):
    

    ## Initialising dictionary to hold the data:
    full_data_dict = initialise_empty_dictionaries(scenario_dict=scenario_list, components=components)

    print(components)
    print(full_data_dict.keys())
    readfirstline = 0

    with open(filepath, 'rt') as csv_ssp_file:
    #with open('rcmip-radiative-forcing-annual-means-ssp370-lowNTCF-only-20191218T1425.csv', 'rt') as csv_ssp_file:
        datareader = csv.reader(csv_ssp_file, delimiter=',')
        for line in datareader:
            #print(line)
            if readfirstline == 0:
                years = line[7:]
                readfirstline = 1
                full_data_dict["constant_zero"]["Albedo Change"] =np.zeros(len(years))
            
            #Skip the lines we are not interested in:
            if line[2] != "World":
                continue
            if line[1] not in scenario_list:
                continue
            #Pick out the scenarios, components and units from the 
            # line:
            s = line[1]
            if s not in scenario_list:
                    continue
            c = line[3].split("|")[-1]
            if c not in components:
                continue
            print(c)
            data = np.array(list(map(lambda x: 0. if x == '' else float(x), line[7:])))
            print(data)
            #print(data)
            #print(line[7:])
            #sys.exit(4)
    #        conv_factor = 1

            if len(full_data_dict[s][c]) == 0:
                full_data_dict[s][c] = data
    
            else:
                full_data_dict[s][c] = full_data_dict[s][c] + data 
    print(full_data_dict)

    return full_data_dict, years  
            
            #print "Success " + (',').join(line)
    #print counter
    #print years
    #sys.exit(4)
    #print full_data_dict["SSP2-45"]
    #print unit_dict

def print_full_data_dict(full_data_dict, years, fname_epithet = '', fout_dir = './'):

    ##Now printing the data to scenario files file:
    for s in scenario_list:

        for c in components:
            print(c)
            fname =  f"{fout_dir}{comp_dict[c]}_{s}{fname_epithet}.txt"
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
                        print(line)
                        f.write("%s \n"%line)
                    
                else:
                    for i in range(len(years)):
                        line = years[i] 

                        f.write("%s \n"%full_data_dict[s][c][i])
    #shutil.copy('./VOLC_RCMIP_ssp119.txt', '../../input_RF/RFVOLC/VOLC_RCMIP_monavg_NH.txt')
    #shutil.copy('./VOLC_RCMIP_ssp119.txt', '../../input_RF/RFVOLC/VOLC_RCMIP_monavg_SH.txt')
    
            
            
if __name__ == "__main__":
    full_data_dict, years = get_full_data_dict_from_file()
    print_full_data_dict(full_data_dict, years, fname_epithet = '_RCMIP', fout_dir = './')