import csv
import sys
import numpy as np
import pandas as pd


from interpolation_of_input import interpolate_data
from interpolation_of_input import interpolate_data_wconstant_start
from misc_utils import unit_conv_factor, unit_name_converter, component_renaming

#component_dict = {"MAGICC AFOLU":"CO2_lu", "CFC113":"CFC-113", "CFC114":"CFC-114", "Sulfur":"SO2", "VOC":"NMVOC", "CFC11":"CFC-11", "CFC115":"CFC-115", "CFC12":"CFC-12", "HCFC141b":"HCFC-141b", "HCFC142b":"HCFC-142b", "HCFC22":"HCFC-22", "Halon1211":"H-1211", "Halon1301":"H-1301", "Halon2402":"H-2402","MAGICC Fossil and Industrial":"CO2"} # Halon1212, CH3Cl

def make_emissions_scenario_files(gaspam_file, iamc_data_file, historical=None, scenario_list = None):
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file)
    if scenario_list is None:
        dataframe = pd.read_csv(iamc_data_file)
        print(dataframe.columns)
        if "variable" in dataframe.columns:
            var_name = "variable"
            model_name = "model"
            scen_name = "scenario"
        elif "Variable" in dataframe.columns:
            var_name = "Variable"
            model_name = "Model"
            scen_name = "Scenario"            
        print(pd.unique(dataframe[var_name]))
        long_scen_names = dataframe[[model_name, scen_name]].drop_duplicates()
        short_scen_names = dataframe[[scen_name]].drop_duplicates()
        print(long_scen_names.shape)
        print(short_scen_names.shape)
        scenario_list = []

        for row, content in long_scen_names.iterrows():
            if short_scen_names.shape[0] == long_scen_names.shape[0]:
                scenario_list.append(f"{content[scen_name].lower().replace(' ', '')}")
            else:
                scenario_list.append(f"{content[scen_name].lower().replace(' ', '')}_{content[model_name].lower().replace(' ', '')}")
        print(scenario_list)
    ## Initialising dictionary to hold the data:
    full_data_dict, data_from_rcp, years = read_line_by_line(components, units, scenario_list, iamc_data_file)
    write_file_for_each_scenario(full_data_dict, scenario_list, units, components, years)

def initialise_comp_unit_dict(gaspam_file):
    comp_temp = []
    unit_temp = []
    with open(gaspam_file, 'r') as txt_rcpfile:
        gasreader = csv.reader(txt_rcpfile, delimiter = '\t')
        # Skipping header
        head = next(gasreader)
        for row in gasreader:
            if(row[1] == 'X'):
            #    components.append('CO2_lu')
            #else:
                continue
            else:
                comp_temp.append(row[0])
                unit_temp.append(row[1])
    components = comp_temp[:]
    units = unit_temp[:]
    components.insert(1,'CO2_lu')
    units.insert(1,'Pg_C')
    print(components)
    print(units)
    return components, units

def initialise_empty_dictionaries_wrcp(scenario_list, components):
    ## Initialising dictionary to hold the data:
    # TODO: Get rid of RCMIP part
    full_data_dict = {}
    ## And extra dictionary to hold data from ssp-scenario:
    ## This is for components for which data is missing for the ssp
    data_from_rcp ={}
    rcps = ["rcp60", "rcp26", "rcp85", "rcp45"]

    # Start by getting the list of gas components and units
    # from the gases file:
    rcp_BC_data = {}
    rcp_OC_data = {}

    BC_hist = []
    OC_hist= []
    #Initialising BC and OC data for historical RCPs:
    with open("data/emissions_historical_v10.txt", "r") as rcp_hist_file:
        datareader = csv.reader(rcp_hist_file, delimiter = "\t")
        lnum = 0
        for line in datareader:
            lnum = lnum +1
            if lnum < 5:
                continue
            BC_hist.append(float(line[-4]))
            OC_hist.append(float(line[-3]))
    print((BC_hist[:240]))
    print((OC_hist[:240]))
    #sys.exit(4)

    for s in scenario_list:

        full_data_dict[s] = {}
        data_from_rcp[s] = {}
        for c in components:
            full_data_dict[s][c] = []
            data_from_rcp[s][c] = []
        if s.startswith("rcp"):
            rcp_BC_data[s] = BC_hist[:240]
            rcp_OC_data[s] = OC_hist[:240]
            with open("data/rcp_%s.%s_em_hist_v9.txt"%(s[-2],s[-1]), "r") as rcp_em_file:

                datareader = csv.reader(rcp_em_file, delimiter = "\t")
                lnum = 0
                for line in datareader:
                    lnum = lnum+1
                    if lnum < 5:
                        continue
                    #print(line[-3:])
                    rcp_BC_data[s].append(float(line[-2]))
                    rcp_OC_data[s].append(float(line[-1]))

    return full_data_dict, data_from_rcp, rcp_BC_data, rcp_OC_data


