from survey import Survey
from pathlib import Path
import statistics
import pandas as pd
import warnings
import argparse
from forest.jasmine.traj2stats import Frequency, gps_stats_main
from functools import reduce
from utils import call_function_with_args, load_key, excel_style
from acoustic import process_spa
from gps import find_n_cont_days, day_to_obs_day, date_series_to_str

DATA_DIR_SURVEY = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_data"
)
OUT_ROOT_SURVEY = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_results"
)

DATA_DIR_GPS = (
    "L:/Research Project Current/Social Connectedness/Nelson/additional test GPS"
)
OUT_ROOT_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/GPS downloaded from Biewe/results"

DATA_DIR_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data/spa_outputs"
OUT_ROOT_ACOUSTIC = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data"
)

KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"


def process_survey(data_dir, out_root, key_path, subject_id="", survey_id=""):
    """Create a cleaned and scored copy of all survey CSVs in `data_dir`
    saved in `out_root` by survey ID

    Args:
        data_dir (str): Path to root directory where data is stored
        out_root (str): Path to directory in which data will be saved
        key_path (str): Path to CSV key containing survey scoring rules

    Raises:
        Exception: KeyError if survey ID does not exist in the provided key
    """
    out_root = Path(out_root)
    out_root.mkdir(exist_ok=True)

    key_df = load_key(key_path)
    for file in Path(data_dir).glob("**/*.csv"):
        try:
            this_key = key_df[file.parent.name]
        except KeyError:
            raise Exception("Survey ID not found in key.")

        this_subj_id = file.parent.parent.parent.name

        if (subject_id and this_subj_id != subject_id) or (
            survey_id and file.parent.name != survey_id
        ):
            continue

        out_dir = out_root.joinpath(file.parent.name)
        out_dir.mkdir(exist_ok=True, parents=True)
        this_survey = Survey(file, key=this_key, subject_id=this_subj_id)

        # If there is no scoring to be done, just clean and save survey
        if this_key["index"] is None and this_key["invert"] is None:
            this_survey.clean(minimal=True)
        else:
            this_survey.parse_and_score()
        this_survey.export(out_dir)


