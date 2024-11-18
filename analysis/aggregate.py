# Aggregate scored surveys
# Requires data be stored by survey id (MIRROR_STRUCTURE = False)

import pandas as pd
from pathlib import Path

out_root = Path("L:/Research Project Current/Social Connectedness/Nelson/dev/results")

# Get survey key for readable survey names
key_path = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"

survey_key = pd.read_csv(key_path).T
survey_key = (
    survey_key.rename(columns=survey_key.loc["id"])
    .drop(survey_key.index[0])
    .replace({float("nan"): None})
)

# Aggregate
aggs = {}
for spath in out_root.glob("*"):
    if not spath.is_dir():
        continue
    survey_name = survey_key[spath.name]["name"]
    agg_df = []  # Reset aggregate dataframe every new survey
    for fpath in spath.glob("*.csv"):
        # Collect metadata
        file = fpath.stem
        us_ind = file.find("_")
        sp_ind = file.find(" ")

        subject_id = file[0:us_ind]
        date = file[us_ind + 1 : sp_ind]
        time = file[sp_ind + 1 : file.find("+")]

        # Load file
        this_df = pd.read_csv(fpath, na_filter=False)

        # Establish sum
        if fpath.stem.endswith("PARSE_ERR"):
            sum_field = "PARSING ERROR"
        elif fpath.stem.endswith("SKIPPED_ANS"):
            sum_field = "SKIPPED ANSWER"
        else:
            sum_field = this_df.score.sum()

        # Add this survey's data to aggregate "dataframe" (list, really)
        # Get subscores if ALSFRS
        if "ALSFRS" in survey_name:
            agg_df.append(
                [subject_id, date, time]
                + this_df.score.to_list()
                + [
                    this_df.score[0:3].sum(),
                    this_df.score[3:6].sum(),
                    this_df.score[6:9].sum(),
                    this_df.score[9:12].sum(),
                ]
                + [sum_field]
            )
        else:
            agg_df.append(
                [subject_id, date, time] + this_df.score.to_list() + [sum_field]
            )

    # Create column headers (add subscores for ALSFRS)
    if "ALSFRS" in survey_name:
        cols = (
            ["Subject ID", "date", "time"]
            + this_df["question text"].to_list()
            + ["Bulbar", "Fine Motor", "Gross Motor", "Respiratory", "sum"]
        )
    else:
        cols = (
            ["Subject ID", "date", "time"]
            + this_df["question text"].to_list()
            + ["sum"]
        )

    # Key = readable survey name, value = dataframe of scores for every instance of this survey
    aggs[survey_name] = pd.DataFrame(agg_df, columns=cols)

# Loop through aggregated dataframes and save to separate sheets
with pd.ExcelWriter(out_root.joinpath("SUMMARY_SHEET.xlsx")) as writer:
    for name, df in aggs.items():
        df.to_excel(writer, sheet_name=name, index=False)
