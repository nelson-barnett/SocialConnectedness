import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import date
from forest.jasmine.traj2stats import Frequency, gps_stats_main
from forest.sycamore.base import compute_survey_stats
from soccon.gps import find_n_cont_days


def validate_date(d):
    try:
        date.fromisoformat(d)
    except ValueError:
        raise ValueError(
            f"{d} is an invalid date format. Date must be formatted YYYY-MM-DD"
        )


def get_beiwe_data(args):
    # Validate dates
    if args.time_start is not None:
        validate_date(args.time_start)
    if args.stime_end is not None:
        validate_date(args.time_end)

    # Setup: add forest_mano and import functions
    sys.path.append(str(Path(args.beiwe_code_path).joinpath("code", "forest_mano")))
    from data_summaries import read_keyring  # type: ignore
    from helper_functions import download_data  # type: ignore

    # Name output folder
    time_start_label = args.time_start if args.time_start is not None else "first"
    time_end_label = args.time_end if args.time_end is not None else str(date.today())
    date_info = "_start-" + time_start_label + "_end-" + time_end_label
    data_folder = Path(args.out_dir).joinpath("data_download" + date_info)

    # Get data
    kr = read_keyring(args.keyring_path, args.keyring_pw)

    if args.time_start is None:
        download_data(
            kr,
            args.study_id,
            data_folder,
            args.beiwe_ids,
            time_end=args.time_end,
            data_streams=args.data_streams,
        )
    else:
        download_data(
            kr,
            args.study_id,
            data_folder,
            args.beiwe_ids,
            args.time_start,
            args.time_end,
            args.data_streams,
        )

    # Returns T/F if data was downloaded, the download path
    return not any(data_folder.iterdir()), data_folder


def quality_check(data_dir, subject_id):
    out_dir = Path(data_dir).joinpath("processed")

    # Validate GPS quality,
    gps_stats_main(
        data_dir,
        out_dir,
        "America/New_York",
        Frequency.DAILY,
        False,
    )
    
    gps_summary_df = pd.read_csv(out_dir.joinpath("daily",subject_id), na_filter=False)
    found_10_cont_days = find_n_cont_days(gps_summary_df, n=10)

    # Count surveys and assess completion
    compute_survey_stats(data_dir, out_dir, "America/New_York")
    survey_submits_path = out_dir.joinpath("summaries", "submits_only.csv")
    survey_df = pd.read_csv(survey_submits_path)
    summary_df = survey_df["survey id"].value_counts().reset_index()
    summary_df = summary_df.assign(flag=[False] * len(summary_df))

    for file in out_dir.joinpath("by_survey").iterdir():
        df = pd.read_csv(file, na_filter=False)
        if "audio recording" in df.values:
            continue
        if "NO_ANSWER_SELECTED" in df.values:
            summary_df.loc[summary_df["survey id"] == file.stem, "flag"] = True

    summary_df.to_csv(
        out_dir.joinpath(f"survey_check_summary_{subject_id}.csv"), index=False, header=True
    )


def download_and_check(args):
    dl_success, data_dir = get_beiwe_data(args)

    if not dl_success:
        print("Data download failed. Skipping quality check")
        return
    else:
        for id in args.beiwe_ids:
            quality_check(data_dir, id)


# TODO: Change this to only call either download_and_check or download via subparser
# and add new func to call quality check. Add access points in pyproject.toml
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    parser_get_data = subparsers.add_parser("get_beiwe_data")
    parser_get_data.add_argument("--keyring_path", type=str, required=True)
    parser_get_data.add_argument("--keyring_pw", type=str, required=True)
    parser_get_data.add_argument("--study_id", type=str, required=True)
    parser_get_data.add_argument("--out_dir", type=str, required=True)
    parser_get_data.add_argument("--beiwe_ids", nargs="+", required=True)
    parser_get_data.add_argument("--time_start", type=str, nargs="?", default=None)
    parser_get_data.add_argument("--time_end", type=str, nargs="?", default=None)
    parser_get_data.add_argument(
        "--data_streams",
        nargs="*",
        default=["gps", "survey_timings", "survey_answers", "audio_recordings"],
    )
    parser_get_data.add_argument(
        "--beiwe_code_path", type=str, default="C:/Users/NB254/Desktop/SaSI Lab/beiwe"
    )
    parser_get_data.set_defaults(func=get_beiwe_data)

    # parser_qual_check = subparsers.add_parser("quality_check")
    # parser_qual_check.add_argument("data_dir", required=True)
    # parser_qual_check.add_argument("subject_id", required=True)
    # parser_qual_check.set_defaults(func=quality_check)

    args = parser.parse_args()
    args.func(args)
