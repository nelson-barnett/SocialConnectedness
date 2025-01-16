import pandas as pd
import warnings
import argparse
import zipfile

from pathlib import Path
from datetime import datetime
from forest.jasmine.traj2stats import Frequency, gps_stats_main, Hyperparameters

from survey import BeiweSurvey, RedcapSurvey, aggregate_beiwe, aggregate_redcap
from utils import call_function_with_args, excel_style
from acoustic import process_spa
from gps import find_n_cont_days, day_to_obs_day, date_series_to_str

DATA_DIR_SURVEY = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_data"
)
OUT_ROOT_SURVEY = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_results"
)

DATA_DIR_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_data"
OUT_ROOT_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_results"

DATA_DIR_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data/spa_outputs"
OUT_ROOT_ACOUSTIC = (
    "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data"
)

KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"


def process_survey(
    data_dir,
    out_dir,
    key_path,
    subject_id="",
    survey_id="",
    skip_dirs=[],
    use_zips=False,
):
    """Create a cleaned and scored copy of all survey CSVs in `data_dir`
    saved in `out_dir` by survey ID

    Args:
        data_dir (str): Path to root directory where data is stored
        out_dir (str): Path to directory in which data will be saved
        key_path (str): Path to CSV key containing survey scoring rules
        subject_id (str, optional): Individual subject ID to process. Defaults to "".
        survey_id (str, optional): Individual survey ID to process. Defaults to "".
        skip_dirs (list, optional): List of directories names to skip when looking for data. Does not need to be full path, only dir name. Defaults to [].
        use_zips (bool, optional): Flag to process CSVs in zip files within `data_dir`. Defaults to False.
    """
    # Setup
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    extensions = (
        {".csv", ".zip"} if use_zips else {".csv"}
    )  # zip file control is done here
    # Exclude the to-be-created dir to be safe (user may be intending to overwrite without deleting the folder first)
    skip_dirs += [out_dir.stem]

    ###### Inner funcs
    def process_beiwe(file):
        # Don't error if this survey isn't in key. Print message and move on
        key_df = BeiweSurvey.load_key(key_path, "Beiwe")
        try:
            this_key = key_df[file.parent.name]
        except KeyError:
            print(f"Survey ID '{file.parent.name}' not found in key. Skipping...")
            return

        # Standard file structure for Beiwe downloads
        this_subj_id = file.parent.parent.parent.name

        # TODO: Allow for multiple subjects, surveys to be specified
        if subject_id and (this_subj_id != subject_id or file.parent.name != survey_id):
            return

        # Make out dir in specified path + survey id
        this_out_dir = out_dir.joinpath(file.parent.name)
        this_out_dir.mkdir(exist_ok=True, parents=True)

        # Generate survey object
        this_survey = (
            BeiweSurvey(
                file=file,
                key=this_key,
                subject_id=this_subj_id,
                file_df=zf.open(name),
            )  # zip file requires special handling
            if item.suffix == ".zip"
            else BeiweSurvey(file=file, key=this_key, subject_id=this_subj_id)
        )

        # If there is no scoring to be done, just clean and save survey
        if this_key["index"] is None and this_key["invert"] is None:
            this_survey.clean(minimal=True)
        else:
            this_survey.parse_and_score()
        this_survey.export(this_out_dir)

    def process_redcap(file):
        # Don't error if this survey isn't in key. Print message and move on
        this_key = RedcapSurvey.load_key(key_path, file.stem)

        # Make out dir in specified path + survey id
        this_out_dir = out_dir.joinpath(file.stem)
        this_out_dir.mkdir(exist_ok=True, parents=True)

        # Generate survey object
        this_survey = (
            RedcapSurvey(
                file=file,
                key=this_key,
                file_df=zf.open(name),
            )  # zip file requires special handling
            if item.suffix == ".zip"
            else RedcapSurvey(file=file, key=this_key)
        )

        # If there is no scoring to be done, just clean and save survey
        this_survey.process()
        this_survey.export(this_out_dir)

    ###### Main func -- Iterate recursively through everything in data_dir
    for item in Path(data_dir).glob("**/*"):
        # Check that this item is not meant to be skipped and that it the file extension is intended
        if set(item.parts) & set(skip_dirs) or item.suffix not in extensions:
            continue

        # Zip needs secondary loop. It is treated as a top-level dir
        if item.suffix == ".zip":
            zf = zipfile.ZipFile(item)
            # Go through every file (name) in zip file
            for name in zf.namelist():
                # Skips "__MACOS" folders and non-csv files
                if name.startswith("__") or not name.endswith(".csv"):
                    continue
                elif "redcap" in Path(name).parent.stem.lower():
                    process_redcap(Path(name))
                else:
                    process_beiwe(Path(name))
        elif item.suffix == ".csv":
            if "redcap" in item.parent.stem.lower():
                process_redcap(item)
            else:
                process_beiwe(item)


