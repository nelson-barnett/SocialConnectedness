import pandas as pd
import datetime
import matplotlib.pyplot as plt
from pathlib import Path

def overview_table(summary_path, out_dir, out_name = "timepoint_summary"):
    df = pd.read_excel(summary_path, na_filter=False)

    # Columns with date information
    date_cols = [col for col in df.columns if "date" in col]

    # Get unique dates for each subject for each survey
    df.groupby("Subject ID")[date_cols].agg(["unique"])
    df_dateset = df.groupby("Subject ID")[date_cols].agg(set)

    # There may be a much cleaner way to do this. I couldn't think of one.
    # Isolate unique survey dates per subject
    def f(ser):
        a = set()
        [a.update(x) for x in ser if x != {""}]
        return list(a)

    # This might be improperly written, but it works. Experiment if time.
    # Go through each subject (index) (returns a Series), and apply f.
    # Store as dict with subject as key, unique dates they completed a survey as value.
    # D = {subject:[f(df_dateset.loc[subject])] for subject in df_dateset.index}
    D = {
        subject: sorted(
            f(df_dateset.loc[subject]),
            key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"),
        )
        for subject in df_dateset.index
    }

    max_timepoints = max(len(x) for x in D.values())
    cols = ["time_point_" + str(x) for x in range(1, max_timepoints + 1)]

    df_timepoints = pd.DataFrame.from_dict(D, orient="index", columns=cols)
    df_timepoints.insert(0, "subject_id", df_timepoints.index)
    df_timepoints = df_timepoints.reset_index()
    df_timepoints.drop("index", axis=1, inplace=True)
    df_timepoints.sort_values("time_point_1", inplace=True)

    df_timepoints.to_csv(Path(out_dir).joinpath(out_name + ".csv"), index=False)

    # # DF with Subject IDs as index and lists of unique dates they completed a survey as values
    # df_dates = pd.DataFrame.from_dict(D, orient="index", columns=["survey_timepoints"])

    # # Expand it
    # df_dates_explode = df_dates["survey_timepoints"].explode()

    # # Dictionary with date as key and subject IDs who completed a survey on that date as values
    # D2 = {
    #     d: list(df_dates_explode[df_dates_explode == d].index.array)
    #     for d in df_dates_explode
    # }

    # # Apply padding
    # max_vals = max(len(x) for x in D2.values())
    # D3 = {k: D2[k] + [None] * (max_vals - len(D2[k])) for k in D2.keys()}

    # # Data frame with unique dates as columns and subjects who completed a survey on that date as values
    # df_unique_dates = pd.DataFrame(D3)

    # df_unique_dates.apply(lambda x: x.notnull().sum())


def alsfrs_hist(summary_path, sheet_name="ALSFRS-R"):
    df = pd.read_excel(summary_path, na_filter=False, sheet_name=sheet_name)

    plot_inds = df.index[df["sum"].map(lambda x: not isinstance(x, str))]

    plt.figure()
    df.loc[plot_inds, "sum"].hist(bins=list(range(0, 52, 2)))

    plt.figure()
    df.loc[plot_inds, "Bulbar"].hist(bins=list(range(0, 16, 2)))

    plt.show(block=False)
