import pandas as pd
import re


def get_speaking_rate(df):
    return (98 / df["Total_duration"][0]) * 60


def get_artic_rate(df):
    return 147 / df["Speech_duration"][0]


def get_subject_id(df):
    fname = df["File Name"][0]
    return fname[0 : fname.find("_")]


def get_date(df):
    fname = df["File Name"][0]
    return fname[re.search("Bamboo_", fname).end() : fname.find(" ")]


def process_spa(fpath):
    df = pd.read_excel(
        fpath,
        sheet_name="Pause Statistics",
        header=1,
        usecols=[
            "File Name",
            "%Pause",
            "%Speech",
            "Pause_duration",
            "Speech_duration",
            "Total_duration",
            "Pause_events",
            "Speech_events",
        ],
    )
    df.insert(0, "DATE", get_date(df))
    df.insert(0, "ID", get_subject_id(df))
    df["SR"] = get_speaking_rate(df)
    df["AR"] = get_artic_rate(df)

    return df.rename(
        columns={
            "%Pause": "PAUSE_PERC",
            "%Speech": "SPEECH_PERC",
            "Pause_duration": "PAUSE_DIR",
            "Speech_duration": "SPEECH_DUR",
            "Total_duration": "TOT_DUR",
            "Pause_events": "PAUSE_EVENTS",
            "Speech_events": "SPEECH_EVENTS",
        },
    ).drop("File Name", axis=1)
