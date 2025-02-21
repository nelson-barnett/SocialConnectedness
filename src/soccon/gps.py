import calendar


def is_consecutive(days, months, years):
    """Determines if passed data constitute a continuous set of days.

    Args:
        days (Series): Day values
        months (Series): Month values
        years (Series): Year values

    Returns:
        bool: True if data is consecutive, otherwise False
        int: Last index checked + 1 (last day checked)
    """
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


def find_n_cont_days(df, n):
    """Determines if `n` consecutive days exist in `df`.

    Args:
        df (DataFrame): Output CSV of `process_gps` loaded in as a pandas DataFrame.
        n (int, optional): Number of days to check for consecutivity. Defaults to 30.

    Returns:
        bool: True if `n` consecutive days were found, False otherwise
        Series: Start day (day, month, year). If no consecutive set of days found, last tested start day.
        Series: End day (day, month, year). If no consecutive set of days found, last tested end day.
    """
    # Drop all rows containing NaNs
    df.dropna(how="any", inplace=True)
    df_grouped = df.groupby(["year", "month", "day"]).size().reset_index()
    
    start_ind = 0
    final_ind = len(df_grouped) - 1 if n is None or n > len(df_grouped) else n - 1
    max_cont_days = 0
    best_cont_days = []

    # Only able to loop if df is long enough wrt final_ind
    while (
        final_ind <= len(df_grouped) - 1
        and max_cont_days < len(df_grouped) - 1 - start_ind
    ):
        # Check for continuity in this range
        consecutive_found, break_ind = is_consecutive(
            df_grouped.loc[start_ind:final_ind, "day"],
            df_grouped.loc[start_ind:final_ind, "month"],
            df_grouped.loc[start_ind:final_ind, "year"],
        )
        break_ind = start_ind + break_ind
        if n is not None and consecutive_found:
            return (
                break_ind - start_ind + 1,
                df_grouped.loc[start_ind, ["year", "month", "day"]],
                df_grouped.loc[break_ind, ["year", "month", "day"]],
            )
        else:
            # Update range to check starting at failure point of previous range
            curr_cont_days = break_ind - start_ind
            if curr_cont_days > max_cont_days:
                max_cont_days = curr_cont_days
                best_cont_days = [
                    df_grouped.loc[start_ind, ["year", "month", "day"]],
                    df_grouped.loc[break_ind - 1, ["year", "month", "day"]],
                ]
            start_ind = break_ind + 1
            # if looking for the max (n is None), only update the starting index
            final_ind = start_ind + n - 1 if n is not None else len(df_grouped) - 1
            
    # Can't find consecutive sequence of days either b/c df_grouped is too short or from is_consecutive
    return max_cont_days, best_cont_days[0], best_cont_days[1]


def find_max_cont_days(df):
    return find_n_cont_days(df, None)


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
    """Formats series containing day, month, and year to "/" separated string.
    Intended to be used with outputs from `find_n_cont_days`

    Args:
        date (Series): Series containing month, day, year.

    Returns:
        str: Data in `date` formatted as `month/day/year`
    """
    return "/".join((str(date["month"]), str(date["day"]), str(date["year"])))