def aggregate_survey(data_dir, out_dir, key_path, out_name="SURVEY_SUMMARY"):
    beiwe_summary, beiwe_stats, beiwe_agg_dict = aggregate_beiwe(data_dir, key_path)
    redcap_agg_dict = aggregate_redcap(data_dir, key_path)

    # Combine
    agg_dict = redcap_agg_dict | beiwe_agg_dict

    # Write
    with pd.ExcelWriter(
        Path(out_dir).joinpath(out_name + ".xlsx"),
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_numbers": True}},
    ) as writer:
        beiwe_summary.to_excel(writer, sheet_name="Beiwe Summary", index=False)
        beiwe_stats.to_excel(writer, sheet_name="Beiwe Stats", index=False)
        for name, df in agg_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)


def update_survey(data_dir, out_dir, key_path, subject_id="", survey_id=""):
    """Updates all survey analysis. Packages process and aggregate into one function.

    Args:
        data_dir (str): Path to directory in which data exists.
        out_dir (str): Path to directory into which outputs will be saved
        key_path (str): Path to CSV key containing survey scoring rules
        subject_id (str, optional): ID of subject whose data should be processed. Defaults to "".
        survey_id (str, optional): ID of survey to process. Defaults to "".
    """
    if not subject_id and not survey_id:
        warnings.warn(
            "No subject_id or survey_id specified. Processing and aggregating all data"
        )

    process_survey(
        data_dir, out_dir, key_path, subject_id=subject_id, survey_id=survey_id
    )
    aggregate_survey(out_dir, out_dir, key_path)


