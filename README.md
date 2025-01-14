# Social Connectedness Project using Beiwe 

## Intro
This repository contains code used to process, aggregate, and analyze data collected from surveys and passive GPS data using the Beiwe app.

## Setup
Install Python: https://www.python.org/downloads/

This project uses Poetry to manage dependencies. 
Install poetry following the instructions here: https://python-poetry.org/docs/#installing-with-the-official-installer

**NOTE**
If you plan to run GPS analysis, make sure you are using Python 3.11, 
as this is what is supported by the source GPS processing code at https://github.com/onnela-lab/forest.
If you are only running survey processing, Python 3.13 works.

## Running Code
All end-user functions are run from the command line. 
Almost all functions are split into "processing" and "aggregating" categories.
Processing functions take raw data and synthesize it into a meaningful form for human analysis.
Aggregating functions take processed data and combine it into an easily readable format.

To run any function, call it by invoking `poetry run SocialConnectedness/src/SocialConnectedness/main.py FUNC --options`,
where `FUNC` is the name of the function (described below) and `--options` is are any and all arguments you wish to pass.

Below is a description of the tools associated with each type of data for this project. 
All examples are shown as if SocialConnectedness/src/SocialConnectedness is the current directory

# Survey
_`process_survey`_:
- data_dir: Path to root directory where data is stored
- out_dir: Path to directory in which data will be saved
- key_path: Path to CSV/Excel key containing survey scoring rules
- subject_id (optional): Individual subject ID to process. Defaults to "".
- survey_id (optional): Individual survey ID to process. Defaults to "".
- skip_dirs (optional): List of directories names to skip when looking for data. Does not need to be full path, only dir name. Defaults to [].
- use_zips (optional): Flag to process CSVs in zip files within `data_dir`. Defaults to False.

_Example function call using all arguments_

`poetry run SocialConnectedness/src/SocialConnectedness/main.py process_survey --data_dir L:/SocialConnectednessProject/Data/Survey Data
--out_dir L:/SocialConnectednessProject/Data/ProcessedData --key_path C:/Users/MyUser/Desktop/SurveyKey.csv 
--subject_id subject1 --survey_id qqqqqqq123 --skip_dirs OldBadData NewWorseData --use_zips False`

_`aggregate_survey`_:
- data_dir: Path to directory in which `processed` data exists.
- out_dir: Directory to which summary sheet should be saved.
- key_path: Path to CSV key containing survey scoring rules
- out_name (optional): Name of output file. Defaults to "SURVEY_SUMMARY".

_Example function call using all arguments_

`poetry run SocialConnectedness/src/SocialConnectedness/main.py aggregate_survey --data_dir L:/SocialConnectednessProject/Data/ProcessedData
--out_dir L:/SocialConnectednessProject/Data/ProcessedData --key_path C:/Users/MyUser/Desktop/SurveyKey.csv 
--out_name Best_Survey_Summary_Ever`

# Acoustic
_`aggregate_acoustic`_:
- data_dir: Path to directory in which data is stored.
- out_dir: Path to directory into which summary will be saved
- out_name (optional): Name of the summary file. Defaults to "ACOUSTIC_SUMMARY".
- subject_id (optional): Subject whose data should be analyzed. Defaults to "".

_Example function call using all arguments_

`poetry run main.py aggregate_acoustic --data_dir L:/SocialConnectednessProject/Data/AcousticData
--out_dir L:/SocialConnectednessProject/Data/ProcessedData --out_name New_Acoustic_Summary1234 --subject_id best_subject`

# GPS
_`process_gps`_:
- data_dir: Path to directory in which data is stored.
- out_dir: Path to directory into which summary will be saved
- subject_ids (optional): List of subject ids to use. If None, all ids in `data_dir` are used. Defaults to None.
- quality_thresh (optional): Data quality threshold. Defaults to 0.05.

_Example function call using all arguments_

`poetry run main.py process_gps --data_dir L:/SocialConnectednessProject/Data/GPSData
--out_dir L:/SocialConnectednessProject/Data/ProcessedData/GPS --subject_ids subj1 subj2 --quality_thresh 0.1`

_`aggregate_gps`_:
- data_dir: Path to directory in which processed data exists
- out_dir: Path to directory into which summary will be saved
- out_name (optional): Name of the summary file. Defaults to "GPS_SUMMARY".

_Example function call using all arguments_

`poetry run main.py aggregate_gps --data_dir L:/SocialConnectednessProject/Data/ProcessedData/GPSData
--out_dir L:/SocialConnectednessProject/Data/ProcessedData --out_name CoolGPSSUMMARY`

# Other
_`combine_summaries`_:
- out_dir: Directory into which document will be saved
- acoustic_path (optional): Path to acoustic summary file. Defaults to "".
- gps_path (optional): Path to gps summary file. Defaults to "".
- survey_path (optional): Path to survey summary file. Defaults to "".
- out_name (optional): Name of output file. Defaults to "COMBINED_SUMMARY".

_Example function call using all arguments_

`poetry run main.py combine_summaries --out_dir L:/SocialConnectednessProject/Data/ProcessedData
--acoustic_path L:/SocialConnectednessProject/Data/ProcessedData/GPSData/New_Acoustic_Summary1234.xlsx
--gps_path L:/SocialConnectednessProject/Data/ProcessedData/CoolGPSSUMMARY.csv
--survey_path L:/SocialConnectednessProject/Data/ProcessedData/ProcessedData/Best_Survey_Summary_Ever.xlsx
--out_name SUMMARY`

# Tips
(TODO: write bash/powershell file from which all functions can be run)


**NOTE:** Forest must be installed separately following the instructions on the github. 
Check here: https://python-poetry.org/docs/repositories/#package-source-constrain to see if integration with poetry is possible.
