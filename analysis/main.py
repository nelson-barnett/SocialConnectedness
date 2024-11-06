from parsing import parse
from pathlib import Path

data_dir = "./data"
out_dir = "./results"

Path(out_dir).mkdir(exist_ok=True)

for file in Path(data_dir).glob("*.csv"):
    parse(file, out_dir)
