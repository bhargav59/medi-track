"""
nepali_date.py — AD to Bikram Sambat (BS) date converter
=========================================================
Converts Gregorian (AD) dates to Nepali Bikram Sambat calendar.
Uses a lookup table of BS month lengths for years 2070–2095 BS
(approx. 2013–2039 AD), which covers the operational range.
"""

from datetime import date, timedelta

# BS month lengths for each year (12 months per year)
# Source: Standard Nepali calendar data
BS_CALENDAR_DATA = {
    2070: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2071: [31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
    2072: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2073: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2074: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2075: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2076: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
    2077: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2078: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2079: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2080: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 29, 31],
    2081: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2082: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2083: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2084: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2085: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2086: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
    2087: [30, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
    2088: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2089: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2090: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2091: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2092: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
    2093: [30, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
    2094: [31, 31, 32, 31, 31, 30, 30, 30, 29, 29, 30, 31],
    2095: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
}

# Reference point: 2070/01/01 BS = 2013/04/14 AD
BS_REF_YEAR = 2070
BS_REF_MONTH = 1
BS_REF_DAY = 1
AD_REF_DATE = date(2013, 4, 14)


def ad_to_bs(ad_date):
    """
    Convert a Gregorian (AD) date to Bikram Sambat (BS) date.

    Args:
        ad_date: datetime.date or datetime.datetime object, or 'YYYY-MM-DD' string

    Returns:
        tuple: (bs_year, bs_month, bs_day)
        Returns None if the date is outside the supported range.
    """
    if isinstance(ad_date, str):
        try:
            parts = ad_date.split("-")
            ad_date = date(int(parts[0]), int(parts[1]), int(parts[2].split()[0]))
        except (ValueError, IndexError):
            return None

    if hasattr(ad_date, 'date'):
        ad_date = ad_date.date()

    # Calculate days difference from reference
    diff_days = (ad_date - AD_REF_DATE).days

    if diff_days < 0:
        return None  # Before supported range

    bs_year = BS_REF_YEAR
    bs_month = BS_REF_MONTH
    bs_day = BS_REF_DAY

    # Walk forward through days
    while diff_days > 0:
        if bs_year not in BS_CALENDAR_DATA:
            return None  # Beyond supported range

        month_days = BS_CALENDAR_DATA[bs_year][bs_month - 1]
        remaining_in_month = month_days - bs_day

        if diff_days <= remaining_in_month:
            bs_day += diff_days
            diff_days = 0
        else:
            diff_days -= (remaining_in_month + 1)
            bs_month += 1
            bs_day = 1
            if bs_month > 12:
                bs_month = 1
                bs_year += 1

    return (bs_year, bs_month, bs_day)


def ad_to_bs_string(ad_date):
    """
    Convert AD date to a formatted BS string: 'YYYY/MM/DD'

    Args:
        ad_date: datetime.date, datetime.datetime, or 'YYYY-MM-DD' string

    Returns:
        str: BS date as 'YYYY/MM/DD' or empty string if conversion fails
    """
    result = ad_to_bs(ad_date)
    if result:
        return f"{result[0]}/{result[1]:02d}/{result[2]:02d}"
    return ""


def get_dual_date(ad_date_str):
    """
    Get both BS and AD dates formatted for invoice display.
    Returns: 'BS_DATE  AD_DATE' e.g. '2082/01/06  04/19/2026'
    """
    bs = ad_to_bs_string(ad_date_str)
    # Format AD as MM/DD/YYYY
    try:
        if isinstance(ad_date_str, str):
            parts = ad_date_str.split("-")
            ad_formatted = f"{parts[1]}/{parts[2].split()[0]}/{parts[0]}"
        else:
            ad_formatted = ad_date_str.strftime("%m/%d/%Y")
    except (ValueError, IndexError):
        ad_formatted = str(ad_date_str)

    if bs:
        return f"{bs}&nbsp;&nbsp;{ad_formatted}"
    return ad_formatted


# Quick test
if __name__ == "__main__":
    # Test: 2026-04-19 should be approximately 2083/01/06 BS
    from datetime import date as d
    test = d(2026, 1, 20)
    result = ad_to_bs(test)
    print(f"2026-01-20 AD = {result} BS = {ad_to_bs_string(test)}")
    print(f"Dual: {get_dual_date('2026-01-20')}")

    test2 = d(2026, 4, 19)
    print(f"2026-04-19 AD = {ad_to_bs_string(test2)} BS")
    print(f"Dual: {get_dual_date('2026-04-19')}")
