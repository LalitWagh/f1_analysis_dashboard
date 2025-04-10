# f1_analysis_dashboard/src/analysis/pace_analysis.py
import pandas as pd
import numpy as np
import fastf1 as ff1
import logging
from typing import Optional

from f1_analysis_dashboard.src.utils import formatting, helpers
from f1_analysis_dashboard import config

logger = logging.getLogger(__name__)

def get_constructor_race_pace(session: ff1.core.Session) -> Optional[pd.Series]:
    """
    Calculates the median race pace for each constructor.

    Filters out first lap, inaccurate laps, and laps significantly slower
    than the overall median lap time. Requires a Race session ('R').

    Args:
        session: The loaded FastF1 Session object (must be Race, include laps).

    Returns:
        A pandas Series with Team as index and median lap time (in seconds)
        as values, sorted fastest to slowest. Returns None if calculation fails.
    """
    session_name = getattr(session, 'name', 'Unknown Session')
    logger.info(f"Calculating constructor race pace for {session_name}...")

    if session_name != config.SESSION_TYPES['R']:
        logger.warning(f"Constructor pace analysis is designed for Race sessions. Session type is '{session_name}'.")
        # Allow continuing, but the results might be less meaningful

    if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
        logger.warning("Laps data not available for constructor pace analysis.")
        return None

    laps = session.laps.copy()
    laps = helpers.ensure_team_info(laps, session) # Critical for grouping

    # Check if team info is usable
    if config.COL_TEAM not in laps.columns or laps[config.COL_TEAM].isnull().all() or laps[config.COL_TEAM].nunique() < 2 :
        logger.error("Cannot perform constructor pace analysis: Team information is missing or insufficient.")
        return None

    try:
        # --- Data Preparation and Filtering ---
        # Convert LapTime to seconds for calculation
        if config.COL_LAP_TIME not in laps.columns:
             logger.error(f"'{config.COL_LAP_TIME}' column missing, cannot calculate pace.")
             return None
        laps[config.COL_LAP_TIME_SECONDS] = laps[config.COL_LAP_TIME].dt.total_seconds()

        # Basic filters
        laps = laps[laps[config.COL_LAP_NUMBER] >= config.MIN_LAP_NUMBER_PACE]
        if config.COL_IS_ACCURATE in laps.columns:
            laps = laps[laps[config.COL_IS_ACCURATE]]
        else:
            logger.warning(f"'{config.COL_IS_ACCURATE}' column not found. Pace calculation might be less accurate.")

        # Filter out laps with no time
        laps.dropna(subset=[config.COL_LAP_TIME_SECONDS], inplace=True)

        if laps.empty:
            logger.warning("No valid laps remaining after initial filtering.")
            return None

        # --- Outlier Filtering (based on overall median) ---
        # Calculate overall median *only* on valid numeric times
        valid_times = laps[config.COL_LAP_TIME_SECONDS]
        if not valid_times.empty:
            median_lap_time = valid_times.median()
            cutoff_time = median_lap_time * config.PACE_FILTER_THRESHOLD
            laps = laps[laps[config.COL_LAP_TIME_SECONDS] <= cutoff_time]
            logger.info(f"Filtered laps slower than {config.PACE_FILTER_THRESHOLD:.0%} of median ({formatting.format_timedelta(pd.Timedelta(seconds=cutoff_time))}).")
        else:
            logger.warning("No valid lap times found for median calculation; skipping outlier filter.")


        if laps.empty:
            logger.warning("No valid laps remaining after outlier filtering.")
            return None

        # --- Calculate Median Pace per Constructor ---
        constructor_pace = laps.groupby(config.COL_TEAM)[config.COL_LAP_TIME_SECONDS].median()

        # Drop teams if their median calculation resulted in NaN (e.g., no valid laps left)
        constructor_pace.dropna(inplace=True)

        if constructor_pace.empty:
             logger.warning("Could not calculate median pace for any constructor after filtering.")
             return None

        constructor_pace = constructor_pace.sort_values() # Sort fastest to slowest

        logger.info(f"Calculated median pace for {len(constructor_pace)} constructors.")
        return constructor_pace

    except KeyError as e:
        logger.error(f"Missing expected column for pace analysis: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error calculating constructor race pace: {e}", exc_info=True)
        return None