def read_line_by_line(components, units, scenario_list, iamc_data_file):
    counter = 0
    readfirstline = 0
    full_data_dict, data_from_rcp, rcp_BC_data, rcp_OC_data  = initialise_empty_dictionaries_wrcp(scenario_list, components)

    with open(iamc_data_file, 'r') as csv_ssp_file:
    #with open('rcmip-emissions-annual-means-ssp370-lowNTCF-only-20191218T1423.csv', 'r') as csv_ssp_file:
        datareader = csv.reader(csv_ssp_file, delimiter=',')
        for line in datareader:
            if readfirstline == 0:
                years = line[7:]
                readfirstline = 1
            
            #Skip the lines we are not interested in:
            #print(line)
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
            if c == "CO2":
                continue
            if c not in components:
                
                if component_renaming(c) in components:
                    c = component_renaming(c)
                    #print("%s %s: %s: %s"%(s, c, line[3], line[22]))
                    if c == "CO2_lu" and line[3].split("|")[-2] != "CO2":
    #                    print(line[3])
                        continue
                    if c == "CO2" and line[3].split("|")[-2] != "CO2":
                        continue
                elif line[3].split("|")[-3] in ["BC", "OC"] and len(c.split(" "))> 1 and c.split(" ")[1] == "Burning" :
                    print(line[:7])
                    c = "BMB_AEROS_%s"%line[3].split("|")[-3]
                    
                else:
                
                    #print(c)
                    #sys.exit(4)
                    continue
            counter = counter +1
            sector = "total"
            
            #Find the unit and the original unit
            u = line[4]
            proper_unit = units[components.index(c)]
            #Getting units on the same form T/g
            if u != proper_unit:
            
                if(u[0:2] == proper_unit[0:2]):
                    if(u  == 'Mt NOx/yr' and proper_unit == "Mt_N"):
                        u = u
                    else:
                        u = proper_unit
                        
                else:
                    u = unit_name_converter(u)
                    
                    if(u[1] != proper_unit[1]):
                        print("%s %s: Failing to match unit %s to proper unit %s "%(s, c, u, proper_unit))
                    
            # Pick out the data and convert it to floats
            #Then make the whole thing a numpy array for easy
            # addition
            #print(s)
            #print(c)
            try:
                #print(s[0:3])
                if s[0:3] == "rcp":
                #print(s)
                    
                    data = np.array(list(map(float,interpolate_data_wconstant_start(line[7:],start=15))))
                else:
                    data = np.array(list(map(float,interpolate_data(line[7:]))))
            except:
                print(s)
                print(line[7:])
                data = np.zeros(len(years))
                sys.exit(4)
            #print(data)
            #sys.exit(4)
            conv_factor = 1
            # Check if the units match original
            # and save them:
            if u != proper_unit:
    #            print "Unit mismatch between proper unit: %s and unit %s"%(proper_unit, u)
                conv_factor = unit_conv_factor(proper_unit, u, c)   

            #First entry of scenario and component is
            # used to initialise
            #if len(full_data_dict[s][c]) == 0 and c != 'CO2_lu':
            if len(full_data_dict[s][c]) == 0 and sector == 'total':
                if s[0:3] =="rcp" and c =="OC":
                    data_conv = data*conv_factor
                    split_fraction =  rcp_OC_data[s][350]/data_conv[350]
                    full_data_dict[s][c] = rcp_OC_data[s]#.append(data_conv[351:]*split_fraction)
                    for d in data_conv[351:]:
                        full_data_dict[s][c].append(d*split_fraction)
                    print(len(full_data_dict[s][c]))
                    full_data_dict[s]['BMB_AEROS_OC'] = data_conv - full_data_dict[s][c]
                elif s[0:3] =="rcp" and c =="BC":
                    data_conv = data*conv_factor
                    split_fraction =  rcp_BC_data[s][350]/data_conv[350]
                    
                    full_data_dict[s][c] = rcp_BC_data[s]#.append(data_conv[351:]*split_fraction)
                    for d in data_conv[351:]:
                        full_data_dict[s][c].append(d*split_fraction)
                    print(len(full_data_dict[s][c]))
                    full_data_dict[s]['BMB_AEROS_BC'] = data_conv - full_data_dict[s][c]
                else:
                    print(data*conv_factor)
                    full_data_dict[s][c] = data*conv_factor
            else:
                print("Shouldn't really be here... Adding to initialised component with %s and %s"%(s,c))
                full_data_dict[s][c] = full_data_dict[s][c] + conv_factor*data    
                #sys.exit(4)
            #Subtracting forest and grassland burning components 
            #from OC and BC:


            if (c == 'BMB_AEROS_BC' or c =='BMB_AEROS_OC'):
                total_comp = '%s'%c[-2:]
                full_data_dict[s][total_comp] = full_data_dict[s][total_comp] - data*conv_factor
    return full_data_dict, data_from_rcp, years

