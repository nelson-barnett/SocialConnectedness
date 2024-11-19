import pandas as pd
import re
from pathlib import Path

PARSE_ERR = -201
SKIP_ANS = -101


def score(ans_opts, answer, q_ind, score_ind, invert, invert_qs):
    """Survey scoring algorithm

    Args:
        ans_opts (list): List of answer options (strings)
        answer (string): The answer to score
        q_ind (int): Index of this question
        score_ind (int): The scoring index (e.g., some surveys are 1-4, others 0-3)
        invert (bool): Flag to invert responses (0-4 scale survey, 0 match -> returns 4)
        invert_qs (list): List of specific questions to invert (ints)

    Returns:
        int: Scored value
    """
    ans_opts = [i.strip() for i in ans_opts]
    answer = answer.strip()
    try:
        if invert or (invert_qs and q_ind + 1 in invert_qs):
            return (len(ans_opts) - int(answer)) + score_ind
        else:
            return score_ind + int(answer)
    except ValueError:  # answer non-numeric (expected most of the time)
        try:
            if invert or (invert_qs and q_ind + 1 in invert_qs):
                return (len(ans_opts) - ans_opts.index(answer)) + score_ind
            else:
                return score_ind + ans_opts.index(answer)
        except ValueError:
            return PARSE_ERR


def split_and_score(opts, ans, q_ind, survey_key, invert_qs):
    """Splits answer options and returns answer score

    Args:
        opts (str): String of answer options split by semicolons
        ans (str): Answer for this question
        q_ind (int): This question's number
        survey_key (pd.DataFrame): Metadata for how to score this survey
        invert_qs (list): List of integers for questions that should be inverted

    Returns:
        int: Scored answer
    """
    # Catch skippable rows before extracting answer options
    if ans == "NO_ANSWER_SELECTED":
        return SKIP_ANS

    # Beiwe separates questions with semicolon
    sc_space_sep = False

    # Check if expected splits exist (e.g., "opt 1;opt 2;...")
    if re.findall(r"\S;\S", opts):
        splits = re.finditer(r"\S;\S", opts)  # Use them if they exist
    else:
        # Assume splits are separated with spaces, too (e.g., "opt 1; opt 2; ...")
        splits = re.finditer(r"\S;\s\S", opts)
        sc_space_sep = True

    # Containers
    ans_opts = []
    prev_split = []  # Will be an re.Match object

    # Extract each answer option
    # Cannot simply use "split(";") because options may contain semicolons"
    while True:
        try:
            this_split = splits.__next__()
            if not prev_split:  # First option
                ans_opts.append(opts[0 : this_split.start() + 1])
            else:
                if (
                    not sc_space_sep and this_split.start() - prev_split.end() == 1
                ) or (
                    sc_space_sep and this_split.start() - prev_split.end() == 2
                ):  # Single character option
                    # Take just that character
                    ans_opts.extend(
                        [opts[prev_split.end() - 1], opts[this_split.start()]]
                    )
                else:
                    # End of previous split and start of current one
                    ans_opts.append(opts[prev_split.end() - 1 : this_split.start() + 1])
            prev_split = this_split  # Update
        # Length of iterable isn't know prior to looping. Catch for last ans option.
        except StopIteration:
            # If match starts with split pattern, single character ans opt exists
            # Extract both single character option and whatever is remaining
            last_block = opts[this_split.end() - 1 : len(opts)]
            if re.match(r"\S;\S", last_block):
                ans_opts.extend(
                    [opts[this_split.end() - 1], opts[this_split.end() + 1 : len(opts)]]
                )
            elif re.match(r"\S;\s\S", last_block):
                ans_opts.extend(
                    [opts[this_split.end() - 1], opts[this_split.end() + 2 : len(opts)]]
                )
            else:
                # Final answer option is remainder of "q"
                ans_opts.append(last_block)
            break

    return score(
        ans_opts,
        ans,
        q_ind,
        survey_key["index"],
        survey_key["invert"],
        invert_qs,
    )


def parse(fpath, out_dir, survey_key, out_prefix):
    """Parses a given survey and saves a cleaned and scored csv file

    Args:
        fpath (Path): Path to the survey file
        out_dir (str): Path to directory in which to save data
        survey_key (pd.DataFrame): Metadata for how to score this survey
        out_prefix (str): String with which to prefix the saved csv
    """
    # Load
    df = pd.read_csv(fpath, na_filter=False)

    # TODO: Make this one method call. For some reason, listing the column names doesn't work
    # EX: df[["question answer options", "answer"]].apply(lambda x: x.replace("[","").replace("]",""))
    df["question answer options"] = df["question answer options"].apply(
        lambda x: x.replace("[", "").replace("]", "")
    )
    df["answer"] = df["answer"].apply(lambda x: x.replace("[", "").replace("]", ""))

    # Remove all non-question and not presented rows
    df.drop(
        df.loc[
            (df["question type"] == "info_text_box")
            | (df["answer"] == "NOT_PRESENTED")
            | (
                (df["answer"] == "NO_ANSWER_SELECTED")
                & (df["question text"].str.lower().str.startswith("(only answer if"))
            )
            | (
                df["question answer options"]
                .str.lower()
                .str.contains("(?=.*yes)(?=.*no)")  # yes/no questions
            )
        ].index,
        inplace=True,
    )

    df.reset_index(drop=True, inplace=True)

    invert_qs = survey_key["invert_qs"]
    if invert_qs:
        invert_qs = [int(x) for x in survey_key["invert_qs"].split(",")]

    # Score each answer
    df["score"] = df.apply(
        lambda x: split_and_score(
            x["question answer options"], x["answer"], x.name, survey_key, invert_qs
        ),
        axis=1,
    )

    # Export
    if SKIP_ANS in df["score"].unique():
        df.to_csv(
            Path(out_dir).joinpath(
                out_prefix + "_" + fpath.stem + "_OUT_SKIPPED_ANS.csv"
            ),
            index=False,
            header=True,
        )
    elif PARSE_ERR in df["score"].unique():
        df.to_csv(
            Path(out_dir).joinpath(
                out_prefix + "_" + fpath.stem + "_OUT_PARSE_ERR.csv"
            ),
            index=False,
            header=True,
        )
    else:
        df.to_csv(
            Path(out_dir).joinpath(out_prefix + "_" + fpath.stem + "_OUT.csv"),
            index=False,
            header=True,
        )
