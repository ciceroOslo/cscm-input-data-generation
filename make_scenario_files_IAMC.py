import csv
import sys
import os
import numpy as np
import pandas as pd


from interpolation_of_input import interpolate_array_with_nans
from misc_utils import unit_conv_factor_long_name, initialise_empty_dictionaries, initialise_comp_unit_dict, component_renaming, lift_scenariolist_from_datafile, glue_scenario_to_historical
from infilling_data import HISTORY_PATH, INFILLING_START_YEAR, LEAD_VARIABLE, MARKER_DB_PATH, load_history
from infilling_utils import classify_against_history, history_series_for_component, infill_missing, prepare_infilling

#component_dict = {"MAGICC AFOLU":"CO2_lu", "CFC113":"CFC-113", "CFC114":"CFC-114", "Sulfur":"SO2", "VOC":"NMVOC", "CFC11":"CFC-11", "CFC115":"CFC-115", "CFC12":"CFC-12", "HCFC141b":"HCFC-141b", "HCFC142b":"HCFC-142b", "HCFC22":"HCFC-22", "Halon1211":"H-1211", "Halon1301":"H-1301", "Halon2402":"H-2402","MAGICC Fossil and Industrial":"CO2"} # Halon1212, CH3Cl

#scenario_dict = {'scenarionopolicy_gemini-e3eu1.0', 'scenarioprotocolesrtaxes+ets_gemini-e3eu1.0', 'scenarioprotocolets+ets-2_gemini-e3eu1.0', 'scenarioprotocolfulltrading_gemini-e3eu1.0', 'new_diam_cp_v20260904_nemesis-worldv1.1', 'new_diam_nopol_v20260904_nemesis-worldv1.1', 'nopolicy_omnia', 'baseline_v1_2_new+softlink_omnia', 'diamond_baseline_open-prom2.2', 'climpol_gcameurope8.716102026', 'diamond_baseline_gcameurope8.716102026', 'ref_gcameurope8.716102026', 'npi_open-prom2.2'}
scenarios_drop = ['baseline_clews', 'diamond_baseline_gcameurope8.7', 'ref_gcameurope8.7']

def make_emissions_scenario_files(gaspam_file, iamc_data_file, historical=None, scenario_dict = None, glue_historical=False, fname_end = "em_DIAMOND.txt", infill=False, marker_db_path=MARKER_DB_PATH):
    components, units = initialise_comp_unit_dict(gaspam_file=gaspam_file)
    if infill:
        infill_inputs = prepare_infilling(marker_db_path=marker_db_path, history_path=historical or HISTORY_PATH)
        history = infill_inputs["history"]
    else:
        infill_inputs = None
        history = load_history(historical) if historical is not None else None
    if historical is not None:
        data_dict_historical, years_hist, refs = read_historical_emissions(components, units, historical)
        write_file_for_each_scenario(data_dict_historical, {"historical": "historical"}, units, components, years_hist, f"em_{gaspam_file.split('/')[-1].split('.')[0]}_{fname_end}", refs = refs)

    if scenario_dict is None:
        scenario_dict = lift_scenariolist_from_datafile(iamc_data_file, as_dict=True)
        for scenario in scenarios_drop:
            if scenario in scenario_dict:
                del scenario_dict[scenario]
    for scenario in scenario_dict:
        print(f"Preparing scenario: {scenario}")
        fname_long_end = f"em_{gaspam_file.split('/')[-1].split('.')[0]}_{fname_end}"
        fname = f"{scenario}_{fname_long_end}"
        fname_infilled = f"{scenario}_infilled_{fname_long_end}"
        if os.path.exists(fname) and (not infill or os.path.exists(fname_infilled)):
            print(f"File {fname} already exists.")
            continue
        scenario_dict_one = {scenario: scenario_dict[scenario]}
        if scenario in scenarios_drop:
            continue
        ## Initialising dictionary to hold the data:
        full_data_dict, years, infilled, refs_orig = read_iamc_and_convert(components, units, scenario_dict_one, iamc_data_file, dump_single_emissions_file=True, infill_inputs=infill_inputs, history=history)
        for scenario, data in full_data_dict.items():
            print(f"Scenario: {scenario}")
            #for comp, values in data.items():
            #    print(f"  Component: {comp}, Values: {values}")
        #print(full_data_dict)
        years_infilled = years.copy()
        if historical is not None and glue_historical:
            full_data_dict, years = glue_scenario_to_historical(full_data_dict, data_dict_historical, years, years_hist)
        write_file_for_each_scenario(full_data_dict, scenario_dict_one, units, components, years.copy(), fname_long_end, refs=refs_orig)
        if infilled is not None:
            infilled_data_dict, refs_infilled = infilled
            if historical is not None and glue_historical:
                infilled_data_dict, years_infilled = glue_scenario_to_historical(infilled_data_dict, data_dict_historical, years_infilled, years_hist)
            write_file_for_each_scenario(infilled_data_dict, scenario_dict_one, units, components, years_infilled.copy(), f"infilled_{fname_long_end}", refs=refs_infilled)
        
        sys.exit(4)

