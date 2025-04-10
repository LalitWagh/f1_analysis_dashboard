# f1_analysis_dashboard/src/utils/helpers.py
import pandas as pd
import fastf1 as ff1
import logging
from f1_analysis_dashboard import config # Use relative import within the package

logger = logging.getLogger(__name__)

def ensure_team_info(laps_df: pd.DataFrame, session: ff1.core.Session) -> pd.DataFrame:
    """
    Ensures the 'Team' column exists and is populated in the laps DataFrame.

    It checks if the column exists. If not, or if it has missing values,
    it attempts to map team names from the session results using the 'Driver'
    abbreviation.

    Args:
        laps_df: DataFrame of lap data.
        session: The FastF1 Session object (must have results loaded).

    Returns:
        The laps DataFrame, potentially with an added/updated 'Team' column.
        Returns the original DataFrame if mapping is not possible.
    """
    if laps_df is None or laps_df.empty:
        logger.warning("Input laps DataFrame is empty or None. Cannot ensure team info.")
        return laps_df

    col_team = config.COL_TEAM
    col_driver = config.COL_DRIVER
    col_abbr = config.COL_ABBREVIATION
    col_team_name = config.COL_TEAM_NAME

    # Check if Team column exists and is sufficiently populated
    if col_team in laps_df.columns and not laps_df[col_team].isnull().all():
         # Count missing values if column exists
         missing_count = laps_df[col_team].isnull().sum()
         if missing_count > 0:
             logger.info(f"'{col_team}' column exists but has {missing_count} missing values. Attempting to fill.")
         else:
             logger.debug(f"'{col_team}' column already exists and is populated.")
             return laps_df # Already good
    else:
        logger.info(f"'{col_team}' column missing or empty. Attempting to map from session results.")


    # Attempt mapping from results
    if hasattr(session, 'results') and session.results is not None and not session.results.empty:
        if col_abbr in session.results.columns and col_team_name in session.results.columns:
            try:
                # Create mapping from Driver Abbreviation (in results) to TeamName
                # Use drop_duplicates in case results have multiple entries per driver (unlikely but safe)
                driver_team_map = session.results.drop_duplicates(subset=[col_abbr])\
                                                 .set_index(col_abbr)[col_team_name]\
                                                 .to_dict()

                # Map using the 'Driver' column in laps_df (assuming it holds the abbreviation)
                if col_driver in laps_df.columns:
                    laps_df[col_team] = laps_df[col_driver].map(driver_team_map)
                    missing_after_map = laps_df[col_team].isnull().sum()
                    if missing_after_map > 0:
                         logger.warning(f"Could not map team for {missing_after_map} lap entries.")
                    else:
                         logger.info("Successfully mapped team information from session results.")
                else:
                     logger.warning(f"Cannot map teams: '{col_driver}' column not found in laps data.")

            except Exception as e:
                logger.error(f"Error during team mapping: {e}", exc_info=True)
        else:
            logger.warning(f"Cannot map teams: Required columns ('{col_abbr}', '{col_team_name}') not found in session results.")
    else:
        logger.warning("Cannot map teams: Session results are not loaded or available.")

    # If mapping failed or wasn't possible, ensure the column exists, filled with N/A
    if col_team not in laps_df.columns:
         laps_df[col_team] = 'N/A'
    elif laps_df[col_team].isnull().any(): # Fill remaining NaNs if mapping was partial
         laps_df[col_team].fillna('N/A', inplace=True)


    return laps_df