def write_file_for_each_scenario(full_data_dict, scenario_list, units, components, years):
    for s in scenario_list:
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
        fname =  "%s_em_RCMIP.txt"%(s)
        with open(fname, 'w') as f:
            f.write("Component \t CO2 \t CO2 \t %s \n"%("\t".join(str(c) for c in components[2:])))
            f.write("Unit \t %s\n"%("\t".join(str(u) for u in units)))
            f.write("Description \t fossil_fuel \t landuse %s\n"%("\t total"*(len(components)-2)))
            refline = ("Reference")
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
                    if len(full_data_dict[s][c])> 0 and ( c not in ["BC", "OC"]):
                        line = "%s \t %.8f"%(line, full_data_dict[s][c][i])
                        #Noting in the reference line that there is
                        #data from the ssp
                        if i == 0:
                            refline = refline + "\t" + s

                    elif len(full_data_dict[s][c])> 0:
                        if len(full_data_dict[s]["BMB_AEROS_%s"%c]) > 0:
                            line = "%s \t %.8f"%(line, full_data_dict[s][c][i])
                            #Noting in the reference line that there is
                            #data from the ssp
                            if i == 0:
                                refline = refline + "\t" + s
                        else:
                            #print(s)
                            line = "%s \t %.8f"%(line, full_data_dict[s][c][i])
                            if i == 0:
                                refline = refline + "\t" + s + " old"               
                    elif 'BMB_AEROS' in c:
                        line = "%s \t %.8f"%(line, 0.)
                    

                    else:
                        #print(c)
                        line = "%s \t %.8f"%(line, 0.)
                        #line = line + "\t" +  str(data_from_rcp[s][c][i])
                        #Noting in the reference line that missing data was
                        #taken from the rcp
                        full_data_dict[s][c] = np.zeros(len(years))
                        if i == 0:
                            refline = refline + "\t" + "No data"

                line = line + "\n"
                lines.append(line)

                #Now making interpolation for years with no data:
                if (i < len(years)-1) and (int(years[i+1]) > int(years[i])+1):
                    y0 = int(years[i])
                    y1 = int(years[i+1])
                    #print(y0)
                    #print(y1)
                    #Looping over missing years:    
                    for y in range(y0+1,y1):
                        #print y
                        line = str(y)
                        print(line)
                        #Using simple linear interpolation formula for each component:
                        for c in components:
                            
                            if len(full_data_dict[s][c])> 0:
                                #print("Component:%s, i:%s, arraylnegth:%s"%(c, i, len(full_data_dict[s][c])))
                                cy = str((full_data_dict[s][c][i]*(y1-y) + full_data_dict[s][c][i+1]*(y-y0))/(y1-y0))
                                line = line + "\t" + cy
                                
                            else:
                                print("Component:%s, i:%s, arraylnegth:%s"%(c, i, len(full_data_dict[s][c])))
                                cy = str((float(data_from_rcp[s][c][i])*(y1-y) + float(data_from_rcp[s][c][i+1])*(y-y0))/(y1-y0))
                                line = line + "\t" +  cy
                                """
                                try:
                                    cy = str((float(data_from_rcp[s][c][i])*(y1-y) + float(data_from_rcp[s][c][i+1])*(y-y0))/(y1-y0))
                                    line = line + "\t" +  cy
                                except:
                                    full_data_dict[s][c] = zeros(years[len(years)] -years[0])
                                """
                        line = line + "\n"
                        lines.append(line)
                        
            refline = refline + "\n"
            #Writing out the reference line:
            f.write(refline)
            #Writing out all the finished lines:
            for l in lines:
                f.write(l)