def read_historical_emissions(components, units, iamc_data_file):
    full_data_dict = initialise_empty_dictionaries(["historical"], components)
    df = pd.read_csv(iamc_data_file)
    for num,column in enumerate(df.columns):
        try:
            print(int(column))
            break
        except (ValueError, TypeError):
            print(f"Column {column} not int")
    years = np.array(df.columns[num:], int)
    refs = initialise_empty_dictionaries(["historical"], components)
    for row, content in df.iterrows():
        comp_in = content["variable"].split("|")[-1]
        comp_total = content["variable"]
        print(comp_in)
        if comp_in in components:
            comp = comp_in
        elif component_renaming(comp_in, comp_total) in components:
            comp = component_renaming(comp_in, comp_total)
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
        full_data_dict["historical"][comp] = conv_factor * interpolate_array_with_nans(np.array(content.iloc[num:],float),years)
        refs["historical"][comp] = content["model"]
    print(df.columns)
    print(df.head())
    return full_data_dict, years, refs

def preprocess_omnia_data(data):
    # Implement any specific preprocessing steps for Omnia scenarios here
    # For now, just return the data as is

    sum_n2o = None
    sum_ch4 = None
    for row, content in data.iterrows():
        if "N2O" in content["variable"]:
            if sum_n2o is None:
                sum_n2o = content.copy()
                sum_n2o["variable"] = "Emissions|N2O"
            else:
                sum_n2o.iloc[5:] += content.iloc[5:]
        elif ("CH4" in content["variable"]) and not "Demand" in content["variable"]:
            if sum_ch4 is None:
                sum_ch4 = content.copy()
                sum_ch4["variable"] = "Emissions|CH4"
            else:
                sum_ch4.iloc[5:] += content.iloc[5:]
    if sum_n2o is not None:
        sum_n2o["variable"] = "Emissions|N2O"
        data = pd.concat([data, pd.DataFrame([sum_n2o])], ignore_index=True)
    if sum_ch4 is not None:
        sum_ch4["variable"] = "Emissions|CH4"
        data = pd.concat([data, pd.DataFrame([sum_ch4])], ignore_index=True)
    
    row_co2 = data[data["variable"] == "Emissions|CO2|Energy and Industrial Processes"].iloc[0].copy()
    row_co2["variable"] = "Emissions|CO2"
    data = pd.concat([data, pd.DataFrame([row_co2])], ignore_index=True)

    return data

def to_annual(values, years, years_total, hist=None, check_units=False):
    """
    Interpolate values on (possibly irregular, gappy) years onto years_total; returns (annual values, rescale factor).

    hist=(years, values) in the same units fills years before the first reported value.
    With check_units, a power-of-1000 mismatch against hist is treated as a unit mislabel and rescaled.
    """
    values = np.array(values, float)
    valid = ~np.isnan(values)
    if not valid.any():
        return np.zeros(len(years_total)), 1.0
    xp = years[valid].astype(float)
    fp = values[valid]
    factor = 1.0
    if hist is not None:
        hist_years, hist_vals = hist
        ref_year = INFILLING_START_YEAR if xp[0] <= INFILLING_START_YEAR else xp[0]
        if check_units:
            action, factor = classify_against_history(np.interp(ref_year, xp, fp), np.interp(ref_year, hist_years, hist_vals))
            if action != "rescale":
                factor = 1.0
            fp = fp * factor
        before = hist_years < xp[0]
        xp = np.concatenate((hist_years[before], xp))
        fp = np.concatenate((hist_vals[before], fp))
    return np.interp(years_total, xp, fp), factor

