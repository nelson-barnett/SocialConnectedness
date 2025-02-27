[![Documentation Status](https://github.com/nelson-barnett/SocialConnectedness/actions/workflows/docs.yml/badge.svg?branch=main)](https://nelson-barnett.github.io/SocialConnectedness/index.html)
# Social Connectedness Project using Beiwe 

## Intro
This repository contains code used to analyze, aggregate, and visualize data collected from surveys and passive GPS data using the [Beiwe](https://beiwe.hsph.harvard.edu/) app.

This code is specifically built for the Social Connectedness in ALS project taking place at MGH-IHP, but is intended to be useful for many projects collecting data with Beiwe.

## Setup
Below is a detailed guide to running the scripts provided by this codebase. 
To jump directly to the analysis scripts, go to [Running Code](#running-code)

### Install Python
Install Python: https://www.python.org/downloads/

**NOTE:**

This project requires a Python version <= 3.11, as the data processing API provided by the Beiwe developers, [forest](https://github.com/onnela-lab/forest), is restricted to this version.
 
### Set up a virtual environment
Create a virtual environment. For detailed instructions, see [here](https://docs.python.org/3/library/venv.html).

In brief, in your working directory, run:

```
python -m venv .venv
```

to create a folder name ".venv" in the current directory.

Then, activate it by running the command below that corresponds to your shell (copied from python docs linked above):

| Shell | Command |
|:----- |:------- |  
| bash/zsh | $ source <venv>/bin/activate |
| fish | $ source <venv>/bin/activate.fish |
| csh/tchs | $ source <venv>/bin/activate.csh |
| pwsh | $ <venv>/bin/Activate.ps1 |
| cmd.exe | C:\> <venv>\Scripts\activate.bat |
| PowerShell | PS C:\> <venv>\Scripts\Activate.ps1 |

**NOTE**

Take note of the python version running in your virtual environment. Make sure it is 3.11. 
If multiple python versions exist on the machine, it is easy to accidentally invoke the wrong one. 

### Install
You can install directly from GitHub or from a local version of this code by first 
[cloning](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) this repository. 
With the virtual environment active, run your preferred version:

After cloning:
```console
python -m pip install path/to/SocialConnectedness
```

From GitHub
```console
python -m pip install git+https://github.com/nelson-barnett/SocialConnectedness
```

## Running Code
All analysis scripts are invoked via the command line.

The main analysis scripts are almost all split into "processing" and "aggregating" categories.
Processing scripts take raw data and synthesize it into a meaningful form for human analysis.
Aggregating scripts take processed data and combine it into an easily readable format.

In addition to these, there are several "quality checking" scripts that are used for directly downloading data 
for a subject or given subject or set of subjects from the Beiwe servers 
during the study's data collection period and assessing its volume and quality.    

Two files are provided (`run_analysis.ps1` for Windows and `run_analysis` for Mac) for ease of use.  
Copy the file for your operating system from this repository to your current working directory.
Edit the paths and variables at the top of the file to your satisfication then uncomment the line(s) with the function(s) you wish to run.

Run analysis by envoking the file:

Windows PowerShell:
```console
./run_analysis.ps1
```

Bash (Mac):
```console
bash run_analysis
```

### Brief docs
Below is a description of the tools associated with each type of data for this project.
Refer to the `run_analysis` files to see specific examples.

### Survey
_`process_survey`_:
- -d, --data_dir  
Path to root directory where data is stored
- -o, --out_dir  
Path to directory into which data will be saved
- -k, --key_path  
Path to Excel file containing survey scoring rules
- --subject_ids (optional):  
List of subject IDs to process. If nothing is provided, all subjects in `data_dir` will be used
- --survey_ids (optional):  
List of survey IDs to process. If nothing is provided, all surveys in `data_dir` will be used
- --skip_dirs (optional):  
List of directory names to skip when looking for data. Only use the dir name, not the full path
- --use_zips (optional):  
Flag to process CSVs in zip files within `data_dir`. Defaults to False
- --only_redcap (optional):  
Flag to only process redcap data. Mutually exclusive with `only_beiwe`. Defaults to False
- --only_beiwe (optional):  
Flag to only process beiwe data. Mutually exclusive with `only_redcap`. Defaults to False

_`aggregate_survey`_:
- -d, --data_dir  
Path to root directory where data is stored
- -o, --out_dir  
Path to directory into which data will be saved
- -k, --key_path  
Path to Excel file containing survey scoring rules
- --out_name (optional):  
Name of output file. Defaults to `"SURVEY_SUMMARY"`

### Acoustic
_`aggregate_acoustic`_:
- -d, --data_dir  
Path to root directory where data is stored
- -o, --out_dir  
Path to directory into which data will be saved
- --subject_ids (optional):  
Subjects whose data should be analyzed. If nothing is provided, all subjects in `data_dir` will be used
- --out_name (optional):  
Name of the summary file. Defaults to `"ACOUSTIC_SUMMARY"`

### GPS
_`process_gps`_:
- -d, --data_dir  
Path to root directory where data is stored
- -o, --out_dir  
Path to directory into which data will be saved
- --subject_ids (optional):  
Subjects whose data should be analyzed. If nothing is provided, all subjects in `data_dir` will be used
- --quality_thresh (optional):  
Data quality threshold. Defaults to `0.05`

_`aggregate_gps`_:
- -d, --data_dir  
Path to root directory where data is stored
- -o, --out_dir  
Path to directory into which data will be saved
- --out_name (optional):  
Name of the summary file. Defaults to `"GPS_SUMMARY"`

### Other
_`combine_summaries`_:
- -o, --out_dir  
Path to directory into which data will be saved
- --acoustic_path (optional):  
Path to acoustic summary file. Defaults to ""
- --gps_path (optional):  
Path to gps summary file. Defaults to ""
- --survey_path (optional):  
Path to survey summary file. Defaults to ""
- --out_name (optional):  
Name of output file. Defaults to `"COMBINED_SUMMARY"`

### Quality Check
_`make_key`_:
- --username  
Beiwe username
- --beiwe_pw  
Beiwe password
- --access_key  
Public access key obtained from Beiwe server
- --secret_key  
Secret access key obtained from Beiwe server
- --out_path  
Path to directory into which key will be saved
- --beiwe_code_path  
Path to [this](https://github.com/onnela-lab/beiwe) cloned repository
- --file_pw,  
Password with which to encrypt the file

_`download_and_check`_:
- --keyring_path  
Path to keyring file generated by `make_key`
- --keyring_pw  
Password for the keyring file
- --study_id  
Beiwe study ID
- --out_dir  
Path to directory into which data will be saved
- --beiwe_ids  
Beiwe subject IDs' data to download 
- --beiwe_code_path  
Path to [this](https://github.com/onnela-lab/beiwe) cloned repository
- --time_start  
Earliest date at which to download data. Formatted YYYY-MM-DD. 
If not supplied, earliest collected data will be used for all subjects
- --time_end"  
Latest date at which to download data. Formatted YYYY-MM-DD.
If not supplied, current date will be used for all subjects
- --data_streams  
Data streams to download.
Defaults to ["gps", "survey_timings", "survey_answers", "audio_recordings"]
- --survey_key_path  
Path to Excel file containing survey scoring rules
- --skip_gps_stats  
Flag to skip running GPS processing, as this can sometimes be time-intensive

_`download_beiwe_data`_:
- --keyring_path  
Path to keyring file generated by `make_key`
- --keyring_pw  
Password for the keyring file
- --study_id  
Beiwe study ID
- --out_dir  
Path to directory into which data will be saved
- --beiwe_ids  
Beiwe subject IDs' data to download 
- --beiwe_code_path  
Path to [this](https://github.com/onnela-lab/beiwe) cloned repository
- --time_start  
Earliest date at which to download data. Formatted YYYY-MM-DD. 
If not supplied, earliest collected data will be used for all subjects
- --time_end"  
Latest date at which to download data. Formatted YYYY-MM-DD.
If not supplied, current date will be used for all subjects
- --data_streams  
Data streams to download.
Defaults to ["gps", "survey_timings", "survey_answers", "audio_recordings"]

_`run_quality_check`_:
- --data_dir  
Path to root directory where data is stored
- --subject_id  
Beiwe ID of subject's data to check
- --survey_key_path  
Path to Excel file containing survey scoring rules
- --skip_gps_stats  
Flag to skip running GPS processing, as this can sometimes be time-intensive