def aggregate_acoustic(data_dir, out_dir, out_name="ACOUSTIC_SUMMARY", subject_id=""):
    """Collects acoustic data in `data_dir`
    (processed externally in SPA) into a summary sheet in `out_dir`.

    Args:
        data_dir (str): Path to directory in which data is stored.
        out_dir (str): Path to directory into which summary will be saved
        out_name (str, optional): Name of the summary file. Defaults to "ACOUSTIC_SUMMARY".
        subject_id (str, optional): Subject whose data should be analyzed. Defaults to "".
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

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
            out_dir.joinpath(out_name + ".xlsx"), engine="xlsxwriter"
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
        df.to_excel(out_dir.joinpath(out_name + ".xlsx"), index=False)


def process_gps(data_dir, out_dir, subject_ids=None, quality_thresh=0.05):
    """Runs Forest.Jasmine's GPS analysis with some user interaction and
    additional helpful info printed

    Args:
        data_dir (str): _description_
        out_dir (str): _description_
        subject_ids (Union[list, None], optional): List of subject ids to use. If None, all ids in `data_dir` are used. Defaults to None.
        quality_thresh (float, optional): Data quality threshold. Defaults to 0.05.
    """
    # Get already existing data
    out_dir_jasmine = Path(out_dir).joinpath("hourly")
    init_update_times = (
        {p.stem: p.stat().st_ctime for p in out_dir_jasmine.iterdir()}
        if out_dir_jasmine.exists()
        else []
    )

    # Get ids of all subjects in data dir (assumes data_dir exists)
    data_dir_ids = [d.stem for d in Path(data_dir).iterdir() if d.is_dir()]

    # Intersection of already processed ids and those passed
    # If subject_ids is None, we're doing all the data anyway so the intersection doesn't matter
    processed_and_passed_intersect = (
        list(set(subject_ids) & set(init_update_times.keys()))
        if subject_ids is not None
        else []
    )

    # Provide useful information to the user
    if init_update_times and (subject_ids is None or processed_and_passed_intersect):
        print(f"The following processed data already exists in {out_dir_jasmine}:")
        for id in processed_and_passed_intersect:
            print(
                f"id: {id}, last updated: {datetime.fromtimestamp(init_update_times[id]).strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if subject_ids is None:
            cont = input(
                f"Would you like to continue with processing all data in {data_dir}: {data_dir_ids}? (y/n): "
            )
        else:
            cont = input(
                f"Would you like to continue with processing data for subjects {subject_ids}? (y/n): "
            )

    if cont == "n":
        print("User requested stop")
        return

    # Process data
    gps_stats_main(
        data_dir,
        out_dir,
        "America/New_York",
        Frequency.HOURLY,
        True,
        participant_ids=subject_ids,
        parameters=Hyperparameters(quality_threshold=quality_thresh),
    )

    final_update_times = (
        {p.stem: p.stat().st_ctime for p in out_dir_jasmine.iterdir()}
        if out_dir_jasmine.exists()
        else []
    )

    # Subject IDs that exist in data_dir but not in out_dir_jasmine
    # If specific ids were passed, only report those if they were in skipped
    skipped_subjects = list(set(data_dir_ids).difference(final_update_times.keys()))
    skipped_subjects = (
        list(set(skipped_subjects) & set(subject_ids))
        if subject_ids is not None
        else skipped_subjects
    )

    # If any data was processed
    if final_update_times:
        # Describe the data that now exists
        for id, time in final_update_times.items():
            if id in init_update_times.keys() and init_update_times[id] != time:
                print(
                    f"Data for subject {id} has been processed. Previously processed data existed and has been overwritten/updated."
                )
            else:
                print(f"Data for subject {id} has been processed.")
    else:
        print(f"No data was processed. Make sure there are data in {data_dir}")

    # Print all subject ids that were skipped
    if skipped_subjects:
        print("The following subjects were not processed:")
        for id in skipped_subjects:
            print(id)
        print(
            f"The current quality threshold is: {quality_thresh} consider passing a lower `quality_thresh` value and retrying."
        )


def aggregate_gps(data_dir, out_dir, out_name="GPS_SUMMARY"):
    """Collects data from `process_gps` in `data_dir` into a summary sheet in `out_dir`.

    Args:
        data_dir (str): Path to directory in which data exists
        out_dir (str): Path to directory into which summary will be saved
        out_name (str, optional): Name of the summary file. Defaults to "GPS_SUMMARY".
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    df_list = []
    for file in Path(data_dir).glob("**/*.csv"):
        this_id = file.stem
        df = pd.read_csv(file)
        is_cont, start_day, end_day = find_n_cont_days(df, n=30)

        if is_cont:
            # Get day number and real date of continuous period
            obs_day_start_num = day_to_obs_day(df, start_day)
            obs_day_end_num = day_to_obs_day(df, end_day)
            obs_day_start_str = date_series_to_str(start_day)
            obs_day_end_str = date_series_to_str(end_day)

            # Get indices of beginning and end datapoints of thirty day period
            df_start_ind = df.index[
                (df[["year", "month", "day"]] == start_day).all(axis=1)
            ].min()
            df_end_ind = df.index[
                (df[["year", "month", "day"]] == end_day).all(axis=1)
            ].max()

            # Get average for only the thirty day period, convert back to DF, rename columns
            df_avg = (
                df.drop(["year", "month", "day", "hour"], axis=1)
                .iloc[df_start_ind:df_end_ind, :]
                .mean()
                .to_frame()
                .T.add_suffix("_mean")
            )
        else:
            obs_day_start_num = obs_day_end_num = obs_day_start_str = (
                obs_day_end_str
            ) = None
            df_avg = pd.DataFrame()

        # Add subject_id column and continuous period info and append to list
        df_avg.insert(0, "subject_id", [this_id])
        df_list.append(
            df_avg.assign(
                thirty_days_continuous=is_cont,
                continuous_obs_start_date=obs_day_start_str,
                continuous_obs_end_date=obs_day_end_str,
                continuous_obs_start_study_date=obs_day_start_num,
                continuous_obs_end_study_date=obs_day_end_num,
            )
        )

    # Combine all dfs and export
    df_out = pd.concat(df_list, axis=0)
    df_out.to_csv(out_dir.joinpath(out_name + ".csv"), index=False, header=True)


