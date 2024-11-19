from parsing import parse, load_key
from pathlib import Path
import statistics
import pandas as pd
import sys

MIRROR_STRUCTURE = False

DATA_DIR = "L:/Research Project Current/Social Connectedness/Nelson/dev"
OUT_ROOT = "L:/Research Project Current/Social Connectedness/Nelson/dev/results"
KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"


def process(data_dir, out_root, key_path, mirror_structure):
    """Create a cleaned and scored copy of all survey CSVs in `data_dir`
    saved in `out_root` either by survey ID (`mirror_structure` == False)
    or in exactly the same layout as `data_dir` (`mirror_structure` == True)

    Args:
        data_dir (str): Path to root directory where data is stored
        out_root (str): Path to directory in which data will be saved
        key_path (str): Path to CSV key containing survey scoring rules
        mirror_structure (bool): Flag to either mirror structure of `data_dir` or save by survey ID

    Raises:
        Exception: KeyError if survey ID does not exist in the provided key
    """
    out_root = Path(out_root)
    out_root.mkdir(exist_ok=True)

    survey_key = load_key(key_path)
    for file in Path(data_dir).glob("[!results]**/**/*.csv"):
        try:
            this_key = survey_key[file.parent.name]
        except KeyError:
            raise Exception("Survey ID not found in key.")

        if this_key["index"] is None and this_key["invert"] is None:
            continue

        if mirror_structure:
            out_dir = out_root.joinpath(
                file.parent.relative_to(data_dir)
            )  # Mirror path in results directory
            prefix = ""
        else:
            # Group by survey id
            out_dir = out_root.joinpath(file.parent.name)
            prefix = file.parent.parent.parent.name

        out_dir.mkdir(exist_ok=True, parents=True)
        parse(file, out_dir, this_key, prefix)


def aggregate(results_dir, key_path):
    """Take all processed data and create a summary sheet saved to `results_dir`.
    Requires data be saved by survey ID (process called with mirror_structure = False)

    Args:
        results_dir (str): Path to directory in which both `processed` data exists and summary sheet will be saved
        key_path (str): Path to CSV key containing survey scoring rules
    """
    results_dir = Path(results_dir)
    survey_key = load_key(key_path)

    # Aggregate
    aggs = {}  # Dictionary of dataframes
    summary = {}  # Dictionary (keys = subject ids) of dictionaries (keys = survey ids, values = list of survey score sums)
    for spath in results_dir.glob("*"):
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

            # Do not add to final statistics if there is missing/bad data
            if not isinstance(sum_field, str):
                if subject_id in summary.keys():
                    if spath.name in summary[subject_id].keys():
                        summary[subject_id][spath.name].append(this_df.score.sum())
                    else:
                        summary[subject_id][spath.name] = [this_df.score.sum()]
                else:
                    summary[subject_id] = {spath.name: [this_df.score.sum()]}

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

    # Extract statistics from lists of sums (that are buried in summary dict)
    subj_ids = []
    surv_names = []
    n = []
    avgs = []
    stds = []
    for s_id, survey_dicts in summary.items():
        for survey_id, survey_sum in survey_dicts.items():
            subj_ids.append(s_id)
            surv_names.append(survey_key[survey_id]["name"])
            n.append(len(survey_sum))
            avgs.append(statistics.fmean(survey_sum))
            if len(survey_sum) > 1:
                stds.append(statistics.stdev(survey_sum))
            else:
                stds.append(float("nan"))

    # Build DF
    summary_df = pd.DataFrame(
        {
            "Subject ID": subj_ids,
            "Survey Name": surv_names,
            "n": n,
            "Mean": avgs,
            "STD": stds,
        }
    )

    # Loop through aggregated dataframes and save to separate sheets
    with pd.ExcelWriter(results_dir.joinpath("SUMMARY_SHEET.xlsx")) as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        for name, df in aggs.items():
            df.to_excel(writer, sheet_name=name, index=False)

########### CLI ###########
if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3 and args[1] == "process":
        print(
            "Processing surveys using default arguments:\ndata_dir = ",
            DATA_DIR,
            "\nout_dir = ",
            OUT_ROOT,
            "\nkey = ",
            KEY_PATH,
            "\nmirror_path = ",
            MIRROR_STRUCTURE,
        )
        process(DATA_DIR, OUT_ROOT, KEY_PATH, MIRROR_STRUCTURE)
    elif len(args) < 3 and args[1] == "aggregate":
        print(
            "Aggregating using default arguments:\nout_dir = ",
            OUT_ROOT,
            "\nkey = ",
            KEY_PATH,
        )
        aggregate(OUT_ROOT, KEY_PATH)
    else:
        print("Running ", args[1], " function with supplied arguments")
        globals()[args[1]](*args[2:])
    print("Complete!")