def aggregate_survey(data_dir, out_path, key_path, out_name="SURVEY_SUMMARY"):
    """Take all processed data and create a summary sheet saved to `data_dir`.

    Args:
        data_dir (str): Path to directory in which both `processed` data exists and summary sheet will be saved
        key_path (str): Path to CSV key containing survey scoring rules
    """
    data_dir = Path(data_dir)
    survey_key = load_key(key_path)

    # Aggregate
    aggs_dict = {}  # Dictionary of dataframes
    stats = {}  # Dictionary (keys = subject ids) of dictionaries (keys = survey ids, values = list of survey score sums)
    for spath in data_dir.glob("*"):
        if not spath.is_dir():
            continue
        survey_name = survey_key[spath.name]["name"]
        agg_list = []  # Reset aggregate dataframe every new survey
        for fpath in spath.glob("*.csv"):
            # Collect metadata
            file = fpath.stem
            us_ind = file.find("_")
            sp_ind = file.find(" ")

            subject_id = file[0:us_ind]
            date = file[us_ind + 1 : sp_ind]
            time = file[sp_ind + 1 : file.find("+")]

            # Parse datetime
            # dt = file[us_ind + 1 : file.find("+")]
            # datetime.strptime(dt, "%Y-%m-%d %H_%M_%S")

            # Load file
            this_df = pd.read_csv(fpath, na_filter=False)
            is_nonnumeric = "score" not in this_df.columns

            # Establish sum
            if fpath.stem.endswith("PARSE_ERR"):
                sum_field = "PARSING ERROR"
            elif fpath.stem.endswith("SKIPPED_ANS"):
                sum_field = "SKIPPED ANSWER"
            elif is_nonnumeric:
                sum_field = "NON-NUMERIC SURVEY"
            else:
                this_df.score = pd.to_numeric(this_df.score, errors="coerce")
                sum_field = this_df.score.sum()

            # Add this survey's data to aggregate "dataframe" (list, really)
            # Get subscores if ALSFRS
            if is_nonnumeric:
                agg_list.append(
                    [subject_id, date, time] + this_df.answer.to_list() + [sum_field]
                )
            elif "ALSFRS" in survey_name:
                res = (
                    [subject_id, date, time]
                    + this_df.score.to_list()
                    + [
                        this_df.score[0:3].sum(),
                        this_df.score[3:6].sum(),
                        this_df.score[6:9].sum(),
                        this_df.score[9:12].sum(),
                        sum_field,
                    ]
                )
                # Replace erroring subscores with nan
                agg_list.append(
                    [
                        float("nan") if not isinstance(x, str) and x < 0 else x
                        for x in res
                    ]
                )
            else:
                agg_list.append(
                    [subject_id, date, time] + this_df.score.to_list() + [sum_field]
                )

            # Do not add to final statistics if there is missing/bad data
            if not isinstance(sum_field, str):
                if subject_id in stats.keys():
                    if spath.name in stats[subject_id].keys():
                        stats[subject_id][spath.name].append(this_df.score.sum())
                    else:
                        stats[subject_id][spath.name] = [this_df.score.sum()]
                else:
                    stats[subject_id] = {spath.name: [this_df.score.sum()]}

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
        aggs_dict[survey_name] = pd.DataFrame(agg_list, columns=cols)

    # Extract statistics from lists of sums (that are buried in stats dict)
    subj_ids = []
    surv_names = []
    n = []
    avgs = []
    stds = []
    for s_id, survey_dicts in stats.items():
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
    stats_df = pd.DataFrame(
        {
            "Subject ID": subj_ids,
            "Survey Name": surv_names,
            "n": n,
            "Mean": avgs,
            "STD": stds,
        }
    )

    # Create summary sheet with all survey data
    summary = []
    for name, df in aggs_dict.items():
        new_date = "date_" + name
        new_time = "time_" + name
        sum_df = df.rename(columns={"sum": name, "date": new_date, "time": new_time})
        summary.append(sum_df[["Subject ID", new_date, new_time, name]])
    df_merged = reduce(
        lambda left, right: pd.merge(left, right, on=["Subject ID"], how="outer"),
        summary,
    )

    # Loop through aggregated dataframes and save to separate sheets
    with pd.ExcelWriter(
        Path(out_path).joinpath(out_name + ".xlsx"),
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_numbers": True}},
    ) as writer:
        df_merged.to_excel(writer, sheet_name="Summary", index=False)
        stats_df.to_excel(writer, sheet_name="Stats", index=False)
        for name, df in aggs_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)


def update_survey(data_dir, out_root, key_path, subject_id="", survey_id=""):
    if not subject_id and not survey_id:
        warnings.warn(
            "No subject_id or survey_id specified. Processing and aggregating all data"
        )

    process_survey(
        data_dir, out_root, key_path, subject_id=subject_id, survey_id=survey_id
    )
    aggregate_survey(data_dir, out_root, key_path)


def aggregate_acoustic(data_dir, out_path, out_name="ACOUSTIC_SUMMARY", subject_id=""):
    out_path = Path(out_path)
    out_path.mkdir(exist_ok=True)

    df_list = []
    for file in Path(data_dir).glob("**/*.xlsx"):
        if subject_id and subject_id != file.stem[0 : file.stem.find("_")]:
            continue
        df_list.append(process_spa(file))

    df = pd.concat(df_list, axis=0)

    # Add conditional formatting if there is a flag column
    # Prevents erroring if no analyst added a flag
    if "flag" in df.columns.str.lower():
        # Prep
        writer = pd.ExcelWriter(
            out_path.joinpath(out_name + ".xlsx"), engine="xlsxwriter"
        )
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Convert index of first flag value to excel notation
        excel_col_flag = excel_style(2, df.columns.str.lower().get_loc("flag") + 1)

        # Makes the font color of the whole row red if the "flag" column == "y"
        format1 = workbook.add_format({"font_color": "#FF0000"})
        worksheet.conditional_format(
            1,
            0,
            df.shape[0],
            df.shape[1] - 1,
            {
                "type": "formula",
                "criteria": f'=${excel_col_flag}="y"',
                "format": format1,
            },
        )

        writer.close()
    else:
        df.to_excel(out_path.joinpath(out_name + ".xlsx"), index=False)


