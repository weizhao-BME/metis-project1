"""
    This file contains all pre-analysis data gathering & cleaning.
"""

from __future__ import print_function, division

import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime as dt


def data_wrangling(
    week_nums=[191228, 191221, 191214, 191207, 191130, 191123, 191116, 191109]
):
    """


    week_nums (optional): the week numbers for which the MTA data will be pulled (list).
        - default weeks are Nov 9 - Dec 28, 2019

    Returns:
        - df_turnstiles: all MTA turnstile data (http://web.mta.info/developers/turnstile.html).
        - df_ampm: Dataframe filtered by station by AM/PM for each day.
    """

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

        df_turnstiles.rename(
            columns={
                "EXITS                                                               ": "EXITS"
            },
            inplace=True,
        )

        return df_turnstiles

    def add_ampm(df_turnstiles):
        """
        Function to convert time to AM/PM
        """
        df_turnstiles["AMPM"] = (
            pd.DatetimeIndex(df_turnstiles["TIME"]).strftime("%r").str[-2:]
        )
        return df_turnstiles

    def add_day_name(df_turnstiles):
        """
        Function to convert date to day name
        """
        df_turnstiles["DAY_NAME"] = pd.to_datetime(df_turnstiles["DATE"]).dt.day_name()
        return df_turnstiles

    def fixup_entries_exits(df_turnstiles):
        """
        Clean entries and exits column.

        Returns a dataFrame grouped by individual turnstile and AM/PM.

        Entries & exit columns converted from cumulative --> change from previous value



        """
        # group data by date, taking the maximum for each date as we
        tmp = df_turnstiles.groupby(
            ["C/A", "UNIT", "SCP", "STATION", "DATE", "AMPM", "DAY_NAME"],
            as_index=False,
        ).ENTRIES.max()

        ##
        t = df_turnstiles.groupby(
            ["C/A", "UNIT", "SCP", "STATION", "DATE", "AMPM", "DAY_NAME"],
            as_index=False,
        ).EXITS.max()
        tmp["EXITS"] = t["EXITS"]

        # create prev_date and prev_entries cols by shifting these columns forward one day
        # if shifting date and entries, don't group by date
        tmp[["PREV_DATE", "PREV_ENTRIES", "PREV_EXITS"]] = tmp.groupby(
            ["C/A", "UNIT", "SCP", "STATION"]
        )[["DATE", "ENTRIES", "EXITS"]].apply(lambda grp: grp.shift(1))

        # Drop the rows for the earliest date in the df, which are now NaNs for prev_date and prev_entries cols
        tmp.dropna(subset=["PREV_DATE"], axis=0, inplace=True)

        def count_entries(row, max_counter):
            """Max counter is the maximum difference between entries & prev. entries that
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
        tmp["TMP_ENTRIES"] = tmp.apply(count_entries, axis=1, max_counter=200000)

        def count_exits(row, max_counter):
            """Max counter is the maximum difference between exits & prev. exits that
            we will allow. Same as above func, but for exits instead of entries.
            """

            counter = row["EXITS"] - row["PREV_EXITS"]
            if counter < 0:
                # Maybe counter is reversed?
                counter = -counter

            if counter > max_counter:
                # Maybe counter was reset to 0?
                # take the lower value as the counter for this row
                counter = min(row["EXITS"], row["PREV_EXITS"])

            if counter > max_counter:
                # Check it again to make sure we're not still giving a counter that's too big
                return 0

            return counter

        # we will use a 200k counter - anything more seems incorrect.
        tmp["TMP_EXITS"] = tmp.apply(count_exits, axis=1, max_counter=200000)
        return tmp

    def main():
        """
        Execute the nested functions above.


        """
        df_turnstiles = get_mta_data2()
        df_turnstiles = clean_data(df_turnstiles)
        df_turnstiles = add_ampm(df_turnstiles)
        df_turnstiles = add_day_name(df_turnstiles)

        df_ampm = fixup_entries_exits(df_turnstiles)
        return df_turnstiles, df_ampm

    df_turnstiles, df_ampm = main()
    return df_turnstiles, df_ampm