# --- NEW FUNCTION ---
def get_driver_race_laps(session: ff1.core.Session) -> Optional[pd.DataFrame]:
    """
    Extracts and cleans lap time data per driver for race pace analysis.

    Applies similar filters as constructor pace (lap number, accuracy,
    basic outlier removal based on overall median).

    Args:
        session: The loaded FastF1 Session object (must be Race, include laps).

    Returns:
        A pandas DataFrame with cleaned lap data (Driver, Team, LapTimeSeconds),
        or None if insufficient data.
    """
    session_name = getattr(session, 'name', 'Unknown Session')
    logger.info(f"Extracting cleaned driver lap times for {session_name}...")

    if session_name != config.SESSION_TYPES['R']:
        logger.warning(f"Driver pace distribution analysis is designed for Race sessions. Session type is '{session_name}'.")
        # Allow continuing, but the results might be less meaningful

    if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
        logger.warning("Laps data not available for driver pace analysis.")
        return None

    laps = session.laps.copy()
    laps = helpers.ensure_team_info(laps, session) # Get Team info

    # Check if team info is usable (needed for coloring/grouping later)
    if config.COL_TEAM not in laps.columns or laps[config.COL_TEAM].isnull().all():
        logger.warning("Team information is missing or incomplete. Proceeding without it for pace calculation, but plotting might lack team colors.")
        # Ensure the column exists even if empty for consistency downstream
        if config.COL_TEAM not in laps.columns: laps[config.COL_TEAM] = 'N/A'
        laps[config.COL_TEAM].fillna('N/A', inplace=True)

    try:
        # --- Data Preparation and Filtering (similar to constructor pace) ---
        if config.COL_LAP_TIME not in laps.columns:
             logger.error(f"'{config.COL_LAP_TIME}' column missing, cannot calculate pace.")
             return None
        laps[config.COL_LAP_TIME_SECONDS] = laps[config.COL_LAP_TIME].dt.total_seconds()

        # Basic filters
        laps = laps[laps[config.COL_LAP_NUMBER] >= config.MIN_LAP_NUMBER_PACE]
        if config.COL_IS_ACCURATE in laps.columns:
            laps = laps[laps[config.COL_IS_ACCURATE]]
        else:
            logger.warning(f"'{config.COL_IS_ACCURATE}' column not found. Pace calculation might be less accurate.")

        # Filter out laps with no time
        laps.dropna(subset=[config.COL_LAP_TIME_SECONDS], inplace=True)

        if laps.empty:
            logger.warning("No valid laps remaining after initial filtering.")
            return None

        # --- Outlier Filtering (based on overall median) ---
        # Note: More advanced analysis might filter outliers *per driver*
        valid_times = laps[config.COL_LAP_TIME_SECONDS]
        if not valid_times.empty:
            median_lap_time = valid_times.median()
            cutoff_time = median_lap_time * config.PACE_FILTER_THRESHOLD
            laps = laps[laps[config.COL_LAP_TIME_SECONDS] <= cutoff_time]
            logger.info(f"Filtered laps slower than {config.PACE_FILTER_THRESHOLD:.0%} of median ({formatting.format_timedelta(pd.Timedelta(seconds=cutoff_time))}).")
        else:
            logger.warning("No valid lap times found for median calculation; skipping outlier filter.")

        if laps.empty:
            logger.warning("No valid laps remaining after outlier filtering.")
            return None

        # Select relevant columns
        output_cols = [config.COL_DRIVER, config.COL_TEAM, config.COL_LAP_TIME_SECONDS]
        # Ensure columns exist before selecting
        output_cols = [col for col in output_cols if col in laps.columns]
        cleaned_laps = laps[output_cols].copy()

        logger.info(f"Prepared cleaned lap data for {cleaned_laps[config.COL_DRIVER].nunique()} drivers.")
        return cleaned_laps

    except KeyError as e:
        logger.error(f"Missing expected column for driver pace analysis: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error preparing driver race laps: {e}", exc_info=True)
        return None