##### SETUP
# Change these locations according to your file structure/naming conventions
$DATA_DIR_SURVEY = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_data"
$PROCESSED_DIR_SURVEY = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_results"
$SURVEY_KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.xlsx"
$FILE_NAME_SURVEY_SUMMARY = "SURVEY_SUMMARY"

$DATA_DIR_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data/spa_outputs"
$PROCESSED_DIR_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data"
$FILE_NAME_ACOUSTIC_SUMMARY = "ACOUSTIC_SUMMARY"

$DATA_DIR_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_data"
$PROCESSED_DIR_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_results"
$FILE_NAME_GPS_SUMMARY = "GPS_SUMMARY"
$GPS_QUALITY_THRESH = 0.1

$COMBINED_SUMMARY_OUT_DIR = "L:/Research Project Current/Social Connectedness/Nelson/dev"
$FILE_NAME_COMBINED_SUMMARY = "COMBINED_SUMMARY"


##### Uncomment the line(s) you want to run

### Survey
## process_survey
#  process_survey --data_dir $DATA_DIR_SURVEY --out_dir $PROCESSED_DIR_SURVEY --key_path $SURVEY_KEY_PATH

## To skip certain directories, add them one by one. 
## To only process certain subject or survey ids, add them in the same way
## To process data in zip files, pass the flag "--use_zips" (no value needed)
## To only process REDCap or Beiwe data, specify one of the mutually exclusive flags "only_beiwe" or "only_redcap":
#  process_survey --data_dir $DATA_DIR_SURVEY --out_dir $PROCESSED_DIR_SURVEY --key_path $SURVEY_KEY_PATH --skip_dirs "dir1" "dir2" --use_zips --subject_ids "subj1" "subj2" --survey_ids "surveyid123" "surveyid44444" --only_redcap


## aggregate_survey
#  aggregate_survey --data_dir $PROCESSED_DIR_SURVEY --out_dir $PROCESSED_DIR_SURVEY --key_path $SURVEY_KEY_PATH --out_name $FILE_NAME_SURVEY_SUMMARY

### Acoustic
#  aggregate_acoustic --data_dir $DATA_DIR_ACOUSTIC --out_dir $PROCESSED_DIR_ACOUSTIC --out_name $FILE_NAME_ACOUSTIC_SUMMARY

## If you wish to specify subject IDs to process, add them like so:
#  aggregate_acoustic --data_dir $DATA_DIR_ACOUSTIC --out_dir $PROCESSED_DIR_ACOUSTIC --out_name $FILE_NAME_ACOUSTIC_SUMMARY -- subject_ids "s1" "s2"

### GPS
## process_gps
#  process_gps --data_dir $DATA_DIR_GPS --out_dir $PROCESSED_DIR_GPS --quality_thresh $GPS_QUALITY_THRESH

## To process specific subject IDs. Follow this template:
#  process_gps --data_dir $DATA_DIR_GPS --out_dir $PROCESSED_DIR_GPS --subject_ids "subject1" "subject2"

## aggregate_gps
#  aggregate_gps --data_dir $DATA_DIR_GPS --out_dir $PROCESSED_DIR_GPS --out_name $FILE_NAME_GPS_SUMMARY

## Other

## Uncomment three lines below when running combine_summaries
## Make sure to only pass summaries sheets that exist
# $ACOUSTIC_SUMMARY_PATH = Join-Path -Path $PROCESSED_DIR_ACOUSTIC -ChildPath "$FILE_NAME_ACOUSTIC_SUMMARY.xlsx"
# $SURVEY_SUMMARY_PATH = Join-Path -Path $PROCESSED_DIR_SURVEY -ChildPath "$FILE_NAME_SURVEY_SUMMARY.xlsx"
# $GPS_SUMMARY_PATH = Join-Path -Path $PROCESSED_DIR_GPS -ChildPath "$FILE_NAME_GPS_SUMMARY.csv"

## combine all summaries
#  combine_summaries --out_dir $COMBINED_SUMMARY_OUT_DIR --out_name $FILE_NAME_COMBINED_SUMMARY --acoustic_path $ACOUSTIC_SUMMARY_PATH --survey_path $SURVEY_SUMMARY_PATH --gps_path $GPS_SUMMARY_PATH

## All other valid combine_summaries configurations
#  combine_summaries --out_dir $COMBINED_SUMMARY_OUT_DIR --out_name $FILE_NAME_COMBINED_SUMMARY --survey_path $SURVEY_SUMMARY_PATH --gps_path $GPS_SUMMARY_PATH
#  combine_summaries --out_dir $COMBINED_SUMMARY_OUT_DIR --out_name $FILE_NAME_COMBINED_SUMMARY --acoustic_path $ACOUSTIC_SUMMARY_PATH --gps_path $GPS_SUMMARY_PATH 
#  combine_summaries --out_dir $COMBINED_SUMMARY_OUT_DIR --out_name $FILE_NAME_COMBINED_SUMMARY --acoustic_path $ACOUSTIC_SUMMARY_PATH --survey_path $SURVEY_SUMMARY_PATH