def history_in_cicero_units(history, components, units):
    """Return {component: (years, values in CICERO units)} for components present in history."""
    hist_cicero = {}
    if history is None:
        return hist_cicero
    for c in components:
        h = history_series_for_component(history, c)
        if h is not None:
            hist_cicero[c] = (h[1], h[2] * unit_conv_factor_long_name(units[components.index(c)], h[0], c))
    return hist_cicero

def infill_scenario_components(scen_data_dict, scen_refs, data, num, years, years_total, components, units, infill_inputs, hist_cicero, model, scenario):
    """Return (data dict with all-zero or implausible components infilled, refs dict), or None if infilling is not possible."""
    missing = [c for c in components if len(scen_data_dict[c]) == 0 or np.all(np.asarray(scen_data_dict[c]) == 0)]
    lead_rows = data[data["variable"] == LEAD_VARIABLE]
    if lead_rows.empty:
        print(f"No {LEAD_VARIABLE} reported for {scenario}, skipping infilling")
        return None
    lead_vals = np.array(lead_rows.iloc[0, num:], float)
    lead_annual, _ = to_annual(lead_vals, years, years_total)

    total_rows = data[data["variable"] == "Emissions|CO2"]
    if "CO2_lu" in missing and not total_rows.empty:
        if not np.allclose(np.array(total_rows.iloc[0, num:], float), lead_vals, equal_nan=True):
            # CO2 comes from a total including AFOLU, so infilling CO2_lu would double count
            missing.remove("CO2_lu")

    infilled_dict = dict(scen_data_dict)
    refs = dict(scen_refs)
    for c in components:
        if c in missing or c in ("CO2", "CO2_lu") or c not in hist_cicero:
            continue
        hist_value = np.interp(INFILLING_START_YEAR, *hist_cicero[c])
        scen_value = np.interp(INFILLING_START_YEAR, years_total, infilled_dict[c])
        action, _ = classify_against_history(scen_value, hist_value)
        if action == "infill":
            print(f"{scenario}: {c} is {scen_value / hist_value:.2f} x history in {INFILLING_START_YEAR}, likely incomplete, infilling")
            missing.append(c)

    result = infill_missing(lead_annual, lead_rows.iloc[0]["unit"], years_total, missing, infill_inputs, model=model, scenario=scenario)
    if result is None:
        return None
    for comp, (unit, values) in result.items():
        conv_factor = unit_conv_factor_long_name(units[components.index(comp)], unit, comp)
        infilled_dict[comp] = conv_factor * values
        refs[comp] = "infilled"
    return infilled_dict, refs

