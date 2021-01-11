#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file includes all the functions for the analysis.
"""
import numpy as np
import pandas as pd
import geopandas as gp # make sure descartes and shapely are installed
from pandas.api.types import CategoricalDtype

#
def calculate_total_daily_traffic(df_ampm):

    """
    Function to group df_ampm by station, date, and day name and
    sum up daily entries and exits to generate total daily traffic data.
    Therefore, the total daily traffic data sums am and pm traffic.
    """
    # sum daily entries for the group
    df_daily = df_ampm.groupby(
        ["STATION", "DATE", "DAY_NAME"], as_index=False
    ).TMP_ENTRIES.sum()
    df_daily.rename(columns={"TMP_ENTRIES": "DAILY_ENTRIES"}, inplace=True)
    # sum daily exits for the group
    t_df = df_ampm.groupby(
        ["STATION", "DATE", "DAY_NAME"], as_index=False
    ).TMP_EXITS.sum()
    df_daily["DAILY_EXITS"] = t_df.TMP_EXITS
    # sum daily entries and exits to obtain daily traffic
    df_daily["DAILY_TRAFFIC"] = df_daily.DAILY_ENTRIES + df_daily.DAILY_EXITS
    return df_daily


def set_axis(
    handle,
    x_label=None,
    y_label=None,
    fontsize=None,
    rot_xticklabels=None,
    bar_width=1,
    x_lim=None,
    y_lim=None,
    x_ticks=None,
    y_ticks=None,
    horizontal_alignment="left",
):
    """
    Function to set figure axes.
    """
    handle.set_xlabel(x_label, fontsize=fontsize)
    handle.set_ylabel(y_label, fontsize=fontsize)
    x_ticks = handle.get_xticks()
    y_ticks = handle.get_yticks()

    if x_ticks is not None:
        handle.set_xticks = x_ticks
    if y_ticks is not None:
        handle.set_yticks = y_ticks

    x_ticklabels = handle.get_xticklabels()
    handle.set_xticklabels(
        x_ticklabels, rotation=rot_xticklabels, ha=horizontal_alignment
    )

    x_ticklabels = handle.get_xticklabels()
    for t_x in x_ticklabels:
        t_x.set_fontsize(fontsize)

    y_ticklabels = handle.get_yticklabels()
    for t_y in y_ticklabels:
        t_y.set_fontsize(fontsize)

    for t_h in handle.patches:
        t_h.set_width(bar_width)

    if x_lim is not None:
        handle.set_xlim(x_lim)
    if y_lim is not None:
        handle.set_ylim(y_lim)
    #


def sort_by_day_name(t_df):
    """
    Function to sort a data frame by day name
    """
    cat_day_of_week = CategoricalDtype(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )

    t_df["DAY_NAME2"] = t_df.index.astype(cat_day_of_week)
    t_df = t_df.sort_values(["DAY_NAME2"])
    t_df["DAY_NAME2"] = t_df.index

    return t_df


def generate_mask_for_top_stations(top_stations, top_stations_name, df_daily):
    """
    Function to generate mask for top_stations based on station name
    """
    mask2 = np.zeros((len(df_daily["STATION"]), len(top_stations)))
    for i, t_name in enumerate(top_stations_name):
        mask = (df_daily["STATION"] == t_name).to_numpy()
        mask2[:, i] = mask
    mask = mask2.any(axis=1)
    return mask


def sort_by_station(top_stations_name, df_to_sort):
    """
    Function to sort the data frame by station name
    """
    cat_station = CategoricalDtype(top_stations_name, ordered=True)

    df_to_sort["STATION"] = df_to_sort["STATION"].astype(cat_station)
    df_sorted = df_to_sort.sort_values(["STATION"])
    return df_sorted


def calculate_daily_traffic_ampm(df_ampm):
    """
    Function to calculate daily traffic with am/mp time separated,
    which is different from "calculate_total_daily_traffic" above
    """
    #
    df_daily2 = df_ampm.groupby(
        ["C/A", "UNIT", "SCP", "STATION", "DATE", "DAY_NAME", "AMPM"], as_index=False
    ).TMP_ENTRIES.min()
    df_daily2.rename(columns={"TMP_ENTRIES": "DAILY_ENTRIES"}, inplace=True)
    t_df = df_ampm.groupby(
        ["C/A", "UNIT", "SCP", "STATION", "DATE", "DAY_NAME", "AMPM"], as_index=False
    ).TMP_EXITS.min()

    df_daily2["DAILY_EXITS"] = t_df.TMP_EXITS
    df_daily2["DAILY_TRAFFIC"] = df_daily2.DAILY_ENTRIES + df_daily2.DAILY_EXITS
    df_daily2 = df_daily2.groupby(
        ["STATION", "DATE", "DAY_NAME", "AMPM"], as_index=False
    ).sum()
    #
    return df_daily2


def calculate_weekly_traffic_ampm_for_top_stations(
    top_stations, top_stations_name, df_daily2
):
    """
    Function to calculate weekly traffic with am/pm time separted
    for the top stations.
    """
    mask = (df_daily2["DAY_NAME"] == "Sunday") | (df_daily2["DAY_NAME"] == "Saturday")
    df_weekends = df_daily2[mask]
    df_weekdays = df_daily2[~mask]
    # get weekday AMPM data
    mask = generate_mask_for_top_stations(top_stations, top_stations_name, df_weekdays)
    # average for each station
    t_wkd = df_weekdays[mask].groupby(["STATION", "AMPM"], as_index=False).mean()
    t_wkd = t_wkd.drop(["DAILY_ENTRIES", "DAILY_EXITS"], axis=1)
    #
    t_wkd_am = t_wkd[t_wkd["AMPM"] == "AM"]
    t_wkd_am = sort_by_station(top_stations_name, t_wkd_am)
    #
    t_wkd_pm = t_wkd[t_wkd["AMPM"] == "PM"]
    t_wkd_pm = sort_by_station(top_stations_name, t_wkd_pm)
    # now, generate weekend AMPM data
    mask = generate_mask_for_top_stations(top_stations, top_stations_name, df_weekends)
    # average for each station
    t_wke = df_weekends[mask].groupby(["STATION", "AMPM"], as_index=False).mean()
    t_wke = t_wke.drop(["DAILY_ENTRIES", "DAILY_EXITS"], axis=1)

    t_wke_am = t_wke[t_wke["AMPM"] == "AM"]
    t_wke_am = sort_by_station(top_stations_name, t_wke_am)

    t_wke_pm = t_wke[t_wke["AMPM"] == "PM"]
    t_wke_pm = sort_by_station(top_stations_name, t_wke_pm)
    #
    return t_wkd_am, t_wkd_pm, t_wke_am, t_wke_pm


def map_stations_daily_traffic(df_daily):
    """
    Function to join Latitude and Longitude information based on data from all stations.  
    """

    # get Lat/Lon data
    mta_stations = pd.read_csv(
        "http://web.mta.info/developers/data/nyct/subway/Stations.csv"
    )
    mta_stations.rename(
        columns={
            "Stop Name": "STATION",
            "GTFS Latitude": "Lat",
            "GTFS Longitude": "Lon",
        },
        inplace=True,
    )

    # rename STATION to all uppercase to stay consistent with df_daily station names
    mta_stations["STATION"] = mta_stations["STATION"].str.upper()

    # set index as STATION as pd.merge() requires the indexes of df_daily and mta_stations to be identical
    mta_stations.set_index(["STATION"], inplace=True)
    df_daily.set_index(["STATION"], inplace=True)

    # merge on right, as to fill in for every station in df_daily
    df_daily_map = pd.merge(mta_stations, df_daily, on="STATION", how="right")

    # remove un-needed columns
    df_daily_map.drop(
        [
            "Station ID",
            "Complex ID",
            "GTFS Stop ID",
            "Division",
            "Line",
            "Borough",
            "Daytime Routes",
            "Structure",
            "North Direction Label",
            "South Direction Label",
            "ADA",
            "ADA Notes",
        ],
        axis=1,
        inplace=True,
    )

    return df_daily_map


def map_agi_by_zipcode(df_ampm):
    """
    Function to merge in geopandas "Shape" parameters on zipcode, used to graph agi by NYC zipcode area.
    Takes in df_ampm.
    """

    # read in necessary parameters to run geopandas, rename postalCode to zipcode (common name with df_daily_map)
    geopandas_data = gp.read_file("data/nyc-zip-code-tabulation-areas-polygons.geojson")
    geopandas_data["ZIPCODE"] = geopandas_data["postalCode"].astype(int)

    # convert df_ampm's ZIPCODE to an int-type
    df_ampm["ZIPCODE"] = pd.to_numeric(df_ampm["ZIPCODE"], errors="coerce")
    df_ampm = df_ampm.dropna(subset=["ZIPCODE"])
    df_ampm["ZIPCODE"] = df_ampm["ZIPCODE"].astype(int)

    # merge in geopandas_data on zipcode
    df_agi_by_zipcode_map = pd.merge(geopandas_data, df_ampm, on="ZIPCODE")

    # remove messy & unnecessary columns
    df_agi_by_zipcode_map.drop(
        [
            "OBJECTID",
            "postalCode",
            "PO_NAME",
            "STATE",
            "borough",
            "ST_FIPS",
            "CTY_FIPS",
            "BLDGpostalCode",
            "@id",
        ],
        axis=1,
        inplace=True,
    )

    return df_agi_by_zipcode_map
