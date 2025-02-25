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


def disp_run_info(args):
    """Prints info about the function call to the command line

    Args:
        args (argparse.Namespace): Contains arguments gathered from the command line
    """
    print("Running", args.func.__name__, "with arguments:")
    for arg_name, value in vars(args).items():
        if arg_name != "func":
            print(arg_name, ": ", value, sep="")


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
