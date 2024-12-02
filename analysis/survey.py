import pandas as pd
from pathlib import Path
import re
from utils import load_key


class Survey(object):
    def __init__(
        self,
        file,
        key_path="",
        key=None,
        id="",
        subject_id="",
        parse_err=-201,
        skip_ans=-101,
    ):
        self.df = pd.read_csv(file, na_filter=False)
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
        answer = answer.strip()
        try:
            if self.key["invert"] or (
                self.key["invert_qs"] and q_num + 1 in self.key["invert_qs"]
            ):
                return (len(ans_opts) - 1 - int(answer)) + self.key["index"]
            else:
                return self.key["index"] + int(answer)
        except ValueError:  # answer non-numeric (expected most of the time)
            try:
                if self.key["invert"] or (
                    self.key["invert_qs"] and q_num + 1 in self.key["invert_qs"]
                ):
                    return (len(ans_opts) - 1 - ans_opts.index(answer)) + self.key[
                        "index"
                    ]
                else:
                    return self.key["index"] + ans_opts.index(answer)
            except ValueError:
                return self.parse_err

    def eval_question(self, opts, ans, q_num, score_flag):
        """Splits answer options and returns answer score

        Args:
            opts (str): String of answer options split by semicolons
            ans (str): Answer for this question
            q_num (int): This question's number

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
        """Cleans the survey dataframe by removing brackets and dropping rows that are not numerically scored.

        Args:
            minimal (bool, optional): _description_. Defaults to False.
        """
        # TODO: Make this one method call. For some reason, listing the column names doesn't work
        # EX: self.df[["question answer options", "answer"]].apply(lambda x: x.replace("[","").replace("]",""))
        self.df["question answer options"] = self.df["question answer options"].apply(
            lambda x: x.replace("[", "").replace("]", "")
        )
        self.df["answer"] = self.df["answer"].apply(
            lambda x: x.replace("[", "").replace("]", "")
        )

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
        
        for index in idx.array:
            score_flag[index] = False
        
        self.df["score_flag"] = score_flag

    def parse_and_score(self):
        """Parses a given survey and saves a cleaned and scored csv file"""
        self.clean(minimal=True)
        self.mark_to_score()

        # Score each answer
        self.df["score"] = self.df.apply(
            lambda x: self.eval_question(
                x["question answer options"], x["answer"], x.name, x["score_flag"]
            ),
            axis=1,
        )
        
        self.df.drop("score_flag", axis=1, inplace=True)

    def export(self, out_dir, out_prefix=""):
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