if __name__ == "__main__":
    ##Initialising list of scenarios components and units
    #
    #scenario_list = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70 (Baseline)", "SSP3-LowNTCF", "SSP4-34", "SSP4-60", "SSP5-34-OS", "SSP5-85 (Baseline)"]
    #scenario_list = ["rcp60", "rcp26", "rcp85", "rcp45", "historical-cmip5", "esm-pi-CO2pulse", "esm-pi-cdr-pulse", "esm-piControl", "esm-bell-1000PgC", "esm-bell-2000PgC", "esm-bell-750PgC"]
    #scenario_list =["ssp370-lowNTCF-aerchemmip","ssp370-lowNTCF-gidden" ]
    #scenario_list = ["historical", "ssp370", "ssp370-lowNTCF", "ssp434", "ssp460", "ssp119", "ssp126", "ssp245", "ssp534-over", "ssp585","esm-bell-1000PgC", "esm-bell-2000PgC", "esm-bell-750PgC", "esm-pi-CO2pulse",  "esm-pi-cdr-pulse", "esm-piControl", "historical_cmip5"]
    scenario_list = ["ssp245", "rcp60"]
    #make_emissions_scenario_files("../ciceroscm/tests/test-data/gases_v1RCMIP.txt", "data/rcmip-emissions-annual-means-v3-1-0.csv", scenario_list=scenario_list)
    make_emissions_scenario_files("gases_vupdate_2024_WMO.txt", "data/rcmip-emissions-annual-means-v3-1-0.csv")#, scenario_list=scenario_list)
    #ssp_rcp_dict = {"rcp60":"rcp_6.0.txt","rcp85":"rcp_8.5.txt","rcp45":"rcp_4.5.txt"}#"esm-pi-CO2pulse":"rcp_6.0.txt", "esm-pi-cdr-pulse":"rcp_6.0.txt","esm-piControl":"rcp_4.5.txt", "historical-cmip5":"rcp_6.0.txt"}
    #NBNB!! Check mappings for last four

    #sys.exit(4)
    ssp245_orig = pd.read_csv("../ciceroscm/tests/test-data/ssp245_em_RCMIP.txt", sep=r"\s+", index_col=0, skiprows=[1, 2, 3])
    ssp245_here = pd.read_csv("../ciceroscm/tests/test-data/ssp245_em_RCMIP.txt", sep=r"\s+", index_col=0, skiprows=[1, 2, 3])

    make_emissions_scenario_files("gases_vupdate_2024_WMO.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv")
            
            #print "Success " + (',').join(line)
    #print counter
    #print years
    #sys.exit(4)
    #print full_data_dict["SSP2-45"]
    #print unit_dict

    ##Now printing the data to scenario files file:
    

        
                
                
