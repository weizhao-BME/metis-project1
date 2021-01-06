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
    a = soup.find_all("a")
    o = ()
    # correct files start at index 37
    start = 37
    if num_weeks is None:
        end = len(a)
    else:
        end = start + num_weeks
    for i in range(start, end):
        # for i in range(37, len(a)):
        ins = (
            a[i].get_text(),
            URL_PREFACE + a[i]["href"],
        )
        o = o + (ins,)

    col = [
        "C/A",
        "UNIT",
        "SCP",
        "STATION",
        "LINENAME",
        "DIVISION",
        "DATE",
        "TIME",
        "DESC",
        "ENTRIES",
        "EXITS",
    ]
    data = pd.DataFrame()

    for a, b in o:
        d = a[-4:]
        if d.find("2020") != -1:
            df = pd.read_csv(
                b, sep=r"\s*,\s*", header=0, engine="python"
            )  # else "EXITS" gives an error, python engine will avoid warning
            df["dt"] = df["DATE"] + " " + df["TIME"]
            data = pd.concat([data, df])
            data.sort_values(by=["STATION", "SCP", "dt"], inplace=True)

    data["dt"] = pd.to_datetime(data.dt)

    # add unique identifier for each turnstile
    data["station_scp"] = data.STATION + " " + data.SCP
    # sort by new identifier, then datetime
    data.sort_values(by=["station_scp", "dt"], inplace=True)

    groups = data.groupby("station_scp")

    dfs = {}
    
    for name, group in groups:
        new_df = group.copy()
        new_df["hourly_entries"] = new_df.ENTRIES.diff()
        new_df['hourly_entries'] = new_df["hourly_entries"].fillna(0)
        
        new_df["hourly_exits"] = new_df.EXITS.diff()
        new_df['hourly_exits'] = new_df["hourly_exits"].fillna(0)
        dfs[name] = new_df

    df = pd.concat(dfs).reset_index()

    return pd.DataFrame(df)