def read_iamc_and_convert(components, units, scenario_dict, iamc_data_file, dump_single_emissions_file=False, infill_inputs=None, history=None):
    """
    Return (data dict, years, infilled, refs).

    history (IAMC frame, see infilling_data.load_history) fills years before the first reported value and
    is used to detect unit mislabels. infilled is ({scen: infilled dict}, {scen: refs}) if infill_inputs
    (from prepare_infilling) is given and infilling succeeded, else None.
    """
    full_data_dict = initialise_empty_dictionaries(scenario_dict, components)
    refs_orig = {}
    infilled_data_dict = {}
    refs_infilled = {}
    if history is None and infill_inputs is not None:
        history = infill_inputs["history"]
    hist_cicero = history_in_cicero_units(history, components, units)
    df = pd.read_csv(iamc_data_file)
    
    # If a column name starts with a capital letter, rename it to all lowercase
    new_columns = []
    for col in df.columns:
        if isinstance(col, str) and len(col) > 0 and col[0].isupper():
            new_columns.append(col.lower())
        elif isinstance(col, str) and len(col) >= 4 and col[:4].isdigit():
            new_columns.append(int(col[:4]))
        else:
            new_columns.append(col)
    df.columns = new_columns
    df = df[df["variable"].str.contains("Emissions", na=False)].reset_index(drop=True)
    for num,column in enumerate(df.columns):
        try:
            print(int(column))
            break
        except (ValueError, TypeError):
            
            print(f"Column {column} not int")
    years = np.array(df.columns[num:], int)
    years_total = np.arange(years[0], years[-1]+1)
    for scen_short, scen_details in scenario_dict.items():
        print(scen_short)
        data = df.loc[(df["region"] == "World") & (df["scenario"]==scen_details[1]) & (df["model"] == scen_details[0])]
        print(data)
        if "omnia" in scen_short:
            print(f"Processing Omnia scenario: {scen_short}")
            data = preprocess_omnia_data(data)
        if dump_single_emissions_file:
            data.to_csv(f"single_emissions_{scen_short}.csv", index=False)
        refs_orig[scen_short] = {c: scen_short for c in components}

        for row, content in data.iterrows():
            if not content["variable"].startswith("Emissions|"):
                continue
            comp_in = content["variable"].split("|")[-1]
            comp_total = content["variable"]
            if comp_in in components:
                comp = comp_in
            elif component_renaming(comp_in, comp_total) in components:
                comp = component_renaming(comp_in, comp_total=comp_total)
                print(comp)
            else:
                print(f"Found no match for {comp_in}, full variable: {content["variable"]}")
                continue
            unit_c = units[components.index(comp)]
            print(content["unit"])
            #print(content)
            #print(comp)
            #print(f"Starting point is input unit {content['unit']} and desired unit {unit_c} for {comp}")
            conv_factor = unit_conv_factor_long_name(unit_c, content["unit"], comp)
            if comp == "N2O":
                print(f"Component {comp} with unit_c {unit_c}, input unit {content['unit']} and conv_factor {conv_factor}")
                #sys.exit(4)
            full_data_dict[scen_short][comp], factor = to_annual(
                conv_factor * np.array(content.iloc[num:], float), years, years_total,
                hist=hist_cicero.get(comp), check_units=comp not in ("CO2", "CO2_lu"),
            )
            if factor != 1.0:
                print(f"{scen_short}: {comp} ({content['variable']}) off from history by ~{1 / factor:g}, assuming unit mislabel, multiplying by {factor:g}")
                refs_orig[scen_short][comp] = f"rescaled_x{factor:g}"
            #print(full_data_dict[scen_short][comp])
            #sys.exit(4)
        for c in components:
            if len(full_data_dict[scen_short][c]) < len(years_total):
                print(f"Found no data for {c}, making a second pass summing sub-sectors")
                full_data_dict[scen_short][c] = np.zeros(len(years_total))
                if c == "CO2_lu" and len(full_data_dict[scen_short]["CO2"]) == len(years_total):
                    continue
                parts = []
                for row, content in data.iterrows():
                    comp_in = content["variable"].split("|")[1]
                    comp_total = content["variable"]
                    if comp_in != c and component_renaming(comp_in, comp_total) != c:
                        continue
                    conv_factor = unit_conv_factor_long_name(units[components.index(c)], content["unit"], c)
                    parts.append(conv_factor * np.array(content.iloc[num:], float))
                if not parts:
                    continue
                # NaN wherever any sub-sector is unreported, so the sum is only used where complete
                summed = np.sum(parts, axis=0)
                if np.isnan(summed).all():
                    print(f"Sub-sectors for {c} share no reported years, summing them separately interpolated")
                    full_data_dict[scen_short][c] = np.sum([to_annual(p, years, years_total)[0] for p in parts], axis=0)
                    continue
                full_data_dict[scen_short][c], factor = to_annual(
                    summed, years, years_total, hist=hist_cicero.get(c), check_units=c not in ("CO2", "CO2_lu"),
                )
                if factor != 1.0:
                    print(f"{scen_short}: summed {c} off from history by ~{1 / factor:g}, assuming unit mislabel, multiplying by {factor:g}")
                    refs_orig[scen_short][c] = f"rescaled_x{factor:g}"
        if infill_inputs is not None:
            res = infill_scenario_components(full_data_dict[scen_short], refs_orig[scen_short], data, num, years, years_total, components, units, infill_inputs, hist_cicero, model=scen_details[0], scenario=scen_details[1])
            if res is not None:
                infilled_data_dict[scen_short], refs_infilled[scen_short] = res
    print("Ready to return")
    infilled = (infilled_data_dict, refs_infilled) if infilled_data_dict else None
    return full_data_dict, years_total, infilled, refs_orig

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
        years_here = years.copy()
        print(s)
        print(years_here)
        fname =  f"{s}_{fname_end}"
        refline = make_ref_line(full_data_dict, components, scenario=s, refs=refs)
        with open(fname, 'w') as f:
            f.write("Component \t CO2 \t CO2 \t %s \n"%("\t".join(str(c) for c in components[2:])))
            f.write("Unit \t %s\n"%("\t".join(str(u) for u in units)))
            f.write("Description \t fossil_fuel \t landuse %s\n"%("\t total"*(len(components)-2)))
            lines = []
            #Finding each of the lines to print for each year:
            # And what to write on the reference line (ssp or rcp)
            for c in components:
                if c not in ["CO2", "N2O", "CH4"]:
                    continue
                data_len = len(full_data_dict[s][c])
                if data_len < len(years_here):
                    print(f"Warning: Scenario {s}, component {c} has less data ({data_len}) than the number of years ({len(years_here)})")
                    years_here = years_here[:data_len]
                    #sys.exit(4)
            #sys.exit(4)
            for i in range(len(years_here)):
                line = years_here[i] 
                for c in components:
                    if len(full_data_dict[s][c])> 0:
                        #print(f"Using data for scenario {s}, component {c}, year {years_here[i]}: {i}, {len(full_data_dict[s][c])}")
                        line = "%s \t %.8f"%(line, full_data_dict[s][c][i])
                    else:
                        #print(c)
                        line = "%s \t %.8f"%(line, 0.)
                        #line = line + "\t" +  str(data_from_rcp[s][c][i])
                        #Noting in the reference line that missing data was
                        #taken from the rcp
                        full_data_dict[s][c] = np.zeros(len(years_here))

                line = line + "\n"
                lines.append(line)
                        
            refline = refline + "\n"
            #Writing out the reference line:
            f.write(refline)
            #Writing out all the finished lines:
            for l in lines:
                f.write(l)

