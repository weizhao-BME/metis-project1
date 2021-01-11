"""
    This file contains all pre-analysis data gathering & cleaning.
"""

from __future__ import print_function, division

import json
import datetime
import googlemaps
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime as dt


def data_wrangling(
    geocode_api_key="AIzaSyB6cfk-jWkqh24U8yBqYoiNZwtDK4B2Atk",
    week_nums=[191228, 191221, 191214, 191207, 191130, 191123, 191116, 191109],
):
    """
        Takes:
            - geocode_api_key (string, REQUIRED): Free and easy to acquire at https://developers.google.com/maps/documentation/geocoding/start
            - week_nums (optional): List of week numbers for which the MTA data will be pulled.
                - default weeks are Nov 9 - Dec 28, 2019
        Returns:
            - df_turnstiles: all MTA turnstile data (http://web.mta.info/developers/turnstile.html).
            - df_ampm: Dataframe filtered by station by AM/PM for each day.
    """

    if geocode_api_key == "":
        raise ValueError("You must assign a valid key to geocode_api_key parameter")

    # week_nums of all 2019:

    def get_mta_data2():
        """Download data from MTA website and create DT column.
        Returns: dataFrame
        """

        url = "http://web.mta.info/developers/data/nyct/turnstile/turnstile_{}.txt"
        dfs = []

        for week_num in week_nums:
            file_url = url.format(week_num)
            dfs.append(
                pd.read_csv(
                    file_url, parse_dates=[["DATE", "TIME"]], keep_date_col=True
                )
            )
        return pd.concat(dfs)

    def clean_data(df_turnstiles):
        """Removes rows where 'DESC' == 'RECOVR AUD' (not 'REGULAR').
        These caused duplicate entries when grouping by turnstile & datetime.
        - Removes DESC column.
        - Fixes EXITS column name.
        """

        # sort values in a such a way that the duplicate values sit directly below the originals, so they will be removed.
        df_turnstiles.sort_values(
            ["C/A", "UNIT", "SCP", "STATION", "DATE_TIME"],
            inplace=True,
            ascending=False,
        )
        # keeps top row, deletes others
        df_turnstiles.drop_duplicates(
            subset=["C/A", "UNIT", "SCP", "STATION", "DATE_TIME"], inplace=True
        )

        # remove DESC column
        df_turnstiles = df_turnstiles.drop(["DESC"], axis=1, errors="ignore")

        # remove the many spaces in the EXITS column name
        df_turnstiles.rename(
            columns={
                "EXITS                                                               ": "EXITS"
            },
            inplace=True,
        )

        return df_turnstiles

    def add_dt_cols(df_turnstiles):
        """
        Adds 'AMPM' and 'DAY_NAME' columns to the dataFrame.
        """
        df_turnstiles["AMPM"] = (
            pd.DatetimeIndex(df_turnstiles["TIME"]).strftime("%r").str[-2:]
        )

        df_turnstiles["DAY_NAME"] = pd.to_datetime(df_turnstiles["DATE"]).dt.day_name()

        return df_turnstiles

    def merge_zipcode_agi(df_turnstiles):
        """ This function adds ZIPCODE and ZIPCODE_AGI columns to the dataFrame. """

        # define URLs for MTA Station data & IRS Income Info
        mta_url = "http://web.mta.info/developers/data/nyct/subway/Stations.csv"
        irs_url = "https://www.irs.gov/pub/irs-soi/18zpallagi.csv"

        # collect & clean MTA station info
        mta_station_info = pd.read_csv(mta_url)
        mta_station_info.rename(
            columns={
                "Stop Name": "STATION",
                "GTFS Latitude": "Lat",
                "GTFS Longitude": "Lon",
            },
            inplace=True,
        )

        # rename some columns where the names were different in the two tables
        mta_station_info["STATION"] = mta_station_info["STATION"].replace(
            "34 ST-PENN STATION", "34 ST-PENN STA"
        )
        mta_station_info["STATION"] = mta_station_info["STATION"].replace(
            "GRD CNTRL-42 ST", "34 ST-PENN STA"
        )
        mta_station_info["STATION"] = mta_station_info["STATION"].replace(
            "34 ST-HERALD SQ", "34 ST-HERALD"
        )

        # only read data from google if there is no station_zips.json file stored
        try:
            station_zips = json.load(open("data/station_zips.json", "r"))
            assert station_zips["23 ST"] == "10011"
        except:
            # you may need to get your own API Key, this API key will not work for you.
            # get your own at: https://developers.google.com/maps/documentation/geocoding/start
            gmaps = googlemaps.Client(key=geocode_api_key)
            # initialize dictionary to store zipcodes in
            station_zips = {}
            mta_station_names = list(df_turnstiles.STATION.unique())

            for station in mta_station_names:
                address = station + " Station New York City, NY"
                geocode_result = gmaps.geocode(address)
                # use try/except to avoid errors when Google can't find the zipcode (just keep going)
                try:
                    # geocode_result is in a complex json format and requires us to access it like this
                    zipcode = geocode_result[0]["address_components"][6]["long_name"]
                    if len(zipcode) == 5:
                        station_zips[station.upper()] = str(zipcode)
                except:
                    continue

        # add zipcode to df_turnstiles
        df_turnstiles["ZIPCODE"] = df_turnstiles["STATION"].map(station_zips)

        # get AGI (adjusted gross income) into df_turnstiles
        us_zips_agi = pd.read_csv(irs_url)
        us_zips_agi.rename(
            columns={"A00100": "adj_gross_inc"}, inplace=True
        )  # in 18zpallagi.csv, A00100 stands for AGI
        us_zips_agi = (
            us_zips_agi[["zipcode", "adj_gross_inc"]].groupby("zipcode").agg(sum)
        )  # group by zipcode and sum AGI

        # now keep just the data for NYC zipcodes (not the full US)
        nyc_zips = pd.read_csv("data/ny_zips.csv")
        nyc_zips.dropna(axis=1, how="all", inplace=True)
        nyc_agi_by_zip = nyc_zips.join(us_zips_agi, how="inner", on="zipcode")

        # must capitalize col name & change from dtype 'object' to 'str' in order to merge into df_turnstiles
        nyc_agi_by_zip.columns = nyc_agi_by_zip.columns.str.upper()
        nyc_agi_by_zip["ZIPCODE"] = nyc_agi_by_zip.ZIPCODE.astype(str)

        # now merge the ZIPCODE_AGI data into df_turnstiles
        zipcode_agis = (
            nyc_agi_by_zip[["ZIPCODE", "ADJ_GROSS_INC"]]
            .set_index("ZIPCODE")
            .to_dict()["ADJ_GROSS_INC"]
        )
        df_turnstiles["ZIPCODE_AGI"] = df_turnstiles["ZIPCODE"].map(zipcode_agis)

        return df_turnstiles

    def fixup_entries_exits(df_turnstiles):
        """
        Clean entries and exits column.
        Returns a dataFrame grouped by individual turnstile and AM/PM.
        Entries & exit columns converted from cumulative --> change from previous value
        """
        # group data by AMPM, taking the maximum entries/exits for each date
        ampm_station_group = df_turnstiles.groupby(
            ["C/A", "UNIT", "STATION", "DATE", "AMPM", "DAY_NAME",], as_index=False,
        )

        df_ampm = ampm_station_group.ENTRIES.max()
        ampm_station_exits = ampm_station_group.EXITS.max()
        df_ampm["EXITS"] = ampm_station_exits["EXITS"]

        # create prev_date and prev_entries cols by shifting these columns forward one day
        # if shifting date and entries, don't group by date
        df_ampm[["PREV_DATE", "PREV_ENTRIES", "PREV_EXITS"]] = df_ampm.groupby(
            ["C/A", "UNIT", "STATION"]
        )[["DATE", "ENTRIES", "EXITS"]].apply(lambda grp: grp.shift(1))

        # Drop the rows for the earliest date in the df, which are now NaNs for prev_date and prev_entries cols
        df_ampm.dropna(subset=["PREV_DATE"], axis=0, inplace=True)

        df_ampm.head(3)

        def add_counts(row, max_counter, column_name):
            """
                Counts the variance between entries/exits and prev timeframe. entries/exits

                Max counter is the maximum difference between entries & prev. entries that
                we will allow.
            """

            counter = row[column_name] - row[f"PREV_{column_name}"]
            if counter < 0:
                # Maybe counter is reversed?
                counter = -counter

            if counter > max_counter:
                # Maybe counter was reset to 0?
                # take the lower value as the counter for this row
                counter = min(row[column_name], row[f"PREV_{column_name}"])

            if counter > max_counter:
                # Check it again to make sure we're not still giving a counter that's too big
                return 0

            return counter

        # we will use a 200k counter - anything more seems incorrect.
        df_ampm["TMP_ENTRIES"] = df_ampm.apply(
            add_counts, axis=1, max_counter=200000, column_name="ENTRIES"
        )

        # we will use a 200k counter - anything more seems incorrect.
        df_ampm["TMP_EXITS"] = df_ampm.apply(
            add_counts, axis=1, max_counter=200000, column_name="EXITS"
        )

        df_ampm["TRAFFIC"] = df_ampm.TMP_ENTRIES + df_ampm.TMP_EXITS

        # add zipcode to df_ampm
        station_zips = json.load(open("data/station_zips.json", "r"))
        df_ampm["ZIPCODE"] = df_ampm["STATION"].map(station_zips)

        return df_ampm

    def main():
        """
        Execute the nested functions above.
        """
        df_turnstiles = get_mta_data2()
        df_turnstiles = clean_data(df_turnstiles)
        df_turnstiles = add_dt_cols(df_turnstiles)
        df_turnstiles = merge_zipcode_agi(df_turnstiles)

        df_ampm = fixup_entries_exits(df_turnstiles)
        return df_turnstiles, df_ampm

    # now we're back to the main func, data_wrangling()
    df_turnstiles, df_ampm = main()
    return df_turnstiles, df_ampm
