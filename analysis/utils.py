import pandas as pd
import inspect


def load_key(fpath):
    """Loads and processes survey key

    Args:
        fpath (str): Path to survey key CSV or XLSX.

    Returns:
        DataFrame: Key formatted such that columns are survey ids
    """

    def to_dict(row, add_to_vals=0):
        """Returns a dictionary made from `row`. Assumes row is of the form "key1:val1,val2,val3;key2:val1,val2,val3..." """
        D = {}
        for x in row.split(";"):
            sep_ind = x.find(":")
            key = int(x[:sep_ind]) if x[:sep_ind].isdigit() else x[:sep_ind]
            val = [int(y) + add_to_vals for y in x[sep_ind + 1 : :].split(",")]
            D[key] = val
        return D

    def to_list(df, name):
        return [
            x if not isinstance(x, str) else [int(y) for y in x.split(",")]
            for x in df[name]
        ]

    # No need to error if key is in .xlsx format instead of csv
    try:
        key = pd.read_csv(fpath)
    except UnicodeDecodeError:
        key = pd.read_excel(fpath)

    # Convert string of invert, no_score vals to list
    key["invert_qs"] = to_list(key, "invert_qs")
    key["no_score"] = to_list(key, "no_score")
    
    # Optional column
    if "n_ans_options" in key.columns:
        key["n_ans_options"] = to_list(key, "n_ans_options")
         
    # Parse subscores and unique rules to dict
    # Subtract 1 from indices of subscores
    key["subscores"] = [
        x if not isinstance(x, str) else to_dict(x, -1) for x in key["subscores"]
    ]
    key["unique_score"] = [
        x if not isinstance(x, str) else to_dict(x) for x in key["unique_score"]
    ]

    key = key.T
    return (
        key.rename(columns=key.loc["id"])
        .drop(key.index[0])
        .replace({float("nan"): None})
    )


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


def excel_style(row, col):
    """Convert given row and column number to an Excel-style cell name.
    Source: https://stackoverflow.com/questions/19153462/get-excel-style-column-names-from-column-number
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = []
    while col:
        col, rem = divmod(col - 1, len(letters))
        result[:0] = letters[rem]
    return "".join(result) + str(row)
