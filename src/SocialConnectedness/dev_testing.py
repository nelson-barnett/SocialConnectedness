# Place to write short scripts for development purposes
from pathlib import Path
from SocialConnectedness.survey import Survey
from SocialConnectedness.utils import load_key, call_function_with_args
import zipfile
import argparse

OUT_ROOT_SURVEY = (
    "L:/Research Project Current/Respiratory_Acoustic/Nelson Barnett/Analyze FRS/testing"
)
KEY_PATH = "L:/Research Project Current/Respiratory_Acoustic/Nelson Barnett/survey_key.csv"


def process_single_survey(file, out_dir, key_path, zip_path="", export=False):
    """processes a single survey file

    Args:
        file (_type_): _description_
        out_dir (_type_): _description_
        key_path (_type_): _description_
        export (bool, optional): flag to export the scored survey. Defaults to False.
    """
    # Setup
    if zip_path:
        zf = zipfile.ZipFile(zip_path)
    
    file = Path(file)
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    key_df = load_key(key_path)

    # Don't error if this survey isn't in key. Print message and move on
    try:
        this_key = key_df[file.parent.name]
    except KeyError:
        print(f"Survey ID '{file.parent.name}' not found in key. Skipping...")
        return

    # Standard file structure for Beiwe downloads
    this_subj_id = file.parent.parent.parent.name

    # Make out dir in specified path + survey id
    this_out_dir = out_dir.joinpath(file.parent.name)
    this_out_dir.mkdir(exist_ok=True, parents=True)

    # Generate survey object
    this_survey = (
        Survey(
            file=file,
            key=this_key,
            subject_id=this_subj_id,
            file_df=zf.open(str(file.relative_to(zip_path)).replace("\\","/")),
        )  # zip file requires special handling
        if zip_path
        else Survey(file=file, key=this_key, subject_id=this_subj_id)
    )

    # If there is no scoring to be done, just clean and save survey
    if this_key["index"] is None and this_key["invert"] is None:
        this_survey.clean(minimal=True)
    else:
        this_survey.parse_and_score()

    if export:
        this_survey.export(this_out_dir)
        
        
def cli_dev():
    """Sets up and runs argparser.
    Takes in command line arguments and dispatches to correct function.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Process Survey
    parser_process_single_survey = subparsers.add_parser("process_single_survey")
    parser_process_single_survey.add_argument("-f", "--file", type=str)
    parser_process_single_survey.add_argument(
        "-o", "--out_dir", type=str, nargs="?", default=OUT_ROOT_SURVEY
    )
    parser_process_single_survey.add_argument(
        "-k", "--key_path", type=str, nargs="?", default=KEY_PATH
    )
    parser_process_single_survey.add_argument("--zip_path", type=str, default="")
    parser_process_single_survey.add_argument("--export", type=bool, default=False)
    parser_process_single_survey.set_defaults(func=process_single_survey)

    # Collect args
    args = parser.parse_args()

    # Print info
    print("Running", args.func.__name__, "with arguments:")
    for arg_name, value in vars(args).items():
        if arg_name != "func":
            print(arg_name, ": ", value, sep="")

    # Call
    call_function_with_args(args.func, args)


if __name__ == "__main__":
    cli_dev()
    print("Complete!")
