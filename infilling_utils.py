"""Infilling of missing emissions species, ported from emissions_harmonization_historical (notebook 5190_infilling)."""

from functools import partial

import numpy as np
import pandas as pd
import pandas_indexing as pix
import pyam
import silicone.database_crunchers
from gcages.renaming import SupportedNamingConventions, convert_variable_name

from infilling_data import (
    HISTORY_PATH,
    INFILLING_END_YEAR,
    INFILLING_START_YEAR,
    LEAD_VARIABLE,
    MARKER_DB_PATH,
    load_infilling_inputs,
)
from misc_utils import component_renaming

PI_YEAR = 1750
# Scenario/history ratio below which a species is treated as incomplete (e.g. missing AFOLU) and infilled
TOO_LOW_RATIO = 0.5
# Max distance in log10 from a power of 1000 for a ratio to count as a unit-prefix mislabel
MISLABEL_LOG10_TOLERANCE = 0.5

_to_reporting_names = partial(
    convert_variable_name,
    from_convention=SupportedNamingConventions.GCAGES,
    to_convention=SupportedNamingConventions.CMIP7_SCENARIOMIP,
)

SCALING_LEADERS = {
    _to_reporting_names(k): _to_reporting_names(v)
    for k, v in {
        "Emissions|C3F8": "Emissions|C2F6",
        "Emissions|C4F10": "Emissions|C2F6",
        "Emissions|C5F12": "Emissions|C2F6",
        "Emissions|C7F16": "Emissions|C2F6",
        "Emissions|C8F18": "Emissions|C2F6",
        "Emissions|cC4F8": "Emissions|CF4",
        "Emissions|SO2F2": "Emissions|CF4",
        "Emissions|HFC236fa": "Emissions|HFC245fa",
        "Emissions|HFC152a": "Emissions|HFC4310mee",
        "Emissions|HFC365mfc": "Emissions|HFC134a",
        "Emissions|CH2Cl2": "Emissions|HFC134a",
        "Emissions|CHCl3": "Emissions|C2F6",
        "Emissions|NF3": "Emissions|SF6",
    }.items()
}


def get_silicone_based_infiller(infilling_db, follower_variable, lead_variables, silicone_db_cruncher):
    silicone_infiller = silicone_db_cruncher(pyam.IamDataFrame(infilling_db)).derive_relationship(
        variable_follower=follower_variable, variable_leaders=lead_variables
    )

    def res(inp):
        res_h = silicone_infiller(pyam.IamDataFrame(inp)).timeseries()
        # Upstream notes this filter works around a silicone bug
        return res_h.loc[:, inp.dropna(axis="columns", how="all").columns]

    return res


def get_direct_copy_infiller(variable, copy_from):
    def infiller(inp):
        model_l = inp.pix.unique("model")
        scenario_l = inp.pix.unique("scenario")
        if len(model_l) != 1 or len(scenario_l) != 1:
            raise AssertionError((model_l, scenario_l))
        return copy_from.loc[pix.isin(variable=variable)].pix.assign(model=model_l[0], scenario=scenario_l[0])

    return infiller


def get_direct_scaling_infiller(leader, follower, scaling_factor, l_0, f_0, f_unit, calculation_year, f_calculation_year):
    def infiller(inp):
        lead_df = inp.loc[pix.isin(variable=[leader])]
        follow_df = (scaling_factor * (lead_df - l_0) + f_0).pix.assign(variable=follower, unit=f_unit)
        if calculation_year in follow_df.columns and not np.isclose(follow_df[calculation_year], f_calculation_year).all():
            raise AssertionError(f"Scaled {follower} does not match history in {calculation_year}")
        return follow_df

    return infiller


def infill(indf, infillers):
    infilled_l = []
    for variable in infillers:
        for _, msdf in indf.groupby(["model", "scenario"]):
            if variable not in msdf.index.get_level_values("variable"):
                infilled_l.append(infillers[variable](msdf))
    if not infilled_l:
        return None
    return pix.concat(infilled_l)


def get_complete(indf, infilled):
    if infilled is None:
        return indf
    return pix.concat([indf, infilled])


def _silicone_infillers(db):
    return {
        variable: get_silicone_based_infiller(
            infilling_db=db,
            follower_variable=variable,
            lead_variables=[LEAD_VARIABLE],
            silicone_db_cruncher=silicone.database_crunchers.RMSClosest,
        )
        for variable in db.pix.unique("variable")
        if variable != LEAD_VARIABLE
    }


def get_scaling_infillers(history):
    infillers = {}
    for follower, leader in SCALING_LEADERS.items():
        lead_df = history.loc[pix.isin(variable=[leader])]
        follow_df = history.loc[pix.isin(variable=[follower])]
        f_unit = follow_df.pix.unique("unit")[0].replace("-", "")

        for calculation_year in [INFILLING_START_YEAR, 2021]:
            l_cy = float(lead_df[calculation_year].values.squeeze())
            f_cy = float(follow_df[calculation_year].values.squeeze())
            if not (pd.isnull(l_cy) or pd.isnull(f_cy)):
                break
        else:
            raise AssertionError(f"No history value to scale {follower} from {leader}")

        # Upstream takes these from CMIP7 GHG inversions, which the history 1750 values are built from
        f_0 = float(follow_df[PI_YEAR].values.squeeze())
        l_0 = float(lead_df[PI_YEAR].values.squeeze())

        infillers[follower] = get_direct_scaling_infiller(
            leader=leader,
            follower=follower,
            scaling_factor=(f_cy - f_0) / (l_cy - l_0),
            l_0=l_0,
            f_0=f_0,
            f_unit=f_unit,
            calculation_year=calculation_year,
            f_calculation_year=f_cy,
        )
    return infillers


