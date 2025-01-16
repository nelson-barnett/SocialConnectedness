import inspect


def row_to_dict(
    row,
    row_sep_str,
    kv_sep_str,
    parse_list,
    parse_keys,
    parse_vals=True,
    list_sep_char=",",
    add_to_vals=0,
):
    """Returns a dictionary made from `row`. Assumes row is of the form "key1:val1,val2,val3;key2:val1,val2,val3..." """
    D = {}
    for x in row.split(row_sep_str):
        sep_ind = x.find(kv_sep_str)
        key = int(x[:sep_ind]) if x[:sep_ind].isdigit() and parse_keys else x[:sep_ind]

        if parse_list:
            val = [
                int(y) + add_to_vals if y.isdigit() and parse_vals else y.strip()
                for y in x[sep_ind + len(kv_sep_str) : :].split(list_sep_char)
            ]
        else:
            val = (
                int(x[sep_ind + len(kv_sep_str) : :]) + add_to_vals
                if x[sep_ind + len(kv_sep_str) : :].isdigit() and parse_vals
                else x[sep_ind + len(kv_sep_str) : :].strip()
            )

        D[key] = val
    return D


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
