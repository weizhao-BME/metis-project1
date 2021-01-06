import re
import requests
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


def generate_mta_data(num_weeks=None):

    url = "http://web.mta.info/developers/turnstile.html"

    # https://blog.proxypage.io/web-scrape-using-python-in-less-than-5-minutes-2/
    # https://hackersandslackers.com/scraping-urls-with-beautifulsoup/

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # print(soup.prettify()) you can see 'soup' is our entire html page
    URL_PREFACE = "http://web.mta.info/developers/"
    links = soup.find_all("a")
    link_dates = ()
    # correct files start at index 37
    start = 37
    if num_weeks is None:
        end = len(a)
    else:
        end = start + num_weeks
    for i in range(start, end):
        # for i in range(37, len(a)):
        ins = (
            links[i].get_text(),
            URL_PREFACE + links[i]["href"],
        )
        link_dates = link_dates + (ins,)

    col = [
        "c/a",
        "unit",
        "scp",
        "station",
        "linename",
        "division",
        "date",
        "time",
        "desc",
        "entries",
        "exits",
    ]
    data = pd.DataFrame()

    for i, j in link_dates:
        d = i[-4:]
        if d.find("2020") != -1:
            df = pd.read_csv(
                j, sep=r"\s*,\s*", header=None, names=col, engine="python"
            )  # else "EXITS" gives an error, python engine will avoid warning
            data = pd.concat([data, df])

    df = data.copy()
    df.columns = col
    df["dt"] = df["date"] + " " + df["time"]
    # df["dt"] = pd.to_datetime(df.dt)
    df.sort_values(by=["station", "scp", "dt"], inplace=True)

    # add unique identifier for each turnstile
    df["station_scp"] = df.station + " " + df.scp
    # sort by new identifier, then datetime
    df.sort_values(by=["station_scp", "dt"], inplace=True)
    df['entries'] = df.entries.str.strip('0')

    groups = df.groupby("station_scp")

    dfs = {}

#     for name, group in groups:
#         new_df = group.copy()
#         new_df["hourly_entries"] = new_df.entries.diff()
#         new_df["hourly_entries"] = new_df["hourly_entries"].fillna(0)

#         new_df["hourly_exits"] = new_df.exits.diff()
#         new_df["hourly_exits"] = new_df["hourly_exits"].fillna(0)
#         dfs[name] = new_df

#     df = pd.concat(dfs).reset_index()

    return pd.DataFrame(df)