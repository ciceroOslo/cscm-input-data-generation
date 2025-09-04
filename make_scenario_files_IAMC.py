import csv
import sys
import numpy as np
import pandas as pd


from interpolation_of_input import interpolate_data, interpolate_array_with_nans
from interpolation_of_input import interpolate_data_wconstant_start
from misc_utils import unit_conv_factor_long_name, initialise_empty_dictionaries, component_renaming

#component_dict = {"MAGICC AFOLU":"CO2_lu", "CFC113":"CFC-113", "CFC114":"CFC-114", "Sulfur":"SO2", "VOC":"NMVOC", "CFC11":"CFC-11", "CFC115":"CFC-115", "CFC12":"CFC-12", "HCFC141b":"HCFC-141b", "HCFC142b":"HCFC-142b", "HCFC22":"HCFC-22", "Halon1211":"H-1211", "Halon1301":"H-1301", "Halon2402":"H-2402","MAGICC Fossil and Industrial":"CO2"} # Halon1212, CH3Cl

def make_emissions_scenario_files(gaspam_file, iamc_data_file, historical=None, scenario_dict = None):
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file)
    if scenario_dict is None:
        dataframe = pd.read_csv(iamc_data_file)
        print(dataframe.columns)
        if "variable" in dataframe.columns:
            var_name = "variable"
            model_name = "model"
            scen_name = "scenario"           
        print(pd.unique(dataframe[var_name]))
        long_scen_names = dataframe[[model_name, scen_name]].drop_duplicates()
        short_scen_names = dataframe[[scen_name]].drop_duplicates()
        print(long_scen_names.shape)
        print(short_scen_names.shape)
        scenario_dict = {}

        for row, content in long_scen_names.iterrows():
            if short_scen_names.shape[0] == long_scen_names.shape[0]:
                scenario = f"{content[scen_name].lower().replace(' ', '')}"
            else:
                scenario = f"{content[scen_name].lower().replace(' ', '')}_{content[model_name].lower().replace(' ', '')}"
            scenario_dict[scenario] = [content[model_name], content[scen_name]]                
        print(scenario_dict)
    ## Initialising dictionary to hold the data:
    full_data_dict, years = read_iamc_and_convert(components, units, scenario_dict, iamc_data_file)
    write_file_for_each_scenario(full_data_dict, scenario_dict, units, components, years, f"em_{gaspam_file.split('/')[-1].split('.')[0]}.txt")

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

def write_file_for_each_scenario(full_data_dict, scenario_dict, units, components, years, fname_end = "em_RCMIP.txt"):
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
    make_emissions_scenario_files("gases_vupdate_2024_WMO.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv")
            
            #print "Success " + (',').join(line)
    #print counter
    #print years
    #sys.exit(4)
    #print full_data_dict["SSP2-45"]
    #print unit_dict

    ##Now printing the data to scenario files file:
    

        
                
                
