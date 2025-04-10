# f1_analysis_dashboard/src/analysis/results_analysis.py
import pandas as pd
import fastf1 as ff1
import logging
from typing import Optional

from f1_analysis_dashboard.src.utils import formatting
from f1_analysis_dashboard import config

logger = logging.getLogger(__name__)

def get_official_results(session: ff1.core.Session) -> Optional[pd.DataFrame]:
    """
    Retrieves and formats the official session results.

    Args:
        session: The loaded FastF1 Session object (must have results loaded).

    Returns:
        A pandas DataFrame containing the formatted official results,
        or None if unavailable.
    """
    session_name = getattr(session, 'name', 'Unknown Session')
    logger.info(f"Retrieving official results for {session_name}...")

    if not hasattr(session, 'results') or session.results is None or session.results.empty:
        logger.warning(f"Results data not available or loaded for {session_name}.")
        # Optionally attempt to load results here if needed:
        # try:
        #     session.load(results=True, laps=False, ...) # Be careful not to overwrite existing data
        # except Exception:
        #     logger.error("Failed to load results data on demand.")
        #     return None
        return None

    try:
        results_df = session.results.copy()

        # --- Data Cleaning and Formatting ---
        # Define desired columns and ensure they exist, adding placeholders if necessary
        required_cols = {
            config.COL_POSITION: 0,
            config.COL_ABBREVIATION: 'N/A',
            config.COL_FULL_NAME: 'N/A',
            config.COL_TEAM_NAME: 'N/A',
            config.COL_STATUS: 'N/A',
            config.COL_TIME: None, # Keep as is initially for TimeStr formatting
            config.COL_POINTS: 0
        }
        for col, default_value in required_cols.items():
            if col not in results_df.columns:
                logger.warning(f"Results column '{col}' not found. Adding with default '{default_value}'.")
                results_df[col] = default_value

        # Format Time column - handle both Timedelta and potentially other representations
        if config.COL_TIME in results_df.columns:
            results_df['TimeStr'] = results_df[config.COL_TIME].apply(formatting.format_timedelta)
        else:
            results_df['TimeStr'] = '' # Should not happen due to check above, but safe

        # Convert Position to integer where possible
        results_df[config.COL_POSITION] = pd.to_numeric(results_df[config.COL_POSITION], errors='coerce').fillna(0).astype(int)

        # Ensure Points is numeric and integer
        results_df[config.COL_POINTS] = pd.to_numeric(results_df[config.COL_POINTS], errors='coerce').fillna(0).astype(int)

        # Fill remaining NaNs in key text columns
        fill_na_map = {
            config.COL_ABBREVIATION: 'N/A',
            config.COL_FULL_NAME: 'N/A',
            config.COL_TEAM_NAME: 'N/A',
            config.COL_STATUS: 'N/A',
            'TimeStr': '' # Fill NaN TimeStr with empty string
        }
        results_df.fillna(value=fill_na_map, inplace=True)

        # Select and order columns for final output/display
        display_cols = [
            config.COL_POSITION, config.COL_ABBREVIATION, config.COL_FULL_NAME,
            config.COL_TEAM_NAME, config.COL_STATUS, 'TimeStr', config.COL_POINTS
        ]
        # Filter list to ensure we only select columns that actually exist
        display_cols = [col for col in display_cols if col in results_df.columns]
        results_out = results_df[display_cols]

        # Sort by position
        if config.COL_POSITION in results_out.columns:
             results_out = results_out.sort_values(by=config.COL_POSITION).reset_index(drop=True)

        logger.info(f"Formatted official results for {len(results_out)} drivers.")
        return results_out

    except Exception as e:
        logger.error(f"Error processing official results: {e}", exc_info=True)
        return None