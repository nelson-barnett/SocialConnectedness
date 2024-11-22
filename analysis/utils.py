import pandas as pd
import inspect


def load_key(fpath):
    key = pd.read_csv(fpath)
    # Convert string of invert vals to list
    key["invert_qs"] = key["invert_qs"].apply(
        lambda x: x if not isinstance(x, str) else [int(y) for y in x.split(",")]
    )
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
