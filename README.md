# Social Connectedness Project using Beiwe 

## Intro
This repository contains code used to process, aggregate, and analyze data collected from surveys and passive GPS data using the Beiwe app.

## Setup
### Install Python
Install Python: https://www.python.org/downloads/

**NOTE:**

If you plan to run GPS analysis, make sure you are using Python 3.11, 
as this is what is supported by the source GPS processing code at https://github.com/onnela-lab/forest.
If you are only running survey processing, Python 3.13 works.

### Set up a virtual environment
Create a virtual environment. For detailed instructions, see [here](https://docs.python.org/3/library/venv.html).

In brief, in your working directory, run:

```
python -m venv .venv
```

to create a folder name ".venv" in the current directory.

Then, activate it by running the command below that corresponds to your shell:
(copied from python docs linked above)

| Shell | Command |
|:----- |:------- |  
| bash/zsh | $ source <venv>/bin/activate |
| fish | $ source <venv>/bin/activate.fish |
| csh/tchs | $ source <venv>/bin/activate.csh |
| pwsh | $ <venv>/bin/Activate.ps1 |
| cmd.exe | C:\> <venv>\Scripts\activate.bat |
| PowerShell | PS C:\> <venv>\Scripts\Activate.ps1 |

**NOTE**

Take note of the python version running in your virtual environment. Make sure it is 3.11 if you plan to process GPS data.

### Install
You can install directly from GitHub or from a local version of this code by first cloning this repository. 
With the virtual environment active, run your preferred version:

After cloning:
```console
python -m pip install path/to/SocialConnectedness
```

From GitHub
```console
python -m pip install git+https://github.com/nelson-barnett/SocialConnectedness
```

If you plan to run GPS analysis, be sure to install Onella Lab's [forest](https://github.com/onnela-lab/forest).
Their installation procedure is identical.

## Running Code
Running analysis consists of envoking this module along with the specific function you wish to run and any associated arguments.

Almost all functions are split into "processing" and "aggregating" categories.
Processing functions take raw data and synthesize it into a meaningful form for human analysis.
Aggregating functions take processed data and combine it into an easily readable format.

For ease of use, copy the file `run_analysis.ps1` from this repository to your current working directory.
Edit the paths and variables at the top of the file to your satisfication then uncomment the line(s) with the function(s) you wish to run.

Run analysis by envoking this file:
```console
./run_analysis.ps1
```

**NOTE:**

A similar `.sh` file is on the way soon (1/17/2025).  

### Brief docs
Below is a description of the tools associated with each type of data for this project. 

### Survey
_`process_survey`_:
- data_dir: Path to root directory where data is stored
- out_dir: Path to directory in which data will be saved
- key_path: Path to CSV/Excel key containing survey scoring rules
- subject_ids (optional): List of subject IDs to process. Defaults to [].
- survey_ids (optional): List of survey IDs to process. Defaults to [].
- skip_dirs (optional): List of directories names to skip when looking for data. Only use the dir name, not the full path. Defaults to [].
- use_zips (optional): Flag to process CSVs in zip files within `data_dir`. Defaults to False.
- skip_redcap (optional): Flag to skip over processing REDCap data, if it's encountered. Defaults to False.

_Example function call using all arguments_

```
python -m SocialConnectedness process_survey --data_dir "L:/SocialConnectednessProject/Data/Survey Data" --out_dir "L:/SocialConnectednessProject/Data/ProcessedData" --key_path "C:/Users/MyUser/Desktop/SurveyKey.csv" --subject_ids "subject1" "subject2" --survey_id "qqqqqqq123" "zyxwvut54321" --skip_dirs "OldBadData" "NewWorseData" --use_zips --skip_redcap
```

_`aggregate_survey`_:
- data_dir: Path to directory in which `processed` data exists.
- out_dir: Directory to which summary sheet should be saved.
- key_path: Path to CSV key containing survey scoring rules
- out_name (optional): Name of output file. Defaults to "SURVEY_SUMMARY".

_Example function call using all arguments_

```console
python -m SocialConnectedness aggregate_survey --data_dir "L:/SocialConnectednessProject/Data/ProcessedData" --out_dir "L:/SocialConnectednessProject/Data/ProcessedData" --key_path "C:/Users/MyUser/Desktop/SurveyKey.csv" --out_name 'Best_Survey_Summary_Ever"
```

### Acoustic
_`aggregate_acoustic`_:
- data_dir: Path to directory in which data is stored.
- out_dir: Path to directory into which summary will be saved
- out_name (optional): Name of the summary file. Defaults to "ACOUSTIC_SUMMARY".
- subject_id (optional): Subject whose data should be analyzed. Defaults to "".

_Example function call using all arguments_

```console
python -m SocialConnectedness aggregate_acoustic --data_dir "L:/SocialConnectednessProject/Data/AcousticData" --out_dir "L:/SocialConnectednessProject/Data/ProcessedData" --out_name "New_Acoustic_Summary1234" --subject_id "best_subject"
```

### GPS
_`process_gps`_:
- data_dir: Path to directory in which data is stored.
- out_dir: Path to directory into which summary will be saved
- subject_ids (optional): List of subject ids to use. If None, all ids in `data_dir` are used. Defaults to None.
- quality_thresh (optional): Data quality threshold. Defaults to 0.05.

_Example function call using all arguments_

```console
python -m SocialConnectedness process_gps --data_dir "L:/SocialConnectednessProject/Data/GPSData" --out_dir "L:/SocialConnectednessProject/Data/ProcessedData/GPS" --subject_ids "subj1" "subj2" --quality_thresh 0.1
```

_`aggregate_gps`_:
- data_dir: Path to directory in which processed data exists
- out_dir: Path to directory into which summary will be saved
- out_name (optional): Name of the summary file. Defaults to "GPS_SUMMARY".

_Example function call using all arguments_

```
python -m SocialConnectedness aggregate_gps --data_dir "L:/SocialConnectednessProject/Data/ProcessedData/GPSData" --out_dir "L:/SocialConnectednessProject/Data/ProcessedData" --out_name "CoolGPSSUMMARY"
```

### Other
_`combine_summaries`_:
- out_dir: Directory into which document will be saved
- acoustic_path (optional): Path to acoustic summary file. Defaults to "".
- gps_path (optional): Path to gps summary file. Defaults to "".
- survey_path (optional): Path to survey summary file. Defaults to "".
- out_name (optional): Name of output file. Defaults to "COMBINED_SUMMARY".

_Example function call using all arguments_

```
python -m SocialConnectedness combine_summaries --out_dir "L:/SocialConnectednessProject/Data/ProcessedData" --acoustic_path "L:/SocialConnectednessProject/Data/ProcessedData/GPSData/New_Acoustic_Summary1234.xlsx" --gps_path "L:/SocialConnectednessProject/Data/ProcessedData/CoolGPSSUMMARY.csv" --survey_path "L:/SocialConnectednessProject/Data/ProcessedData/ProcessedData/Best_Survey_Summary_Ever.xlsx" --out_name "SUMMARY"
```
