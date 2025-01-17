# Change these locations according to your file structure
$DATA_DIR_SURVEY = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_data"
$PROCESSED_SURVEY_OUT = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_results_w_redcap"
$SUMMARY_FILE_NAME = "SURVEY_SUMMARY_PS1_TEST"

$DATA_DIR_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_data"
$OUT_ROOT_GPS = "L:/Research Project Current/Social Connectedness/Nelson/dev/gps_results"

$DATA_DIR_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data/spa_outputs"
$OUT_ROOT_ACOUSTIC = "L:/Research Project Current/Social Connectedness/Nelson/dev/acoustic_analysis_data"

$KEY_PATH = "L:/Research Project Current/Social Connectedness/Nelson/dev/survey_key.xlsx"

# This may need to be "py"
python -m SocialConnectedness process_survey --data_dir $DATA_DIR_SURVEY --out_dir $PROCESSED_SURVEY_OUT --key_path $KEY_PATH

python -m SocialConnectedness aggregate_survey --data_dir $PROCESSED_SURVEY_OUT --out_dir $PROCESSED_SURVEY_OUT --key_path $KEY_PATH --out_name $SUMMARY_FILE_NAME