if __name__ == "__main__":
    make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "/home/maritsandstad/temp/DIAMOND_WP5_baselines_consolidated_20260914_updated.csv", historical="data/historical_emissions_from_emissions_harmonisation_Feb2026.csv", glue_historical=True, infill=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "../emissions_harmonization_historical/notebooks/continuous_emissions_timeseries_1750_2500.csv", glue_historical=False)
    # make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "/home/masan/temp/DIAMOND_4.4/GCAM-Europe-NECP-global-emiss-12Dec2025.csv", fname_end="em_DiamondGCM-Europe.txt",historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)# scenario_dict={"GCAM-Europe-EU_NCEP-LTT": "EU_NCEP_LTT"} )
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv", historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv", historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "/home/masan/temp/DIAMOND_4.4/baseline_run_openprom_reshaped.csv", fname_end="em_DiamondBaseline.txt",historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv", historical="data/historical_emissions_from_emissions_harmonisation_Sep2025.csv", glue_historical=True)
    #make_emissions_scenario_files("data/gases_vupdate_2024_WMO_added_new.txt", "data/20250818_0003_0003_0002_infilled-emissions.csv")
            
            #print "Success " + (',').join(line)
    #print counter
    #print years
    #sys.exit(4)
    #print full_data_dict["SSP2-45"]
    #print unit_dict

    ##Now printing the data to scenario files file:
    

        
                
                
