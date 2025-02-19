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


def download_beiwe_data(args):
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


def _quality_check(data_dir, subject_id, n_days_gps):
    out_dir = Path(data_dir).joinpath("processed")

    # Validate GPS quality,
    gps_stats_main(
        data_dir,
        out_dir,
        "America/New_York",
        Frequency.DAILY,
        False,
    )

    gps_summary_df = pd.read_csv(
        out_dir.joinpath("daily", f"{subject_id}.csv"), na_filter=False
    )
    n_cont_days_found, day_start, day_end = find_n_cont_days(
        gps_summary_df, n=n_days_gps
    )

    # Count surveys and assess completion
    compute_survey_stats(data_dir, out_dir, "America/New_York")
    survey_submits_path = out_dir.joinpath("summaries", "submits_only.csv")
    survey_df = pd.read_csv(survey_submits_path)
    survey_summary_df = survey_df["survey id"].value_counts().reset_index()
    survey_summary_df = survey_summary_df.assign(flag=[False] * len(survey_summary_df))

    audio_found = False
    for file in out_dir.joinpath("by_survey").iterdir():
        df = pd.read_csv(file, na_filter=False)
        if "audio recording" in df.values:
            audio_found = True
            continue
        if "NO_ANSWER_SELECTED" in df.values:
            survey_summary_df.loc[
                survey_summary_df["survey id"] == file.stem, "flag"
            ] = True

    # Build output dfs if necessary
    if n_cont_days_found:
        gps_info_df = pd.concat(
            [day_start.rename("day_start"), day_end.rename("day_end")], axis=1
        )
    else:
        gps_info_df = pd.DataFrame(
            {
                "number of continuous days searched for": n_days_gps,
                f"{n_days_gps} found": n_cont_days_found,
            }
        )

    audio_df = pd.DataFrame(
        {
            "audio_file_found": [audio_found],
            "max_freq": [None],
            "clipping_present": [None],
            "background_db": [None],
            "speech_db": [None],
            "background_speech_diff": [None],
        }
    )

    with pd.ExcelWriter(
        out_dir.joinpath(f"survey_check_summary_{subject_id}.xlsx")
    ) as writer:
        survey_summary_df.to_excel(
            writer, sheet_name="survey", index=False, header=True
        )
        gps_info_df.to_excel(writer, sheet_name="gps", index=False, header=True)
        audio_df.to_excel(writer, sheet_name="audio", index=False, header=True)


def download_and_check(args):
    dl_success, data_dir = download_beiwe_data(args)

    if not dl_success:
        print("Data download failed. Skipping quality check")
        return
    else:
        for id in args.beiwe_ids:
            _quality_check(data_dir, id, args.n_days_gps)


# CLI wrapper
def quality_check_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--subject_id", type=str, required=True)
    parser.add_argument("--n_days_gps", required=False)
    args = parser.parse_args()
    _quality_check(
        args.data_dir,
        args.subject_id,
        args.n_days_gps,
    )


def download_funcs_cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--keyring_path", type=str, required=True)
    parent_parser.add_argument("--keyring_pw", type=str, required=True)
    parent_parser.add_argument("--study_id", type=str, required=True)
    parent_parser.add_argument("--out_dir", type=str, required=True)
    parent_parser.add_argument("--beiwe_ids", nargs="+", required=True)
    parent_parser.add_argument("--time_start", type=str, nargs="?", default=None)
    parent_parser.add_argument("--time_end", type=str, nargs="?", default=None)
    parent_parser.add_argument(
        "--data_streams",
        nargs="*",
        default=["gps", "survey_timings", "survey_answers", "audio_recordings"],
    )
    parent_parser.add_argument(
        "--beiwe_code_path", type=str, default="C:/Users/NB254/Desktop/SaSI Lab/beiwe"
    )

    parser_get_data = subparsers.add_parser(
        "download_beiwe_data", parents=[parent_parser]
    )
    parser_get_data.set_defaults(func=download_beiwe_data)

    parser_dl_check = subparsers.add_parser(
        "download_and_check", parents=[parent_parser]
    )
    parser_dl_check.add_argument("--n_days_gps", required=False, default=10)
    parser_dl_check.set_defaults(func=download_and_check)

    args = parser.parse_args()
    args.func(args)
