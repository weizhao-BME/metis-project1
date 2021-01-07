from __future__ import print_function, division

import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime as dt

def data_wrangling():
    """
    Data wrangling is performed here and returns a data frame
    """

    def get_mta_data2(week_nums=[160903, 160910, 160917]):
        """Download data from MTA website and create DT column. 

        Returns: dataFrame"""
        url = "http://web.mta.info/developers/data/nyct/turnstile/turnstile_{}.txt"
        dfs = []

        for week_num in week_nums:
            file_url = url.format(week_num)
            dfs.append(
                pd.read_csv(file_url, parse_dates=[["DATE", "TIME"]], keep_date_col=True)
            )
        return pd.concat(dfs)

    def clean_data(df):
        """ Removes rows where 'DESC' == 'RECOVR AUD' (not 'REGULAR').
            These caused duplicate entries when grouping by turnstile & datetime.

            Removes DESC column.

            """

        # sort values in a such a way that the duplicate values sit directly below the originals, so they will be removed.
        df.sort_values(
            ["C/A", "UNIT", "SCP", "STATION", "DATE_TIME"], inplace=True, ascending=False
        )
        # keeps top row, deletes others
        df.drop_duplicates(
            subset=["C/A", "UNIT", "SCP", "STATION", "DATE_TIME"], inplace=True
        )

        # remove DESC column
        df = df.drop(["DESC"], axis=1, errors="ignore")

        return df

    def add_ampm(df):
        """
        Function to convert time tp AM/PM
        """
        df['AMPM'] = pd.DatetimeIndex(df['TIME']).strftime('%r').str[-2:]
        return df

    def add_day_name(df):
        """
        Function to convert date to day name
        """
        df['DAY_NAME'] = pd.to_datetime(df['DATE']).dt.day_name()
        return df
    
    df = get_mta_data2()
    df = clean_data(df)
    df = add_ampm(df)
    df = add_day_name(df)
    
    
    return df


def get_daily_entries(df):

    # group data by date, taking the maximum for each date as we 
    daily_entries = df.groupby(
        ["C/A", "UNIT", "SCP", "STATION", "DATE", "AMPM", "DAY_NAME"], as_index=False
    ).ENTRIES.max()
    # create prev_date and prev_entries cols by shifting these columns forward one day
    daily_entries[["PREV_DATE", "PREV_ENTRIES"]] = daily_entries.groupby(
        ["C/A", "UNIT", "SCP", "STATION", "AMPM", "DAY_NAME"]
    )[["DATE", "ENTRIES"]].apply(lambda grp: grp.shift(1))

    # Drop the rows for the earliest date in the df, which are now NaNs for prev_date and prev_entries cols
    daily_entries.dropna(subset=["PREV_DATE"], axis=0, inplace=True)

    def get_daily_counts(row, max_counter):
        """ Max counter is the maximum difference between entries & prev. entries that
        we will allow.
        """

        counter = row["ENTRIES"] - row["PREV_ENTRIES"]
        if counter < 0:
            # Maybe counter is reversed?
            counter = -counter

        if counter > max_counter:
            # Maybe counter was reset to 0?
            # take the lower value as the counter for this row
            counter = min(row["ENTRIES"], row["PREV_ENTRIES"])

        if counter > max_counter:
            # Check it again to make sure we're not still giving a counter that's too big
            return 0

        return counter

    # we will use a 200k counter - anything more seems incorrect.
    daily_entries["DAILY_ENTRIES"] = daily_entries.apply(
        get_daily_counts, axis=1, max_counter=200000
    )
    return daily_entries