def combine_summaries(
    out_dir, acoustic_path="", gps_path="", survey_path="", out_name="COMBINED_SUMMARY"
):
    """Combines summary sheets into single sheet

    Args:
        out_dir (str): Directory into which document will be saved
        acoustic_path (str, optional): Path to acoustic summary file. Defaults to "".
        gps_path (str, optional): Path to gps summary file. Defaults to "".
        survey_path (str, optional): Path to survey summary file. Defaults to "".
        out_name (str, optional): Name of output file. Defaults to "COMBINED_SUMMARY".
    """
    paths = [acoustic_path, gps_path, survey_path]
    if paths.count("") > 2:
        print(
            "Must supply at least two valid paths to summary sheet to create a combined file"
        )
        return

    with pd.ExcelWriter(Path(out_dir).joinpath(out_name + ".xlsx")) as writer:
        for file in paths:
            file = Path(file)  # If file == "", neither condition will be true
            if file.suffix == ".xlsx":
                this_file = pd.ExcelFile(file)
                sheets = this_file.sheet_names
                for sheet in sheets:
                    this_sheet_name = sheet if len(sheets) > 1 else file.stem.lower()
                    df = this_file.parse(sheet_name=sheet)
                    df.to_excel(writer, sheet_name=f"{this_sheet_name}", index=False)
            elif file.suffix == ".csv":
                df = pd.read_csv(file)
                df.to_excel(writer, sheet_name=f"{file.stem.lower()}", index=False)


def cli():
    """Sets up and runs argparser.
    Takes in command line arguments and dispatches to correct function.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Process Survey
    parser_process_survey = subparsers.add_parser("process_survey")
    parser_process_survey.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_SURVEY
    )
    parser_process_survey.add_argument(
        "-o", "--out_dir", type=str, nargs="?", default=OUT_ROOT_SURVEY
    )
    parser_process_survey.add_argument(
        "-k", "--key_path", type=str, nargs="?", default=KEY_PATH
    )
    parser_process_survey.add_argument("--subject_id", type=str, nargs="?", default="")
    parser_process_survey.add_argument("--survey_id", type=str, nargs="?", default="")
    parser_process_survey.add_argument("--skip_dirs", nargs="*", default=[])
    parser_process_survey.add_argument("--use_zips", type=bool, default=False)
    parser_process_survey.set_defaults(func=process_survey)

    # Aggregate Survey
    parser_agg_survey = subparsers.add_parser("aggregate_survey")
    parser_agg_survey.add_argument(
        "-d", "--data_dir", type=str, default=OUT_ROOT_SURVEY
    )
    parser_agg_survey.add_argument(
        "-od", "--out_dir", type=str, default=OUT_ROOT_SURVEY
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
        "-o", "--out_dir", type=str, default=OUT_ROOT_SURVEY
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
        "-od", "--out_dir", type=str, nargs="?", default=OUT_ROOT_ACOUSTIC
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
    parser_process_gps.add_argument(
        "--subject_ids", nargs="*", default=None, const=None
    )
    parser_process_gps.set_defaults(func=process_gps)

    # Aggregate GPS
    parser_agg_gps = subparsers.add_parser("aggregate_gps")
    parser_agg_gps.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR_GPS
    )
    parser_agg_gps.add_argument(
        "-od", "--out_dir", type=str, nargs="?", default=OUT_ROOT_GPS
    )
    parser_agg_gps.add_argument(
        "-on", "--out_name", type=str, nargs="?", default="GPS_SUMMARY"
    )
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
