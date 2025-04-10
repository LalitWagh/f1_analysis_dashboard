# f1_analysis_dashboard/src/analysis/lap_analysis.py
import pandas as pd
import numpy as np
import fastf1 as ff1
import logging
from typing import Optional, Tuple

from f1_analysis_dashboard.src.utils import formatting, helpers
from f1_analysis_dashboard import config

logger = logging.getLogger(__name__)

def get_overall_fastest_lap(session: ff1.core.Session) -> Optional[pd.Series]:
    """
    Identifies the single fastest lap across all drivers in the session.

    Args:
        session: The loaded FastF1 Session object (must include laps).

    Returns:
        A pandas Series containing the data for the fastest lap, or None if unavailable.
    """
    logger.info(f"Calculating overall fastest lap for {session.name}...")
    if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
        logger.warning("Laps data not available for fastest lap analysis.")
        return None

    laps = session.laps.copy()
    laps = helpers.ensure_team_info(laps, session) # Ensure team data is present

    try:
        fastest_lap = laps.loc[laps[config.COL_LAP_TIME].idxmin()]

        if pd.isna(fastest_lap[config.COL_LAP_TIME]):
            logger.warning("Could not determine a valid fastest lap (LapTime is NaN).")
            return None

        # Prepare output Series with key info
        fastest_lap_info = fastest_lap[[
            config.COL_DRIVER, config.COL_TEAM, config.COL_LAP_TIME,
            config.COL_LAP_NUMBER, config.COL_SECTOR1, config.COL_SECTOR2,
            config.COL_SECTOR3, config.COL_COMPOUND, config.COL_TYRE_LIFE
        ]].copy() # Ensure we work on a copy

        # Add formatted times for easier reading later
        fastest_lap_info['LapTimeStr'] = formatting.format_timedelta(fastest_lap_info[config.COL_LAP_TIME])
        fastest_lap_info['Sector1Str'] = formatting.format_timedelta(fastest_lap_info.get(config.COL_SECTOR1))
        fastest_lap_info['Sector2Str'] = formatting.format_timedelta(fastest_lap_info.get(config.COL_SECTOR2))
        fastest_lap_info['Sector3Str'] = formatting.format_timedelta(fastest_lap_info.get(config.COL_SECTOR3))
        # Format TyreLife nicely
        tyre_life = fastest_lap_info.get(config.COL_TYRE_LIFE, np.nan)
        fastest_lap_info['TyreLifeStr'] = f"{tyre_life:.0f}" if pd.notna(tyre_life) else 'N/A'


        logger.info(f"Overall fastest lap found: Driver {fastest_lap_info[config.COL_DRIVER]}, Time {fastest_lap_info['LapTimeStr']}")
        return fastest_lap_info

    except KeyError as e:
        logger.error(f"Missing expected column for fastest lap analysis: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error calculating overall fastest lap: {e}", exc_info=True)
        return None


def get_driver_fastest_laps(session: ff1.core.Session) -> Optional[pd.DataFrame]:
    """
    Finds the fastest lap for each driver in the session.

    Args:
        session: The loaded FastF1 Session object (must include laps).

    Returns:
        A pandas DataFrame containing the fastest lap for each driver,
        sorted by lap time, or None if unavailable.
    """
    logger.info(f"Calculating fastest lap per driver for {session.name}...")
    if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
        logger.warning("Laps data not available for driver fastest lap analysis.")
        return None

    laps = session.laps.copy()
    laps = helpers.ensure_team_info(laps, session) # Ensure team data

    try:
        # Ensure LapTime column exists before proceeding
        if config.COL_LAP_TIME not in laps.columns:
            logger.error(f"'{config.COL_LAP_TIME}' column not found in lap data.")
            return None

        # Drop laps with no valid LapTime before grouping
        valid_laps = laps.dropna(subset=[config.COL_LAP_TIME])
        if valid_laps.empty:
            logger.warning("No laps with valid LapTime found.")
            return None

        # Find the index of the fastest lap for each driver
        idx_fastest = valid_laps.groupby(config.COL_DRIVER)[config.COL_LAP_TIME].idxmin()
        driver_fastest = laps.loc[idx_fastest].sort_values(config.COL_LAP_TIME).reset_index(drop=True)

        # Select and potentially reorder relevant columns for output
        cols_to_keep = [
            config.COL_DRIVER, config.COL_TEAM, config.COL_LAP_NUMBER,
            config.COL_LAP_TIME, config.COL_COMPOUND, config.COL_TYRE_LIFE
        ]
        # Filter cols_to_keep to only include those present in the DataFrame
        cols_present = [col for col in cols_to_keep if col in driver_fastest.columns]
        driver_fastest_out = driver_fastest[cols_present].copy()

        # Add formatted time string
        driver_fastest_out['LapTimeStr'] = driver_fastest_out[config.COL_LAP_TIME].apply(formatting.format_timedelta)

        logger.info(f"Found fastest laps for {len(driver_fastest_out)} drivers.")
        return driver_fastest_out

    except KeyError as e:
        logger.error(f"Missing expected column for driver fastest lap analysis: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error calculating driver fastest laps: {e}", exc_info=True)
        return None