"""
nepali_date.py — AD to Bikram Sambat (BS) date converter
=========================================================
Uses the verified `nepali-datetime` library for accurate conversion.
"""

import nepali_datetime
from datetime import date as _date


def ad_to_bs(ad_date):
    """
    Convert a Gregorian (AD) date to Bikram Sambat (BS) date.

    Args:
        ad_date: datetime.date, datetime.datetime, or 'YYYY-MM-DD' string

    Returns:
        tuple: (bs_year, bs_month, bs_day)
        Returns None if conversion fails.
    """
    try:
        if isinstance(ad_date, str):
            parts = ad_date.split("-")
            ad_date = _date(int(parts[0]), int(parts[1]), int(parts[2].split()[0]))
        if hasattr(ad_date, 'date'):
            ad_date = ad_date.date()
        bs = nepali_datetime.date.from_datetime_date(ad_date)
        return (bs.year, bs.month, bs.day)
    except Exception:
        return None


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
    Returns: 'BS_DATE  AD_DATE' e.g. '2082/10/06  01/20/2026'
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
    from datetime import date as d
    test1 = d(2026, 1, 20)
    print(f"2026-01-20 AD = {ad_to_bs_string(test1)} BS  (expected: 2082/10/06)")

    test2 = d(2026, 4, 19)
    print(f"2026-04-19 AD = {ad_to_bs_string(test2)} BS  (expected: 2083/01/06)")
