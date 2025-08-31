import csv
import sys, shutil
import numpy as np


##Initialising list of scenarios components and units
#
#scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
#scenario_list = ["historical-cmip5", "rcp60", "rcp26", "rcp85", "rcp45", "esm-pi-CO2pulse", "esm-pi-cdr-pulse", "esm-piControl", "esm-bell-1000PgC", "esm-bell-2000PgC", "esm-bell-750PgC" 
scenario_list = ["historical-cmip6", "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460", "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585", "rcp60", "rcp85", "rcp45", "rcp26","constant_zero"]
#scenario_list = ["ssp370-lowNTCF-aerchemmip", "ssp370-lowNTCF-gidden", "constant_zero"]
#scenario_list = ["historical", "constant_zero"]
#components = ["Solar", "Volcanic", "Albedo Change"]
components = ["Albedo Change"]
ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt"}#"esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
#NBNB!! Check mappings for last four
comp_dict ={"Solar":"solar_RCMIP", "Volcanic":"VOLC_RCMIP", "Albedo Change":"LUCalbedo_RCMIP"}
#sys.exit(4)
years = []

#print(components)
#print(units)
#sys.exit(4)

## Initialising dictionary to hold the data:
full_data_dict = {}
## And extra dictionary to hold data from ssp-scenario:
## This is for components for which data is missing for the ssp
data_from_rcp ={}
for s in scenario_list:
    full_data_dict[s] = {}
    data_from_rcp[s] = {}
    for c in components:
        full_data_dict[s][c] = []
        data_from_rcp[s][c] = []

print(components)

counter = 0
readfirstline = 0

with open('rcmip-radiative-forcing-annual-means-v3-1-0.csv', 'rt') as csv_ssp_file:
#with open('rcmip-radiative-forcing-annual-means-ssp370-lowNTCF-only-20191218T1425.csv', 'rt') as csv_ssp_file:
    datareader = csv.reader(csv_ssp_file, delimiter=',')
    for line in datareader:
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
        data = np.array(map(lambda x: 0. if x == '' else float(x), line[7:]))
        print(data)
        #print(line[7:])
        #sys.exit(4)
#        conv_factor = 1

        if len(full_data_dict[s][c]) == 0:
            full_data_dict[s][c] = data
 
        else:
            full_data_dict[s][c] = full_data_dict[s][c] + data    
        
        #print "Success " + (',').join(line)
#print counter
#print years
#sys.exit(4)
#print full_data_dict["SSP2-45"]
#print unit_dict

##Now printing the data to scenario files file:
for s in scenario_list:

    for c in components:
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
    
            
            
