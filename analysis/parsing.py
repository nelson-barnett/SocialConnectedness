import pandas as pd
import re
from pathlib import Path


def score_adi(ans_opts, answer, ind, n_dropped):
    invert_qs = [5, 6, 7, 8, 9, 11, 12]  # Literal question numbers to invert

    # NOTE: Need to check if numeric values in "answer" are flipped before incorporating
    # try:
    #     ans_vals.append(4 - int(df["answer"][ind]))
    #     continue
    # except ValueError:
    #     this_ans = df["answer"][ind]

    # Match answer to list index
    try:
        # "ind + 1" adjusts for python 0-indexing to question 1-indexing
        # subtracting "n_dropped" adjusts for removed non-questions rows above current
        if ind + 1 - n_dropped in invert_qs:
            return 4 - ans_opts.index(answer)
        else:
            return 1 + ans_opts.index(answer)
    except ValueError:
        return -1


def score_alsfrs(ans_opts, answer):
    try:
        return 4 - int(answer)
    except ValueError:  # answer non-numeric (expected most of the time)
        try:
            return 4 - ans_opts.index(answer)
        except ValueError:
            return -1


def parse(fpath, out_dir):
    # Load
    df = pd.read_csv(fpath, na_filter=False)

    # Lists will be same length as df and be added to exported csv
    ans_vals = []
    drop_rows = []

    # Parse/number questions
    # Loop over each question
    for ind, q in enumerate(df["question answer options"]):
        # Catch skippable rows before extracting answer options
        if df["question type"][ind] == "info_text_box":
            drop_rows.append(ind)
            continue

        this_ans = df["answer"][ind]

        if this_ans == "NO_ANSWER_SELECTED" and df["question text"][
            ind
        ].lower().startswith("(only answer if"):
            drop_rows.append(ind)
            continue
        elif this_ans == "NO_ANSWER_SELECTED":
            ans_vals.append(-1)
            continue

        # Beiwe separates questions with semicolon
        splits = re.finditer(r"\S;\S", q)

        ans_opts = []
        prev_split = []
        # Extract each answer option
        while True:
            try:
                this_split = splits.__next__()
                if not prev_split:  # First question
                    ans_opts.append(q[1 : this_split.start() + 1])
                else:  # End of previous split and start of current one
                    ans_opts.append(q[prev_split.end() - 1 : this_split.start() + 1])
                prev_split = this_split  # Update
            # Length of iterable isn't know prior to looping. Catch for last ans option.
            except StopIteration:
                ans_opts.append(q[this_split.end() - 1 : len(q) - 1])
                break

        # Score according to survey rules
        if "ADI" in fpath.stem:
            ans_vals.append(score_adi(ans_opts, this_ans, ind, len(drop_rows)))
        elif "alsfrs" in fpath.stem:
            ans_vals.append(score_alsfrs(ans_opts, this_ans))

    # Make output dataframe
    df_out = df.drop(drop_rows).assign(ans_vals=ans_vals)

    # Add sum row (probably unnecessary)
    # df_out.loc[len(df_out.index)] = [None]*len(df.colums) + [sum(ans_vals), None, None]
    
    # Export
    if -1 in ans_vals:
        df_out.to_csv(
            Path(out_dir).joinpath(fpath.stem + "_OUT_CHECK.csv"),
            index=False,
            header=True,
        )
    else:
        df_out.to_csv(
            Path(out_dir).joinpath(fpath.stem + "_OUT.csv"), index=False, header=True
        )