def process_gps(data_dir, out_dir, subject_ids):
    gps_stats_main(
        data_dir,
        out_dir,
        "America/New_York",
        Frequency.HOURLY,
        True,
        participant_ids=subject_ids,
    )


def aggregate_gps(data_dir, out_path, out_name="GPS_SUMMARY", subject_id=""):
    out_path = Path(out_path)
    out_path.mkdir(exist_ok=True)

    df_list = []
    for file in Path(data_dir).glob("**/*.csv"):
        this_id = file.stem
        if subject_id and subject_id != this_id:
            continue
        df = pd.read_csv(file)
        is_cont, start_day, end_day = find_n_cont_days(df, n=30)

        if is_cont:
            obs_day_start = day_to_obs_day(df, start_day)
            obs_day_end = day_to_obs_day(df, end_day)
            cont_obs_day_start = date_series_to_str(start_day)
            cont_obs_day_end = date_series_to_str(end_day)
        else:
            obs_day_start = obs_day_end = cont_obs_day_start = cont_obs_day_end = None

        df_avg = (
            df.drop(["year", "month", "day", "hour"], axis=1)
            .mean()
            .to_frame()
            .T.add_suffix("_mean")
        )
        df_avg.insert(0, "subject_id", this_id)
        df_list.append(
            df_avg.assign(
                thirty_days_continuous=is_cont,
                continuous_obs_start_date=cont_obs_day_start,
                continuous_obs_end_date=cont_obs_day_end,
                continuous_obs_start_study_date=obs_day_start,
                continuous_obs_end_study_date=obs_day_end,
            )
        )
    df_out = pd.concat(df_list, axis=0)
    df_out.to_csv(out_path.joinpath(out_name + ".csv"), index=False, header=True)


def combine_summaries(
    out_dir, acoustic_path="", gps_path="", survey_path="", out_name="COMBINED_SUMMARY"
):
    paths = [acoustic_path, gps_path, survey_path]
    if paths.count("") > 2:
        print(
            "Must supply at least two valid paths to summary sheet to create a combined file"
        )
        return

    with pd.ExcelWriter(Path(out_dir).joinpath(out_name + ".xlsx")) as writer:
        for file in paths:
            file = Path(file)
            if file.suffix == ".xlsx":
                this_file = pd.ExcelFile(file)
                sheets = this_file.sheet_names
                for sheet in sheets:
                    this_sheet_name = sheet if len(sheets) > 1 else file.stem.lower()
                    df = this_file.parse(sheet_name=sheet)
                    df.to_excel(writer, sheet_name=f"{this_sheet_name}", index=False)
            else:  # csv
                df = pd.read_csv(file)
                df.to_excel(writer, sheet_name=f"{file.stem.lower()}", index=False)