def prepare_infilling(marker_db_path=MARKER_DB_PATH, history_path=HISTORY_PATH, infilling_db_path=None):
    inputs = load_infilling_inputs(marker_db_path, history_path, infilling_db_path)
    inputs["infiller_stages"] = [
        _silicone_infillers(inputs["marker_db"]),
        _silicone_infillers(inputs["silicone_db"]),
        {v: get_direct_copy_infiller(v, inputs["wmo_db"]) for v in inputs["wmo_db"].pix.unique("variable")},
        get_scaling_infillers(inputs["history"]),
    ]
    return inputs


def history_series_for_component(history, component):
    """Return (iamc_unit, years, values) of the history row mapping to a CICERO component, or None."""
    for (variable, unit), row in history.droplevel(["model", "scenario", "region"]).iterrows():
        if component_renaming(variable.split("|")[-1], variable) == component:
            valid = row.notna()
            return unit, row.index[valid].to_numpy(dtype=float), row[valid].to_numpy(dtype=float)
    return None


def classify_against_history(scenario_value, history_value):
    """Return ("ok" | "rescale" | "infill", factor to multiply the scenario by)."""
    if not (history_value > 0 and scenario_value > 0):
        return "ok", 1.0
    log_ratio = np.log10(scenario_value / history_value)
    k = round(log_ratio / 3)
    if k != 0 and abs(log_ratio - 3 * k) < MISLABEL_LOG10_TOLERANCE:
        return "rescale", 1000.0 ** -k
    if scenario_value / history_value < TOO_LOW_RATIO:
        return "infill", 1.0
    return "ok", 1.0


def _build_lead_df(lead_values, lead_unit, years, model, scenario, history):
    """Annual lead timeseries from INFILLING_START_YEAR, bridged from history if the scenario starts later."""
    end_year = min(int(years[-1]), INFILLING_END_YEAR)
    infill_years = np.arange(INFILLING_START_YEAR, end_year + 1)
    lead_years = np.asarray(years, dtype=float)
    lead_values = np.asarray(lead_values, dtype=float)
    if lead_years[0] > INFILLING_START_YEAR:
        hist_lead = history.loc[pix.isin(variable=LEAD_VARIABLE)][INFILLING_START_YEAR].values.squeeze()
        lead_years = np.concatenate(([INFILLING_START_YEAR], lead_years))
        lead_values = np.concatenate(([float(hist_lead)], lead_values))
    index = pd.MultiIndex.from_tuples(
        [(model, scenario, "World", LEAD_VARIABLE, lead_unit)], names=["model", "scenario", "region", "variable", "unit"]
    )
    return pd.DataFrame([np.interp(infill_years, lead_years, lead_values)], index=index, columns=infill_years)


def infill_missing(lead_values, lead_unit, years, missing_components, inputs, model="scenario", scenario="scenario"):
    """
    Infill the CICERO components in missing_components for one scenario.

    Returns {cicero_component: (iamc_unit, values on years)}, or None if infilling is not possible.
    """
    history = inputs["history"]
    db_lead_unit = inputs["marker_db"].loc[pix.isin(variable=LEAD_VARIABLE)].pix.unique("unit")[0]
    if lead_unit != db_lead_unit:
        print(f"Lead unit {lead_unit} differs from infilling DB unit {db_lead_unit}, skipping infilling")
        return None
    if years[-1] < INFILLING_START_YEAR:
        print(f"Scenario ends before {INFILLING_START_YEAR}, skipping infilling")
        return None

    complete = _build_lead_df(lead_values, lead_unit, years, model, scenario, history)
    infill_years = complete.columns
    for infillers in inputs["infiller_stages"]:
        complete = get_complete(complete, infill(complete, infillers)).reindex(columns=infill_years)

    hist_years = [y for y in history.columns if y < INFILLING_START_YEAR]
    result = {}
    for (variable, unit), row in complete.droplevel(["model", "scenario", "region"]).iterrows():
        comp = component_renaming(variable.split("|")[-1], variable)
        if comp not in missing_components or variable == LEAD_VARIABLE:
            continue
        hist_row = history.loc[pix.isin(variable=variable)]
        hist_vals = hist_row[hist_years].values.squeeze() if not hist_row.empty else np.full(len(hist_years), np.nan)
        all_years = np.concatenate((hist_years, infill_years))
        all_vals = np.concatenate((hist_vals, row.values))
        valid = ~np.isnan(all_vals)
        result[comp] = (unit, np.interp(years, all_years[valid], all_vals[valid]))
    return result
