import sys
import argparse
import re
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from forest.jasmine.traj2stats import Frequency, gps_stats_main
from forest.sycamore.base import compute_survey_stats
from soccon.gps import find_max_cont_days, date_series_to_str
from soccon.survey import BeiweSurvey


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
    if args.time_end is not None:
        validate_date(args.time_end)

    # Setup: add forest_mano and import functions
    sys.path.append(str(Path(args.beiwe_code_path).joinpath("code", "forest_mano")))
    from data_summaries import read_keyring  # type: ignore
    from helper_functions import download_data  # type: ignore

    # Name output folder
    time_start_label = args.time_start if args.time_start is not None else "first"
    time_end_label = args.time_end if args.time_end is not None else str(date.today())
    date_info = f"from-{time_start_label}_to-{time_end_label}-{datetime.now().time().strftime('%H%M%S')}"
    data_folder = Path(args.out_dir).joinpath(f"data_download_{date_info}")

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
    return any(data_folder.iterdir()), data_folder


def quality_check(data_dir, subject_id, survey_key_path, skip_gps_stats):
    data_dir = Path(data_dir)
    out_dir = data_dir.joinpath(f"{subject_id}_processed")

    survey_key = BeiweSurvey.load_key(survey_key_path)

    # Validate GPS quality,
    if not skip_gps_stats:
        print(f"Running GPS stats for subject {subject_id}")
        gps_stats_main(
            data_dir,
            out_dir,
            "America/New_York",
            Frequency.DAILY,
            False,
            participant_ids=[subject_id],
        )

    gps_summary_df = pd.read_csv(
        out_dir.joinpath("daily", f"{subject_id}.csv"), na_filter=False
    )
    n_cont_days_found, day_start, day_end = find_max_cont_days(gps_summary_df)

    # Count surveys and assess completion
    compute_survey_stats(
        data_dir, out_dir, "America/New_York", include_audio_surveys=False
    )
    survey_submits_path = out_dir.joinpath("summaries", "submits_only.csv")
    survey_df = pd.read_csv(survey_submits_path)
    survey_summary_df = survey_df["survey id"].value_counts().reset_index()

    # Add use name
    survey_summary_df["survey_name"] = [
        survey_key[id]["name"] if id in survey_key.columns else None
        for id in survey_df["survey id"]
    ]

    # Determine if survey was completed or only started
    survey_dir_names = [
        file.name for file in data_dir.joinpath(subject_id, "survey_answers").iterdir()
    ]
    survey_summary_df["completed"] = [
        id in survey_dir_names for id in survey_summary_df["survey id"]
    ]

    for file in out_dir.joinpath("by_survey").iterdir():
        this_id = file.stem
        this_ind = survey_summary_df["survey id"] == this_id
        this_row = survey_summary_df.loc[this_ind]
        df = pd.read_csv(file, na_filter=False)
        if not this_row.empty and not this_row.completed.item():
            survey_summary_df.loc[this_ind, "check_this_file"] = None
            survey_summary_df.loc[this_ind, "count"] = None
        else:
            survey_summary_df.loc[this_ind, "check_this_file"] = (
                "NO_ANSWER_SELECTED" in df.values
            )

    # Move count column to end
    survey_summary_df["count"] = survey_summary_df.pop("count")

    gps_info_df = pd.DataFrame(
        {
            "max number of continuous days found": [n_cont_days_found],
            "day_start": [date_series_to_str(day_start)],
            "day_end": [date_series_to_str(day_end)],
        }
    )

    # Find audio file
    audio_found = any(
        [
            file.suffix == ".wav"
            for file in data_dir.joinpath(subject_id, "audio_recordings").glob("**/*")
        ]
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

    metadata_df = pd.DataFrame(
        {
            "subject_id": [subject_id],
            "data_check_start_date": re.search("from-(.+?)_to-", str(data_dir)).group(
                1
            ),
            "data_check_end_date": str(data_dir)[
                str(data_dir).find("to-") + len("to-") :
            ],
        }
    )

    with pd.ExcelWriter(
        data_dir.joinpath(f"beiwe_data_check_{subject_id}.xlsx")
    ) as writer:
        survey_summary_df.to_excel(
            writer, sheet_name="survey", index=False, header=True
        )
        gps_info_df.to_excel(writer, sheet_name="gps", index=False, header=True)
        audio_df.to_excel(writer, sheet_name="audio", index=False, header=True)
        metadata_df.to_excel(writer, sheet_name="metadata", index=False, header=True)

    print(f"Quality check complete for subject {subject_id}")


def download_and_check(args):
    dl_success, data_dir = download_beiwe_data(args)

    if not dl_success:
        print("Data download failed. Skipping quality check")
        return
    else:
        for id in args.beiwe_ids:
            quality_check(data_dir, id, args.survey_key_path, args.skip_gps_stats)


######### CLI #########
# Build parsers with shared argument
def get_shared_args_qc_and_dl():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--survey_key_path", type=str, required=True)
    parser.add_argument("--skip_gps_stats", action="store_true")
    return parser


def get_shared_args_dl_funcs():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--keyring_path", type=str, required=True)
    parser.add_argument("--keyring_pw", type=str, required=True)
    parser.add_argument("--study_id", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--beiwe_ids", nargs="+", required=True)
    parser.add_argument("--beiwe_code_path", type=str, required=True)
    parser.add_argument("--time_start", type=str, nargs="?", default=None)
    parser.add_argument("--time_end", type=str, nargs="?", default=None)
    parser.add_argument(
        "--data_streams",
        nargs="*",
        default=["gps", "survey_timings", "survey_answers", "audio_recordings"],
    )
    return parser


# CLI wrappers
def quality_check_cli():
    parent_parser = get_shared_args_qc_and_dl()
    parser = argparse.ArgumentParser("quality_check", parents=[parent_parser])
    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--subject_id", type=str, required=True)
    args = parser.parse_args()
    quality_check(
        args.data_dir,
        args.subject_id,
        args.survey_key_path,
        args.skip_gps_stats,
    )


def download_data_cli():
    parent_parser = get_shared_args_dl_funcs()
    parser = argparse.ArgumentParser("download_beiwe_data", parents=[parent_parser])
    args = parser.parse_args()
    download_beiwe_data(args)


def download_and_check_cli():
    parent_parser_dl = get_shared_args_dl_funcs()
    parent_parser_check = get_shared_args_qc_and_dl()
    parser = argparse.ArgumentParser(
        "download_and_check", parents=[parent_parser_dl, parent_parser_check]
    )
    args = parser.parse_args()
    download_and_check(args)
