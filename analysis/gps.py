import calendar


def is_consecutive(days, months, years):
    for ind, (day, day_next, month, month_next, year, year_next) in enumerate(
        zip(days, days[1:], months, months[1:], years, years[1:])
    ):
        if (
            (
                day + 1 != day_next
            )  # This breaks continuity unless day_next is the start of a new month
            and (
                (day_next != 1)  # Next day is not the start of a new month
                or (
                    day != calendar.monthrange(year, month)[1]
                )  # Current day isn't the end of the month
                or (
                    (month + 1 != month_next) and (month != 12 and month_next != 1)
                )  # If month didn't go up by one and it wasn't a new year
                or ((month == 12 and month_next == 1) and (year + 1 != year_next))
            )
            or (
                (day + 1 == day_next) and (month != month_next)
            )  # Day is correct but month isn't
            or (
                (day + 1 == day_next) and (month == month_next) and (year != year_next)
            )  # Day and month are correct but year isn't
        ):
            return False, ind + 1
        else:
            continue
    return True, ind + 1


def find_n_cont_days(df, n=30):
    df_grouped = df.groupby(["year", "month", "day"]).size().reset_index()
    consecutive_found = False  # Initialize so while loop can pass without running and func still returns correctly
    start_ind = 0
    final_ind = n - 1

    # Only able to loop if df is long enough wrt final_ind
    while final_ind <= len(df_grouped) - 1:
        # Check for consecutivity in this range
        consecutive_found, final_ind = is_consecutive(
            df_grouped.loc[start_ind:final_ind, "day"],
            df_grouped.loc[start_ind:final_ind, "month"],
            df_grouped.loc[start_ind:final_ind, "year"],
        )
        if consecutive_found:
            return (
                consecutive_found,
                df_grouped.loc[start_ind, ["year", "month", "day"]],
                df_grouped.loc[final_ind, ["year", "month", "day"]],
            )
        else:
            # Update range to check starting at failure point of previous range
            start_ind = final_ind
            final_ind = start_ind + n - 1

    # Can't find consecutive sequence of days either b/c df_grouped is too short or from is_consecutive
    return (
        consecutive_found,
        df_grouped.loc[start_ind, ["year", "month", "day"]],
        df_grouped.loc[len(df_grouped) - 1, ["year", "month", "day"]],
    )


def day_to_obs_day(df, day):
    """Returns the observation day of a given Series that has values of "year", "month", and "day"

    Args:
        df (DataFrame): csv output of gps_stats_main read in by Pandas
        day (Series): "year", "month", and "day" values to find

    Raises:
        Exception: day not found in df

    Returns:
        int: Observation day (0-indexed)
    """
    df_grouped = df.groupby(["year", "month", "day"]).size().reset_index()
    idx = df_grouped.index[(df_grouped[["year", "month", "day"]] == day).all(axis=1)]

    if idx.empty:
        raise Exception(
            "Given group of ",
            day["year"],
            day["month"],
            day["day"],
            "not found in DataFrame",
        )
    else:
        return idx[0]


def date_series_to_str(date):
    return "/".join((str(date["month"]), str(date["day"]), str(date["year"])))
