import pandas as pd
from pathlib import Path
import re
from constants import SURVEY_ANSWER_OPTIONS
from utils import load_key


class Survey(object):
    """Object that contains all relevant information for a given survey
    """
    def __init__(
        self,
        file,
        key_path="",
        key=None,
        id="",
        subject_id="",
        parse_err=-201,
        skip_ans=-101,
        file_df="",
    ):
        """Builds Survey object

        Args:
            file (str): Full path to a CSV survey file (Beiwe output)
            key_path (str, optional): Path to the survey key CSV file. Defaults to "".
            key (Union[Series, None], optional): Series from key specific to this survey. Defaults to None.
            id (str, optional): Survey ID. Defaults to "".
            subject_id (str, optional): Subject ID for this survey. Defaults to "".
            parse_err (int, optional): Value to assign to an answer if there is a parsing error. Defaults to -201.
            skip_ans (int, optional): Value to assign to an answer if it is skipped. Defaults to -101.
            file_df (str, optional): Path to the CSV survey file that is readable by pandas. 
                If file is in a zip file, `file_df` should be zipfile.ZipFile.open(). Defaults to "".

        Raises:
            Exception: Survey ID not found in key
            Exception: Survey ID and key ID do not match. Make sure correct key is being passed.
        """
        file_df = file_df if file_df else file
        self.df = pd.read_csv(file_df, na_filter=False)
        self.parse_err = parse_err
        self.skip_ans = skip_ans
        self.file = Path(file)
        self.subject_id = subject_id

        # No need for checks here because errors will appear in key validation
        self.id = id if id else file.parent.name

        # key supersedes key_path if both are passed
        if not key.empty or not key_path:
            # Robust to caller passing specific key for this study or whole loaded df
            if isinstance(key, pd.DataFrame):
                try:
                    self.key = key[self.id]
                except KeyError:
                    raise Exception("Survey ID not found in key")
            elif key.name != self.id:
                raise Exception(
                    "Survey ID and key ID do not match. Make sure correct key is being passed."
                )
            else:
                self.key = key
        else:
            try:
                # Loading the key will always give the full df so no need for extra conditionals
                self.key = load_key(key_path)[self.id]
            except KeyError:
                raise Exception("Survey ID not found in key")

    def score(self, ans_opts, answer, q_num):
        """Survey scoring algorithm

        Args:
            ans_opts (list): List of answer options (strings)
            answer (string): The answer to score
            q_num (int): Index of this question

        Returns:
            int: Scored value
        """
        ans_opts = [i.strip() for i in ans_opts]
        answer = answer.strip() if isinstance(answer, str) else answer
        mult = self.key["multiplier"] if self.key["multiplier"] else 1
        try:
            if self.key["invert"] or (
                self.key["invert_qs"] and q_num + 1 in self.key["invert_qs"]
            ):
                return mult * ((len(ans_opts) - 1 - int(answer)) + self.key["index"])
            else:
                return mult * (self.key["index"] + int(answer))
        except ValueError:  # answer non-numeric (expected most of the time)
            try:
                if self.key["invert"] or (
                    self.key["invert_qs"] and q_num + 1 in self.key["invert_qs"]
                ):
                    return mult * (
                        (len(ans_opts) - 1 - ans_opts.index(answer)) + self.key["index"]
                    )
                else:
                    return mult * (self.key["index"] + ans_opts.index(answer))
            except ValueError:
                return self.parse_err

    def eval_question(self, opts, ans, q_num, score_flag):
        """Splits answer options and returns answer score

        Args:
            opts (str): String of answer options split by semicolons
            ans (str): Answer for this question
            q_num (int): This question's number
            score_flag (bool): True if this question should be score, Flase if not

        Returns:
            int: Scored answer
        """

        # Catch skippable rows before extracting answer options
        if not score_flag:
            return None
        elif ans == "NO_ANSWER_SELECTED":
            return self.skip_ans

        # Beiwe separates questions with semicolon
        sc_space_sep = False

        # Check if expected splits exist (e.g., "opt 1;opt 2;...")
        if re.findall(r"\S;\S", opts):
            splits = re.finditer(r"\S;\S", opts)  # Use them if they exist
        # elif re.findall(r"\S;\s\S", opts) and not re.findall(r",", opts) and self.id in SURVEY_ANSWER_OPTIONS.keys():
        elif self.id in SURVEY_ANSWER_OPTIONS.keys():
            # If there is a replacement for this exact survey, use it
            opts = SURVEY_ANSWER_OPTIONS[self.id][q_num]
            splits = re.finditer(r"\S;\S", opts)
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
                        ans_opts.append(
                            opts[prev_split.end() - 1 : this_split.start() + 1]
                        )
                prev_split = this_split  # Update
            # Length of iterable isn't know prior to looping. Catch for last ans option.
            except StopIteration:
                # If match starts with split pattern, single character ans opt exists
                # Extract both single character option and whatever is remaining
                last_block = opts[this_split.end() - 1 : len(opts)]
                if re.match(r"\S;\S", last_block):
                    ans_opts.extend(
                        [
                            opts[this_split.end() - 1],
                            opts[this_split.end() + 1 : len(opts)],
                        ]
                    )
                elif re.match(r"\S;\s\S", last_block):
                    ans_opts.extend(
                        [
                            opts[this_split.end() - 1],
                            opts[this_split.end() + 2 : len(opts)],
                        ]
                    )
                else:
                    # Final answer option is remainder of "q"
                    ans_opts.append(last_block)
                break

        return self.score(ans_opts, ans, q_num)

    def clean(self, minimal=False):
        """Cleans the survey dataframe by removing brackets,
        dropping rows that are not numerically scored,
        and replacing " ;" and " ; " with ";" in question answer options.

        Args:
            minimal (bool, optional): Minimal cleaning -- likely True most of the time. 
                If False, drops yes/no, and not presented, "only answer if" + no answer selected question rows.
                Defaults to False.
        """
        self.df["question answer options"] = [
            x.replace("[", "").replace("]", "").replace(" ;", ";").replace(" ; ", ";")
            for x in self.df["question answer options"]
        ]
        self.df["answer"] = [
            x.replace("[", "").replace("]", "") if isinstance(x, str) else x
            for x in self.df["answer"]
        ]

        if minimal:
            # Remove all non-question and not presented rows
            self.df.drop(
                self.df.loc[(self.df["question type"] == "info_text_box")].index,
                inplace=True,
            )
        else:
            # Remove all non-question and not presented rows
            self.df.drop(
                self.df.loc[
                    (self.df["question type"] == "info_text_box")
                    | (self.df["answer"] == "NOT_PRESENTED")
                    | (
                        (self.df["answer"] == "NO_ANSWER_SELECTED")
                        & (
                            self.df["question text"]
                            .str.lower()
                            .str.startswith("(only answer if")
                        )
                    )
                    | (
                        self.df["question answer options"]
                        .str.lower()
                        .str.contains("(?=.*yes)(?=.*no)")  # yes/no questions
                    )
                ].index,
                inplace=True,
            )
        self.df.reset_index(drop=True, inplace=True)

    def mark_to_score(self):
        """Adds a "score_flag" column to self.df 
            containing boolean values indicating whether this question should be scored or not. 
            Marks as false: "not presented, only answer if + no answer selected, and yes/no question rows.
            Similar to those that would be dropped if `minimal = True` in `self.clean()`
        """
        score_flag = [True] * len(self.df)
        idx = self.df.loc[
            (self.df["answer"] == "NOT_PRESENTED")
            | (
                (self.df["answer"] == "NO_ANSWER_SELECTED")
                & (
                    self.df["question text"]
                    .str.lower()
                    .str.startswith("(only answer if")
                )
            )
            | (
                self.df["question answer options"]
                .str.lower()
                .str.contains("(?=.*yes)(?=.*no)")  # yes/no questions
            )
        ].index

        addl_skip = (
            [x - 1 for x in self.key["no_score"]] if self.key["no_score"] else []
        )

        for index in set(list(idx.array) + addl_skip):
            score_flag[index] = False

        self.df["score_flag"] = score_flag

    def parse_and_score(self):
        """Parses a given survey and saves a cleaned and scored csv file"""
        self.clean(minimal=True)
        self.mark_to_score()

        # Score each answer
        self.df["score"] = [
            self.eval_question(opts, ans, q_num, score_flag)
            for q_num, (opts, ans, score_flag) in enumerate(
                zip(
                    self.df["question answer options"],
                    self.df["answer"],
                    self.df["score_flag"],
                )
            )
        ]

        self.df.drop("score_flag", axis=1, inplace=True)

    def export(self, out_dir, out_prefix=""):
        """Saves `self.df` to specified location.
            Appends "_OUT" always. Appends "_OUT_SKIPPED_ANS" and "_OUT_PARSE_ERR" 
            if self.skipped_ans or self.parse_err are in self.df.score. 

        Args:
            out_dir (str): Path to directory into which `self.df` should be saved.
            out_prefix (str, optional): Prefix to prepend to filename. Defaults to "".
        """
        if not out_prefix:
            out_prefix = self.subject_id
        if "score" in self.df.columns:
            if self.skip_ans in self.df["score"].unique():
                self.df.to_csv(
                    Path(out_dir).joinpath(
                        out_prefix + "_" + self.file.stem + "_OUT_SKIPPED_ANS.csv"
                    ),
                    index=False,
                    header=True,
                )
                return
            elif self.parse_err in self.df["score"].unique():
                self.df.to_csv(
                    Path(out_dir).joinpath(
                        out_prefix + "_" + self.file.stem + "_OUT_PARSE_ERR.csv"
                    ),
                    index=False,
                    header=True,
                )
                return
        self.df.to_csv(
            Path(out_dir).joinpath(out_prefix + "_" + self.file.stem + "_OUT.csv"),
            index=False,
            header=True,
        )
