"""Heating Degree Days (Heizgradtage) calculation utilities.

Implements Swiss standard SIA 381/3:
  - Heating threshold: 12 °C daily mean temperature
  - HGt = max(0, 12 - daily_mean_temperature)
  - Heating season: October 1 – April 30 (7 months)
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Swiss heating threshold (SIA 381/3)
HEATING_THRESHOLD: float = 12.0

# Heating season boundaries
HEATING_SEASON_START_MONTH: int = 10  # October
HEATING_SEASON_END_MONTH: int = 4     # April
HEATING_SEASON_END_DAY: int = 30      # April 30


def calculate_heating_degree_days(daily_mean_temp: float | None) -> float | None:
    """Calculate heating degree days for a single day.

    Args:
        daily_mean_temp: Daily mean temperature in °C.

    Returns:
        Heating degree days value, or None if input is None.
    """
    if daily_mean_temp is None:
        return None
    return max(0.0, HEATING_THRESHOLD - daily_mean_temp)


def is_in_heating_season(d: date | None = None) -> bool:
    """Check if a date falls within the Swiss heating season (Oct 1 – Apr 30).

    Args:
        d: Date to check (defaults to today).

    Returns:
        True if the date is within the heating season.
    """
    if d is None:
        d = date.today()

    month = d.month
    if month >= HEATING_SEASON_START_MONTH:  # Oct–Dec
        return True
    if month <= HEATING_SEASON_END_MONTH:    # Jan–Apr
        return True
    return False


def get_heating_season_start_date(d: date | None = None) -> date:
    """Get the start date of the current heating season.

    If we're before October, the season started last October.
    If we're in October or later, the season started this October.

    Returns:
        October 1st of the relevant heating season year.
    """
    if d is None:
        d = date.today()

    if d.month >= HEATING_SEASON_START_MONTH:
        return date(d.year, HEATING_SEASON_START_MONTH, 1)
    else:
        return date(d.year - 1, HEATING_SEASON_START_MONTH, 1)


def compute_season_hgt(daily_temperatures: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute accumulated heating degree days for the current heating season.

    Expects a list of daily entries with 'date' (ISO string) and 'temperature_mean'
    keys. Entries outside the current heating season are ignored.

    Returns:
        Dict with keys: season_start, season_hgt, days_counted, today_hgt.
    """
    today = date.today()
    season_start = get_heating_season_start_date(today)

    season_hgt = 0.0
    days_counted = 0
    today_hgt = 0.0

    for entry in daily_temperatures:
        try:
            entry_date_str = entry.get("date", "")
            if not entry_date_str:
                continue
            # Parse ISO date
            if "T" in entry_date_str:
                entry_date = datetime.fromisoformat(entry_date_str).date()
            else:
                entry_date = date.fromisoformat(entry_date_str[:10])

            # Skip entries before season start
            if entry_date < season_start:
                continue
            # Skip entries in the future
            if entry_date > today:
                continue

            temp_mean = entry.get("temperature_mean")
            if temp_mean is None:
                continue

            hgt = calculate_heating_degree_days(float(temp_mean))
            if hgt is not None:
                season_hgt += hgt
                days_counted += 1

                if entry_date == today:
                    today_hgt = hgt

        except (ValueError, TypeError) as err:
            _LOGGER.debug("Skipping invalid daily entry: %s", err)
            continue

    return {
        "season_start": season_start.isoformat(),
        "season_hgt": round(season_hgt, 1),
        "days_counted": days_counted,
        "today_hgt": round(today_hgt, 1),
    }
