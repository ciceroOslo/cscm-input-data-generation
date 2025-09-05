import csv
import sys
import numpy as np
import pandas as pd

SPECIAL_COMPONENTS_DICT = {
    "MAGICC AFOLU":"CO2_lu",
    "Sulfur":"SO2", 
    "VOC":"NMVOC",
    "MAGICC Fossil and Industrial":"CO2",
    "Energy and Industrial Processes":"CO2",
    "AFOLU":"CO2_lu",
    "Albedo Change": "land_use",
}

ROW_NUM_SKIP_GASPAM = {1: "X", 2:"-"}

# Method to convert the unit names from tonnes to grams
def unit_name_converter(unit):
    u = unit[0:2]
    if(u == 'Mt'):
        return "Tg"
    elif(u == 'kt'):
        return "Gg"
    elif(u == 'Gt'):
        return "Pg"
    else:
        print("%s not supported for conversion"%unit)
        sys.exit(4)
        return unit

#Method to find unit conversion factor
def unit_conv_factor(proper_unit, unit,c):
    conv_dict = {"P": 1.e15, "T": 1.e12, "G": 1.e9, "M": 1.e6, "k": 1.e3}
    conv_factor = conv_dict[unit[0]]/conv_dict[proper_unit[0]]
    if(unit[1:] != proper_unit[1:]):
        if(unit[1:] == 'g' and proper_unit[1:] == "g_C" and (c == 'CO2' or c == 'CO2_lu')):
            conv_factor = conv_factor*3./11 #Carbon mass fraction in CO2
        elif(unit[1:]=='g' and proper_unit[1:] == 'g_N' and c == 'N2O'):
            conv_factor = conv_factor*0.636 #Nitrogen mass fraction in N2O
        elif((unit[1: ]=='t NOx/yr' or unit[1: ]=='t NO2/yr') and proper_unit[1:]== 't_N' and c == 'NOx'):
            conv_factor = conv_factor*0.304 # Nitrogen mass fraction in NOx (approximated by NO2)
        elif(unit[1:]=='g' and proper_unit[1:] == 'g_S' and c == 'SO2'):
            conv_factor = conv_factor*0.501 #Sulphur mass fraction in SO2
            print("I went here, and ")
        elif (f"{unit[1:]}_{c}" == proper_unit[1:]):
            conv_factor = conv_factor
        else:
            print("Unit: %s proper unit: %s for %s"%(unit, proper_unit, c))
            print("%s %s %s "%(unit[1:],proper_unit[1:], c))
            sys.exit(4)
    #print "Converting from %s to %s  with conversion factor %e"%(unit, proper_unit, conv_factor)
    return conv_factor

def unit_conv_factor_long_name(proper_unit, unit, c):
    if unit == proper_unit:
        return 1
    print(component_renaming(c))
    if (unit.split(" ")[1] == f"{c}/yr") or (f"{component_renaming(unit.split(' ')[1].split('/')[0])}/{unit.split(' ')[1].split('/')[1]}" == f"{c}/yr"):
        if unit.split(" ")[1] in ["NO2/yr", "NOx/yr"]:
            return unit_conv_factor(proper_unit, unit, c)
        if unit.split(" ")[0] == proper_unit or unit_name_converter(unit.split(" ")[0]) == proper_unit:
            return 1
        if unit_name_converter(unit.split(" ")[0])[1] == proper_unit[1]:
            return unit_conv_factor(proper_unit, unit_name_converter(unit.split(" ")[0]), c)
    if c == "CO2_lu":
        return unit_conv_factor(proper_unit, unit_name_converter(unit.split(" ")[0]), c)
    return unit_conv_factor(proper_unit, unit, c)
        #return unit_conv_factor(proper_unit, unit.split())

def component_renaming(comp_rcmip):
    if comp_rcmip in SPECIAL_COMPONENTS_DICT:
        return SPECIAL_COMPONENTS_DICT[comp_rcmip]
    if comp_rcmip.startswith("CFC") and comp_rcmip[3] != "-":
        return comp_rcmip.replace("CFC", "CFC-")
    if comp_rcmip.startswith("Halon"):
        return comp_rcmip.replace("Halon", "H-")
    if comp_rcmip.startswith("HCFC") and comp_rcmip[4] != "-":
        return comp_rcmip.replace("HCFC", "HCFC-")
    if comp_rcmip in ["HFC43-10", "HFC4310"]:
        return "HFC4310mee"
    #print(f"Don't know what to do with {comp_rcmip}, returning as is")
    return comp_rcmip

def rf_component_renaming(rf_comp):
    if rf_comp in SPECIAL_COMPONENTS_DICT:
        return SPECIAL_COMPONENTS_DICT[rf_comp]
    return rf_comp.lower()        

def initialise_empty_dictionaries(scenario_dict, components):
    ## Initialising dictionary to hold the data:
    full_data_dict = {}

    for s in scenario_dict:

        full_data_dict[s] = {}
        for c in components:
            full_data_dict[s][c] = []

    return full_data_dict

def initialise_comp_unit_dict(gaspam_file, emissions= True):
    comp_temp = []
    unit_temp = []
    if emissions:
        unit_col = 1
    else:
        unit_col = 2

    with open(gaspam_file, 'r') as txt_rcpfile:
        gasreader = csv.reader(txt_rcpfile, delimiter = '\t')
        # Skipping header
        head = next(gasreader)
        for row in gasreader:
            if(row[unit_col] == ROW_NUM_SKIP_GASPAM[unit_col]):
            #    components.append('CO2_lu')
            #else:
                continue
            else:
                comp_temp.append(row[0])
                unit_temp.append(row[unit_col])
    if not emissions:
        return comp_temp, unit_temp
    
    components = comp_temp[:]
    units = unit_temp[:]
    components.insert(1,'CO2_lu')
    units.insert(1,'Pg_C')
    return components, units

def lift_scenariolist_from_datafile(datafile, as_dict = False):

    dataframe = pd.read_csv(datafile)
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

    if as_dict:
        scenario_list = {}

        for row, content in long_scen_names.iterrows():
            if short_scen_names.shape[0] == long_scen_names.shape[0]:
                scenario = f"{content[scen_name].lower().replace(' ', '')}"
            else:
                scenario = f"{content[scen_name].lower().replace(' ', '')}_{content[model_name].lower().replace(' ', '')}"
            scenario_list[scenario] = [content[model_name], content[scen_name]]                
        print(scenario_list)
    else:
        scenario_list = []
        for row, content in long_scen_names.iterrows():
            if short_scen_names.shape[0] == long_scen_names.shape[0]:
                scenario_list.append(content[scen_name])
            else:
                scenario_list.append(f"{content[scen_name].lower().replace(' ', '')}_{content[model_name].lower().replace(' ', '')}")
    return scenario_list

