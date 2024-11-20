from parsing import parse, load_key
from pathlib import Path
import statistics
import pandas as pd
import warnings
import inspect
import argparse

DATA_DIR = "L:/Research Project Current/Social Connectedness/Nelson/dev"
OUT_ROOT = "L:/Research Project Current/Social Connectedness/Nelson/dev/results"
KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"


def process(data_dir, out_root, key_path, subject_id="", survey_id=""):
    # def process(args):
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

    survey_key = load_key(key_path)
    for file in Path(data_dir).glob("[!results]**/**/*.csv"):
        try:
            this_key = survey_key[file.parent.name]
        except KeyError:
            raise Exception("Survey ID not found in key.")

        this_subj_id = file.parent.parent.parent.name

        if (
            (this_key["index"] is None and this_key["invert"] is None)
            or (subject_id and this_subj_id != subject_id)
            or (survey_id and file.parent.name != survey_id)
        ):
            continue

        out_dir = out_root.joinpath(file.parent.name)
        out_dir.mkdir(exist_ok=True, parents=True)
        parse(file, out_dir, this_key, this_subj_id)


def aggregate(results_dir, key_path):
    """Take all processed data and create a summary sheet saved to `results_dir`.

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

            # Parse datetime
            # dt = file[us_ind + 1 : file.find("+")]
            # datetime.strptime(dt, "%Y-%m-%d %H_%M_%S")
            
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
                res = (
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
                # Replace erroring subscores with nan
                agg_df.append(
                    [
                        float("nan") if not isinstance(x, str) and x < 0 else x
                        for x in res
                    ]
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


def update(data_dir, out_root, key_path, subject_id="", survey_id=""):
    if not subject_id and not survey_id:
        warnings.warn("No subject_id or survey_id specified. Processing and aggregating all data")

    process(data_dir, out_root, key_path, subject_id=subject_id, survey_id=survey_id)
    aggregate(out_root, key_path)


def call_function_with_args(func, args):
    """
    Call the function with the arguments extracted from the argparse.Namespace object.
    FROM: https://gist.github.com/amarao/36327a6f77b86b90c2bca72ba03c9d3a

    Args:
        func: The function to call.
        args: The argparse.Namespace object containing the arguments.

    Returns:
        Any: The result of the function call.

    Author:
        Laurent DECLERCQ, AGON PARTNERS INNOVATION <l.declercq@konzeptplus.ch>
    """
    # Let's inspect the signature of the function so that we can call it with the correct arguments.
    # We make use of the inspect module to get the function signature.
    signature = inspect.signature(func)

    # Get the parameters of the function using a dictionary comprehension.
    # Note: Could be enhanced to handle edge cases (default values, *args, **kwargs, etc.)
    args = {parameter: getattr(args, parameter) for parameter in signature.parameters}

    # Type cast the arguments to the correct type according to the function signature. We use the annotation of the
    # parameter to cast the argument. If the annotation is empty, we keep the argument as is. We only process the
    # arguments that are in the function signature.
    args = {
        parameter: (
            signature.parameters[parameter].annotation(args[parameter])
            if signature.parameters[parameter].annotation is not inspect.Parameter.empty
            else args[parameter]
        )
        for parameter in args
        if parameter in signature.parameters
    }

    # Call the function with the arguments and return the result if any.
    return func(**args)

def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Process
    parser_process = subparsers.add_parser("process")
    parser_process.add_argument(
        "-d", "--data_dir", type=str, nargs="?", default=DATA_DIR
    )
    parser_process.add_argument(
        "-o", "--out_root", type=str, nargs="?", default=OUT_ROOT
    )
    parser_process.add_argument(
        "-k", "--key_path", type=str, nargs="?", default=KEY_PATH
    )
    parser_process.add_argument("--subject_id", type=str, nargs="?", default="")
    parser_process.add_argument("--survey_id", type=str, nargs="?", default="")
    parser_process.set_defaults(func=process)

    # Aggregate
    parser_agg = subparsers.add_parser("aggregate")
    parser_agg.add_argument("-d", "--results_dir", type=str, default=OUT_ROOT)
    parser_agg.add_argument("-k", "--key_path", type=str, default=KEY_PATH)
    parser_agg.set_defaults(func=aggregate)

    # Update
    parser_update = subparsers.add_parser("update")
    parser_update.add_argument("-d", "--data_dir", type=str, default=DATA_DIR)
    parser_update.add_argument("-o", "--out_root", type=str, default=OUT_ROOT)
    parser_update.add_argument("-k", "--key_path", type=str, default=KEY_PATH)
    parser_update.add_argument("--subject_id", type=str, default="")
    parser_update.add_argument("--survey_id", type=str, default="")
    parser_update.set_defaults(func=update)

    # Collect args
    args = parser.parse_args()
    
    # Print info
    print("Running", args.func.__name__, "with arguments:")
    for arg_name, value in vars(args).items():
        if arg_name != "func":
            print(arg_name, ": ", value, sep="")
    
    # Call
    call_function_with_args(args.func, args)

########### CLI ###########
if __name__ == "__main__":
    cli()
    print("Complete!")
