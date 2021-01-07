"""The following functions will be used as Jupyer Notebook imports to quickly generate the MTA necessary for our analysis.

Find more information about the project here: https://github.com/edubu2/metis-project1
"""

from __future__ import print_function, division

import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy as np


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
                pd.read_csv(
                    file_url, parse_dates=[["DATE", "TIME"]], keep_date_col=True
                )
            )
        return pd.concat(dfs)

    def clean_data(df):
        """Removes rows where 'DESC' == 'RECOVR AUD' (not 'REGULAR').
        These caused duplicate entries when grouping by turnstile & datetime.

        Removes DESC column.

        """

        # sort values in a such a way that the duplicate values sit directly below the originals, so they will be removed.
        df.sort_values(
            ["C/A", "UNIT", "SCP", "STATION", "DATE_TIME"],
            inplace=True,
            ascending=False,
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
        df["AMPM"] = pd.DatetimeIndex(df["TIME"]).strftime("%r").str[-2:]
        return df

    def add_day_name(df):
        """
        Function to convert date to day name
        """
        df["DAY_NAME"] = pd.to_datetime(df["DATE"]).dt.day_name()
        return df

    df = get_mta_data2()
    df = clean_data(df)
    df = add_ampm(df)
    df = add_day_name(df)

    """   RENAME "EXITS             " to "EXITS"
   Add in prev_exits, prev_entries (describes hourly entries/exits per turnstile)
    -> NOTE: if value is negative (x<0) or above 20,000 (x>20000), reset to the mean, as is described without these outliers.
   Drop any duplicates in prev_exits.
   What is a duplicate? A duplicate can be multiple entries for entries or exits reported at the exact same time (recall 
   data is collected every 4 hours). This is an impossible feat, so we will disregard these values in their entirety.
   
   Add in hourly_traffic to give an idea for entry/exit per hour per turnstile. We can use this to identify top 10 stations.
    """
    df = df.rename(
        columns={
            "EXITS                                                               ": "EXITS"
        },
        errors="raise",
    )

    df["PREV_EXITS"] = df.EXITS - df.EXITS.shift(1)
    df["PREV_ENTRIES"] = df.ENTRIES - df.ENTRIES.shift(1)

    df["PREV_ENTRIES"] = df["PREV_ENTRIES"].transform(
        lambda x: np.where(
            (x < 0) | (x > 20000), x.mask((x < 0) | (x > 20000)).mean(), x
        )
    )

    df["PREV_EXITS"] = df["PREV_EXITS"].transform(
        lambda x: np.where(
            (x < 0) | (x > 20000), x.mask((x < 0) | (x > 20000)).mean(), x
        )
    )

    df.dropna(subset=["PREV_EXITS"], axis=0, inplace=True)

    df["HOURLY_TRAFFIC"] = df.PREV_EXITS + df.PREV_ENTRIES

    # top 10 stations by hourly_traffic:
    # df.groupby('STATION').HOURLY_TRAFFIC.sum().sort_values(ascending=False)[:10]

    # best turnstile by hourly_traffic
    # best_turnstile = df['HOURLY_TRAFFIC'].idxmax()
    # df.loc[best_turnstile,]

    return df
