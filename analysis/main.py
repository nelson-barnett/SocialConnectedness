from parsing import parse
from pathlib import Path
import pandas as pd

MIRROR_STRUCTURE = False

data_dir = "L:/Research Project Current/Social Connectedness/Nelson/dev"
out_root = Path("L:/Research Project Current/Social Connectedness/Nelson/dev/results")
key_path = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.csv"


survey_key = pd.read_csv(key_path).T
survey_key = (
    survey_key.rename(columns=survey_key.loc["id"])
    .drop(survey_key.index[0])
    .replace({float("nan"): None})
)

out_root.mkdir(exist_ok=True)

for file in Path(data_dir).glob("[!results]**/**/*.csv"):
    try:
        this_key = survey_key[file.parent.name]
    except KeyError:
        raise Exception("Survey ID not found in key.")

    if this_key["index"] is None and this_key["invert"] is None:
        continue

    if MIRROR_STRUCTURE:
        out_dir = out_root.joinpath(
            file.parent.relative_to(data_dir)
        )  # Mirror path in results directory
        prefix = ""
    else:
        # Group by survey id
        out_dir = out_root.joinpath(file.parent.name)
        prefix = file.parent.parent.parent.name

    out_dir.mkdir(exist_ok=True, parents=True)
    parse(file, out_dir, this_key, prefix)