def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Process Survey
    parser_process_survey = subparsers.add_parser("process_survey")
    parser_process_survey.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_SURVEY
    )
    parser_process_survey.add_argument(
        "-o", "--out_root", type=str, nargs="?", default=OUT_ROOT_SURVEY
    )
    parser_process_survey.add_argument(
        "-k", "--key_path", type=str, nargs="?", default=KEY_PATH
    )
    parser_process_survey.add_argument("--subject_id", type=str, nargs="?", default="")
    parser_process_survey.add_argument("--survey_id", type=str, nargs="?", default="")
    parser_process_survey.set_defaults(func=process_survey)

    # Aggregate Survey
    parser_agg_survey = subparsers.add_parser("aggregate_survey")
    parser_agg_survey.add_argument(
        "-d", "--data_dir", type=str, default=OUT_ROOT_SURVEY
    )
    parser_agg_survey.add_argument(
        "-op", "--out_path", type=str, default=OUT_ROOT_SURVEY
    )
    parser_agg_survey.add_argument("-k", "--key_path", type=str, default=KEY_PATH)
    parser_agg_survey.add_argument(
        "-on", "--out_name", type=str, default="SURVEY_SUMMARY"
    )
    parser_agg_survey.set_defaults(func=aggregate_survey)

    # Update Survey
    parser_update_survey = subparsers.add_parser("update_survey")
    parser_update_survey.add_argument(
        "-d", "--data_dir", type=str, default=DATA_DIR_SURVEY
    )
    parser_update_survey.add_argument(
        "-o", "--out_root", type=str, default=OUT_ROOT_SURVEY
    )
    parser_update_survey.add_argument("-k", "--key_path", type=str, default=KEY_PATH)
    parser_update_survey.add_argument("--subject_id", type=str, default="")
    parser_update_survey.add_argument("--survey_id", type=str, default="")
    parser_update_survey.set_defaults(func=update_survey)

    # Aggregate_acoustic
    parser_agg_ac = subparsers.add_parser("aggregate_acoustic")
    parser_agg_ac.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_ACOUSTIC
    )
    parser_agg_ac.add_argument(
        "-op", "--out_path", type=str, nargs="?", default=OUT_ROOT_ACOUSTIC
    )
    parser_agg_ac.add_argument(
        "-on", "--out_name", type=str, default="ACOUSTIC_SUMMARY"
    )
    parser_agg_ac.add_argument("--subject_id", type=str, nargs="?", default="")
    parser_agg_ac.set_defaults(func=aggregate_acoustic)

    # Process GPS
    parser_process_gps = subparsers.add_parser("process_gps")
    parser_process_gps.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_GPS
    )
    parser_process_gps.add_argument(
        "-o", "--out_dir", type=str, nargs="?", default=OUT_ROOT_GPS
    )
    parser_process_gps.add_argument("--subject_ids", nargs="?", default=None)
    parser_process_gps.set_defaults(func=process_gps)

    # Aggregate GPS
    parser_agg_gps = subparsers.add_parser("aggregate_gps")
    parser_agg_gps.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_GPS
    )
    parser_agg_gps.add_argument(
        "-op", "--out_path", type=str, nargs="?", default=OUT_ROOT_GPS
    )
    parser_agg_gps.add_argument(
        "-on", "--out_name", type=str, nargs="?", default="GPS_SUMMARY"
    )
    parser_agg_gps.add_argument("--subject_id", type=str, nargs="?", default="")
    parser_agg_gps.set_defaults(func=aggregate_gps)

    # Combine summaries
    parser_combine = subparsers.add_parser("combine_summaries")
    parser_combine.add_argument("-o", "--out_dir", type=str)
    parser_combine.add_argument("-ap", "--acoustic_path", type=str, default="")
    parser_combine.add_argument("-gp", "--gps_path", type=str, default="")
    parser_combine.add_argument("-sp", "--survey_path", type=str, default="")
    parser_combine.add_argument(
        "-on", "--out_name", type=str, default="COMBINED_SUMMARY"
    )
    parser_combine.set_defaults(func=combine_summaries)

    # Collect args
    args = parser.parse_args()

    # Print info
    print("Running", args.func.__name__, "with arguments:")
    for arg_name, value in vars(args).items():
        if arg_name != "func":
            print(arg_name, ": ", value, sep="")

    # Call
    call_function_with_args(args.func, args)


########### RUN ###########
if __name__ == "__main__":
    cli()
    print("Complete!")
