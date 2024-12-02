from forest.jasmine.traj2stats import Frequency, gps_stats_main

study_folder = "L:Research Project Current/Social Connectedness/Nelson/dev/GPS downloaded from Beiwe/test"
out_folder = "L:/Research Project Current/Social Connectedness/Nelson/dev/GPS downloaded from Beiwe/test/results"

gps_stats_main(study_folder, out_folder, "America/New_York", Frequency.HOURLY, True)
