import sys
from pathlib import Path
from argparse import ArgumentParser


def build_kr(
    url,
    beiwe_username,
    beiwe_pw,
    access_key,
    secret_key,
    out_path,
    beiwe_code_path,
    file_pw,
):
    """Builds and saves a keyring file used as a key to download data from Beiwe servers

    Args:
        url (str): Url to Beiwe server. Defaults to: "https://studies.beiwe.org"
        beiwe_username (str): Beiwe username
        beiwe_pw (str): Beiwe password
        access_key (str): Public access key obtained from Beiwe server
        secret_key (str): Secret access key obtained from Beiwe server
        out_path (str): Path to directory into which key will be saved
        beiwe_code_path (str): Path to https://github.com/onnela-lab/beiwe cloned repository
        file_pw (str): Password with which to encrypt the file

    """
    sys.path.append(str(Path(beiwe_code_path).joinpath("code", "forest_mano")))
    from data_summaries import write_keyring  # type: ignore

    D = {
        "URL": url,
        "BEIWE_USERNAME": beiwe_username,
        "BEIWE_PASSWORD": beiwe_pw,
        "BEIWE_ACCESS_KEY": access_key,
        "BEIWE_SECRET_KEY": secret_key,
    }

    write_keyring(out_path, D, True, file_pw)


def main():
    parser = ArgumentParser()
    parser.add_argument("--url", type=str, default="https://studies.beiwe.org")
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--beiwe_pw", type=str, required=True)
    parser.add_argument("--access_key", type=str, required=True)
    parser.add_argument("--secret_key", type=str, required=True)
    parser.add_argument("--out_path", type=str, required=True)
    parser.add_argument("--beiwe_code_path", type=str, required=True)
    parser.add_argument("--file_pw", type=str, default=True)
    args = parser.parse_args()
    build_kr(
        args.url,
        args.username,
        args.beiwe_pw,
        args.access_key,
        args.secret_key,
        args.out_path,
        args.beiwe_code_path,
        args.file_pw,
    )
