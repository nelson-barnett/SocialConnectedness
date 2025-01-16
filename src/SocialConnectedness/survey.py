import pandas as pd
from pathlib import Path
import re
from constants import SURVEY_ANSWER_OPTIONS
from utils import row_to_dict


class BeiweSurvey(object):
    """Object that contains all relevant information for a given survey"""

    def __init__(
        self,
        file,
        key_path="",
        key=None,
        id="",
        subject_id="",
        parse_err=-201,
        skip_ans=-101,
        validation_err=-301,
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
            validation_err (int, optional): Value to assign to an answer if validation of question failed. Defaults to -301.
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
        self.validation_err = validation_err
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
                self.key = BeiweSurvey.load_key(key_path)[self.id]
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
        # Cleaning just in case
        ans_opts = [i.strip() for i in ans_opts]
        answer = answer.strip() if isinstance(answer, str) else answer

        # Check for multiplier
        mult = self.key["multiplier"] if self.key["multiplier"] else 1

        # Score
        try:
            # This question needs to be inverted (a match on index 0 = max possible score)
            if self.key["invert"] or (
                self.key["invert_qs"] and q_num + 1 in self.key["invert_qs"]
            ):
                return mult * ((len(ans_opts) - 1 - int(answer)) + self.key["index"])
            # This question has unique scoring rules
            elif (
                self.key["unique_score"]
                and q_num + 1 in self.key["unique_score"].keys()
            ):
                return self.key["unique_score"][q_num + 1][int(answer)]
            # Score according to index (a match on index 0 = min possible score)
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
                elif (
                    self.key["unique_score"]
                    and q_num + 1 in self.key["unique_score"].keys()
                ):
                    return self.key["unique_score"][q_num + 1][ans_opts.index(answer)]
                else:
                    return mult * (self.key["index"] + ans_opts.index(answer))
            except ValueError:
                return self.parse_err

    def eval_question(self, opts, ans, q_num, score_flag, question_id):
        """Splits answer options and returns answer score

        Args:
            opts (str): String of answer options split by semicolons
            ans (str): Answer for this question
            q_num (int): This question's number
            score_flag (bool): True if this question should be score, Flase if not

        Returns:
            int: Scored answer
        """

        # Beiwe separates questions with semicolon
        sc_space_sep = False
        options_replaced = False

        # Catch skippable rows before extracting answer options
        if not score_flag:
            return None, options_replaced
        elif ans == "NO_ANSWER_SELECTED":
            return self.skip_ans, options_replaced

        # Containers
        ans_opts = []
        prev_split = []  # Will be an re.Match object

        # Check if expected splits exist (e.g., "opt 1;opt 2;...")
        if re.findall(r"\S;\S", opts):
            splits = re.finditer(r"\S;\S", opts)  # Use them if they exist
        elif self.id in SURVEY_ANSWER_OPTIONS.keys():
            # If there is a replacement for this exact survey, use it
            ans_opts = SURVEY_ANSWER_OPTIONS[self.id][question_id]
            options_replaced = True
        else:
            # Assume splits are separated with spaces, too (e.g., "opt 1; opt 2; ...")
            splits = re.finditer(r"\S;\s\S", opts)
            sc_space_sep = True

        # Extract each answer option
        # Cannot simply use "split(";") because options may contain semicolons"
        if not options_replaced:
            while True:
                try:
                    this_split = splits.__next__()
                    if not prev_split:  # First option
                        ans_opts.append(opts[0 : this_split.start() + 1])
                    else:
                        if (
                            not sc_space_sep
                            and this_split.start() - prev_split.end() == 1
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

        # Number of answer options extracted from survey is incorrect according to the key.
        # Either parsed incorrectly or original survey was improperly constructed (may be the case for surveys collected prior to 2025)
        if (
            not options_replaced
            and "n_ans_options"
            in self.key.index  # Prevents errors since n_ans_options is not technically mandatory
            and self.key["n_ans_options"]
            and len(ans_opts) != self.key["n_ans_options"][q_num]
        ):
            if self.id in SURVEY_ANSWER_OPTIONS.keys():
                ans_opts = SURVEY_ANSWER_OPTIONS[self.id][question_id]
                options_replaced = True
            else:
                return self.validation_err, options_replaced

        # If ans_opts is a list of lists, which is possible if using replacement options
        # since different survey years have same question ids with different answer option formats,
        # Go through all sets of options and return if it scores it sucessfully
        if any(isinstance(el, list) for el in ans_opts):
            for curr_ans_opts in ans_opts:
                score = self.score(curr_ans_opts, ans, q_num)
                if score != self.parse_err:
                    return score, options_replaced
        else:  # ans_options is a single list of options
            return self.score(ans_opts, ans, q_num), options_replaced

        # If list of lists loop didn't return, return whatever it's got
        # Will always be self.parse_err, True
        return score, options_replaced

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

        # Include additionally specified questions to skip
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
        self.df[["score", "options_replaced"]] = [
            self.eval_question(opts, ans, q_num, score_flag, question_id)
            for q_num, (opts, ans, score_flag, question_id) in enumerate(
                zip(
                    self.df["question answer options"],
                    self.df["answer"],
                    self.df["score_flag"],
                    self.df["question id"],
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
        out_suffix = "_OUT"

        if not out_prefix:
            out_prefix = self.subject_id
        if "score" in self.df.columns:
            if self.skip_ans in self.df["score"].unique():
                out_suffix = "_OUT_SKIPPED_ANS"
            elif self.parse_err in self.df["score"].unique():
                out_suffix = "_OUT_PARSE_ERR"
            elif self.validation_err in self.df["score"].unique():
                out_suffix = "_OUT_VALIDATION_ERR"

        self.df.to_csv(
            Path(out_dir).joinpath(
                out_prefix + "_" + self.file.stem + out_suffix + ".csv"
            ),
            index=False,
            header=True,
        )

    @staticmethod
    def load_key(fpath, sheet_name):
        """Loads and processes survey key

        Args:
            fpath (str): Path to survey key CSV or XLSX.

        Returns:
            DataFrame: Key formatted such that columns are survey ids
        """

        def to_list(df, name):
            return [
                x if not isinstance(x, str) else [int(y) for y in x.split(",")]
                for x in df[name]
            ]

        key = pd.read_excel(fpath, sheet_name=sheet_name)

        # Convert string of invert, no_score vals to list
        key["invert_qs"] = to_list(key, "invert_qs")
        key["no_score"] = to_list(key, "no_score")

        # Optional column
        if "n_ans_options" in key.columns:
            key["n_ans_options"] = to_list(key, "n_ans_options")

        # Parse subscores and unique rules to dict
        # Subtract 1 from indices of subscores
        key["subscores"] = [
            x
            if not isinstance(x, str)
            else row_to_dict(
                x,
                row_sep_str=";",
                kv_sep_str=":",
                parse_list=True,
                parse_keys=True,
                add_to_vals=-1,
            )
            for x in key["subscores"]
        ]
        key["unique_score"] = [
            x
            if not isinstance(x, str)
            else row_to_dict(
                x, row_sep_str=";", kv_sep_str=":", parse_list=True, parse_ints=True
            )
            for x in key["unique_score"]
        ]

        key = key.T
        return (
            key.rename(columns=key.loc["id"])
            .drop(key.index[0])
            .replace({float("nan"): None})
        )


class RedcapSurvey(object):
    def __init__(
        self,
        file,
        key_path="",
        key=None,
        id="",
        file_df="",
    ):
        """Builds Survey object

        Args:
            file (str): Full path to a CSV survey file (Beiwe output)
            key_path (str, optional): Path to the survey key CSV file. Defaults to "".
            key (Union[Series, None], optional): Series from key specific to this survey. Defaults to None.
            id (str, optional): Survey ID. Defaults to "".
            file_df (str, optional): Path to the CSV survey file that is readable by pandas.
                If file is in a zip file, `file_df` should be zipfile.ZipFile.open(). Defaults to "".

        Raises:
            Exception: Survey ID not found in key
            Exception: Survey ID and key ID do not match. Make sure correct key is being passed.
        """
        file_df = file_df if file_df else file
        self.df = pd.read_csv(file_df, na_filter=False)
        self.file = Path(file)

        # No need for checks here because errors will appear in key validation
        self.id = id if id else file.stem

        # key supersedes key_path if both are passed
        if isinstance(key, pd.DataFrame) and not key.empty:
            self.key = key
        elif key_path:
            try:
                # Loading the key will always give the full df so no need for extra conditionals
                self.key = RedcapSurvey.load_key(key_path, self.id)
            except ValueError:  # ID doesn't exist as a sheet
                raise Exception("Survey ID not found in key")
        else:
            raise Exception(
                "Either a non-empty key dataframe or a valid key_path must be passed"
            )

    @staticmethod
    def load_key(fpath, sheet_name):
        """Loads and processes survey key

        Args:
            fpath (str): Path to survey key CSV or XLSX.

        Returns:
            DataFrame: Key parsed for use in survey processing
        """
        key = pd.read_excel(fpath, sheet_name=sheet_name)
        key.rename(
            columns={
                "Choices, Calculations, OR Slider Labels": "choices",
                "Variable / Field Name": "question",
            },
            inplace=True,
        )

        key["choices"] = [
            x
            if not isinstance(x, str)
            else row_to_dict(
                x,
                row_sep_str=" | ",
                kv_sep_str=", ",
                parse_list=False,
                parse_keys=False,
            )
            for x in key["choices"]
        ]
        return key

    def process(self):
        # Drop rows where all data columns are empty
        data_cols = [
            x for x in self.df.columns if x not in ["record_id", "redcap_event_name"]
        ]
        self.df.dropna(how="all", subset=data_cols, inplace=True)
        self.df = self.df.reset_index()

        D = {}  # Keys = column name (question shorthand), values = parsed column data
        for this_label, this_col in self.df.items():  # Iterate through columns
            # Get question label as it appears in the key
            if "___" in this_label:  # Checkbox answer type
                question = this_label[: this_label.find("___")]
            else:
                question = this_label

            if question in self.key["question"].values:
                this_q_ser = self.key.loc[self.key["question"] == question]
                
                if this_q_ser["Field Type"].values[0] == "yesno":
                    this_q_key = {"0": "no", "1": "yes"}
                else:
                    this_q_key = this_q_ser["choices"].values[0]
                
                # Translate answers based on key
                if isinstance(this_q_key, dict):
                    # Conditionals in comprehension may be unnecessary, but they're good safety
                    D[this_label] = [
                        this_q_key[x] if this_q_key and x in this_q_key.keys() else x
                        for x in this_col
                    ]
                # No "translation" to do, convert series to list and add as dict value
                else:
                    D[this_label] = list(this_col)
            else:
                D[this_label] = list(this_col)

        # Replace df with processed data
        self.df = pd.DataFrame(D)

    def export(self, out_dir, out_prefix=""):
        """Saves `self.df` to specified location.
            Appends "_OUT" always.

        Args:
            out_dir (str): Path to directory into which `self.df` should be saved.
            out_prefix (str, optional): Prefix to prepend to filename. Defaults to "".
        """
        if out_prefix:
            out_prefix += "_"

        self.df.to_csv(
            Path(out_dir).joinpath(out_prefix + self.file.stem + "_OUT.csv"),
            index=False,
            header=True,
        )


# fpath = "L:/Research Project Current/Social Connectedness/Nelson/dev/REDCap Demographics Survey/Initial Demographic Data Information.csv"
# dfpath = "L:/Research Project Current/Social Connectedness/Nelson/dev/REDCap Demographics Survey/Redcap Export - Initial Demographic & Beiwe ID.csv"
# df = pd.read_csv(dfpath)
