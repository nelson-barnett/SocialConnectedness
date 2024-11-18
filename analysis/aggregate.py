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
    this_df = []  # Reset each survey
    for fpath in spath.glob("*.csv"):
        file = fpath.stem
        us_ind = file.find("_")
        sp_ind = file.find(" ")

        subject_id = file[0:us_ind]
        date = file[us_ind + 1 : sp_ind]
        time = file[sp_ind + 1 : file.find("+")]

        if fpath.stem.endswith("PARSE_ERR"):
            sum_field = "PARSING ERROR"
        elif fpath.stem.endswith("SKIPPED_ANS"):
            sum_field = "SKIPPED ANSWER"
        else:
            score_df = pd.read_csv(fpath, usecols=["score"])
            sum_field = score_df.score.sum()
        this_df.append([subject_id, date, time, sum_field])

    aggs[survey_name] = pd.DataFrame(
        this_df, columns=["Subject ID", "date", "time", "sum"]
    )

# Loop through aggregated dataframes and save to separate sheets
with pd.ExcelWriter(out_root.joinpath("SUMMARY_SHEET.xlsx")) as writer:
    for name, df in aggs.items():
        df.to_excel(writer, sheet_name=name, index=False)
