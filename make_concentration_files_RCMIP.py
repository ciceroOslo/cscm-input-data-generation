import csv
import sys
import numpy as np
from interpolation_of_input import interpolate_data
from interpolation_of_input import interpolate_data_wconstant_start

##Initialising list of scenarios components and units
#
#scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
scenarios_vanilla =[ "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460",  "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585"]# "ssp370-lowNTCF-aerchemmip","ssp370-lowNTCF-gidden"]
scenarios_extendconstant=["1pctCO2", "1pctCO2-4xext", "abrupt-0p5xCO2", "abrupt-2xCO2", "abrupt-4xCO2", "piControl"]
scenarios_hist=["historical","historical-cmip5","rcp60","rcp26", "rcp85", "rcp45"]
scenario_list = ["ssp370-lowNTCF-aerchemmip","ssp370-lowNTCF-gidden" ]
#scenario_list = np.concatenate([scenarios_vanilla, scenarios_extendconstant, scenarios_hist])
print(scenario_list)
components = []
units = []
#ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt","esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
#NBNB!! Check mappings for last four

component_dict = {"AFOLU":"CO2_lu", "CFC113":"CFC-113", "CFC114":"CFC-114", "Sulfur":"SO2", "VOC":"NMVOC", "CFC11":"CFC-11", "CFC115":"CFC-115", "CFC12":"CFC-12", "HCFC141b":"HCFC-141b", "HCFC142b":"HCFC-142b", "HCFC22":"HCFC-22", "Halon1211":"H-1211", "Halon1301":"H-1301", "Halon2402":"H-2402"} # Halon1212, CH3Cl

# Start by getting the list of gas components and units
# from the gases file:

with open('../../input_RCP/gases_v1RCMIP.txt', 'rb') as txt_rcpfile:
    gasreader = csv.reader(txt_rcpfile, delimiter = '\t')
    head = next(gasreader)
    for row in gasreader:
        if(row[2] == '-'):
        #    components.append('CO2_lu')
        #else:
            continue
        else:
            components.append(row[0])
            units.append(row[2])
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
print(units)

#sys.exit(4)    
counter = 0
readfirstline = 0
sval = {}
#with open('rcmip-concentrations-annual-means-v3-1-0.csv', 'rb') as csv_ssp_file:
with open('rcmip-concentrations-annual-means-ssp370-lowNTCF-only-20191220T0833.csv', 'r') as csv_ssp_file:
    datareader = csv.reader(csv_ssp_file, delimiter=',')
    for line in datareader:
        if readfirstline == 0:
            years = line[7:]
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
        if c not in components:
            if c in component_dict:
                c = component_dict[c]
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
        #print(s)
        if s in scenarios_vanilla:
            data = np.array(map(float,interpolate_data(line[7:])))
        elif s in scenarios_extendconstant:
            if s == "1pctCO2":
                sval[c] = float(line[157])
                #print("Setting s-value fromscenario %s"%s)
            data = np.array(map(float,interpolate_data_wconstant_start(line[7:], startval=sval[c])))
        else:
            print(line[72])
            print(s)
            data = np.array(map(float,interpolate_data_wconstant_start(line[7:],start=65)))
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

        
        #print "Success " + (',').join(line)
#print counter
#print years
#sys.exit(4)
#print full_data_dict["SSP2-45"]
#print unit_dict

##Now printing the data to scenario files file:
for s in scenario_list:

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
    fname =  "%s_conc_RCMIP.txt"%(s)
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
            line = years[i]
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

            #Now making interpolation for years with no data:
            if (i < len(years)-1) and (int(years[i+1]) > int(years[i])+1):
                y0 = int(years[i])
                y1 = int(years[i+1])
                #Looping over missing years:    
                for y in range(y0+1,y1):
                    #print y
                    line = str(y)
                    #Using simple linear interpolation formula for each component:
                    for c in components:
                        if len(full_data_dict[s][c])> 0:
                            cy = str((full_data_dict[s][c][i]*(y1-y) + full_data_dict[s][c][i+1]*(y-y0))/(y1-y0))
                            line = line + "\t" + cy
                            
                        else:
                            cy = str((float(data_from_rcp[s][c][i])*(y1-y) + float(data_from_rcp[s][c][i+1])*(y-y0))/(y1-y0))
                            line = line + "\t" +  cy
                    line = line + "\n"
                    lines.append(line)
                    
        refline = refline + "\n"
        #Writing out the reference line:
        f.write(refline)
        #Writing out all the finished lines:
        for l in lines:
            f.write(l)

    
            
            
