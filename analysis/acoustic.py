import pandas as pd
import re


def get_speaking_rate(df, n_words=98):
    return (n_words / df["total_duration"][0]) * 60


def get_artic_rate(df, n_syl=147):
    return n_syl / df["speech_duration"][0]


def get_subject_id(df):
    fname = df["file name"][0]
    return fname[0 : fname.find("_")]


def get_date(df):
    fname = df["file name"][0]
    return fname[re.search("Bamboo_", fname).end() : fname.find(" ")]


def process_spa(fpath):
    drop_cols = [
        "file name",
        "iteration",
        "threshold",
        "peak frequency",
        "peak amplitude",
        "3 db bandwidth",
        "speech_threshold",
        "pause_threshold",
        "type",
        "calc_time",
        "mean_pause",
        "mean_speech",
        "stddev_pause",
        "stddev_speech",
        "cv_speech_duration",
        "cv_pause_duration",
        "cvr",
        "stddev_allsignal",
        "mean_minimum_speech",
        "mean_maximum_speech",
        "mean_mean_speech",
        "mean_stddev_speech",
        "stddev_minimum_speech",
        "stddev_maximum_speech",
        "stddev_mean_speech",
        "stddev_stddev_speech",
        "cv_minimum_speech",
        "cv_maximum_speech",
        "cv_mean_speech",
        "cv_stddev_speech",
        "mean_minimum_pause",
        "mean_maximum_pause",
        "mean_mean_pause",
        "mean_stddev_pause",
        "stddev_minimum_pause",
        "stddev_maximum_pause",
        "stddev_mean_pause",
        "stddev_stddev_pause",
        "cv_minimum_pause",
        "cv_maximum_pause",
        "cv_mean_pause",
        "cv_stddev_pause",
    ]

    # Would like to use "usecols", but that may drop analyst-added columns
    # if they are mispelled or in any way different than expected
    df = pd.read_excel(
        fpath,
        sheet_name="Pause Statistics",
        header=1,
    )
    # Lower to make searching for user inputted column names easier
    df.columns = df.columns.str.lower()

    # in case someone writes "effort" instead of "listener effort"
    effort_col_ind = df.filter(like="effort").columns
    effort_col_name = effort_col_ind[0] if not effort_col_ind.empty else ""

    # Add data
    df.insert(0, "DATE", get_date(df))
    df.insert(0, "ID", get_subject_id(df))
    
    SR = get_speaking_rate(df, df.n_words) if "n_words" in df.columns else get_speaking_rate(df)
    AR = get_artic_rate(df, df.n_syl) if "n_syl" in df.columns else get_artic_rate(df)
    
    df.insert(10, "SR", SR)
    df.insert(11, "AR", AR)

    # Rename cols and drop unwanted ones
    return df.rename(
        columns={
            "%pause": "PAUSE_PERC",
            "%speech": "SPEECH_PERC",
            "pause_duration": "PAUSE_DIR",
            "speech_duration": "SPEECH_DUR",
            "total_duration": "TOT_DUR",
            "pause_events": "PAUSE_EVENTS",
            "speech_events": "SPEECH_EVENTS",
            effort_col_name: "LISTENER_EFFORT",
        },
    ).drop(drop_cols, axis=1)
