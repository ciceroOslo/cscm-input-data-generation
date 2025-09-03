import csv
import sys
import numpy as np

SPECIAL_COMPONENTS_DICT = {
    "MAGICC AFOLU":"CO2_lu",
    "Sulfur":"SO2", 
    "VOC":"NMVOC",
    "MAGICC Fossil and Industrial":"CO2",
    "Energy and Industrial Processes":"CO2",
    "AFOLU":"CO2_lu"
}

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
