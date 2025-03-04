import sys
import argparse
import re
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from forest.jasmine.traj2stats import Frequency, gps_stats_main
from soccon.gps import find_max_cont_days, date_series_to_str
from soccon.utils import disp_run_info
from soccon.survey import BeiweSurvey


def validate_date(d):
    try:
        date.fromisoformat(d)
    except ValueError:
        raise ValueError(
            f"{d} is an invalid date format. Date must be formatted YYYY-MM-DD"
        )


def download_beiwe_data(args):
    """Downloads data from Beiwe server into specified directory

    Args:
        args (argparse.Namespace): Args. See download_data_cli for details.

    Returns:
        bool: True if data has been downloaded, false if not
        Path: Path to folder into which data has been downloaded
    """
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
    """Runs a quality check on the data in `data_dir` on `subject_id`
    and outputs the results to `data_dir/subject_id_processed/`

    Args:
        data_dir (str): Path to data directory
        subject_id (str): Beiwe subject ID
        survey_key_path (str): Path to survey key which is used to apply use names to survey ids
        skip_gps_stats (bool): Flag to skip processing GPS data
    """
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

    gps_summary_df = pd.read_csv(out_dir.joinpath("daily", f"{subject_id}.csv"))
    n_cont_days_found, day_start, day_end = find_max_cont_days(gps_summary_df)

    # Count surveys and assess completion
    survey_ids = []
    survey_dates = []
    survey_times = []
    survey_flags = []
    survey_names = []
    for item in data_dir.joinpath(subject_id, "survey_answers").glob("*/*"):
        df = pd.read_csv(item)
        file = item.stem
        survey_id = item.parent.name
        sp_ind = file.find(" ")

        survey_ids.append(survey_id)
        survey_dates.append(file[0:sp_ind])
        survey_times.append(file[sp_ind + 1 : file.find("+")])
        survey_flags.append("NO_ANSWER_SELECTED" in df.values)
        survey_names.append(
            survey_key[survey_id]["name"] if survey_id in survey_key.columns else None
        )

    survey_summary_df = pd.DataFrame(
        {
            "survey_id": survey_ids,
            "survey_name": survey_names,
            "date": survey_dates,
            "time": survey_times,
            "check_this_file": survey_flags,
        }
    )

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
    """Runs download_beiwe_data and quality_check for all subject ids provided"""
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
    parser.set_defaults(func=quality_check)
    args = parser.parse_args()
    disp_run_info(args)
    args.func(
        args.data_dir,
        args.subject_id,
        args.survey_key_path,
        args.skip_gps_stats,
    )


def download_data_cli():
    parent_parser = get_shared_args_dl_funcs()
    parser = argparse.ArgumentParser("download_beiwe_data", parents=[parent_parser])
    parser.set_defaults(func=download_beiwe_data)
    args = parser.parse_args()
    disp_run_info(args)
    args.func(args)


def download_and_check_cli():
    parent_parser_dl = get_shared_args_dl_funcs()
    parent_parser_check = get_shared_args_qc_and_dl()
    parser = argparse.ArgumentParser(
        "download_and_check", parents=[parent_parser_dl, parent_parser_check]
    )
    parser.set_defaults(func=download_and_check)
    args = parser.parse_args()
    disp_run_info(args)
    args.func(args)
