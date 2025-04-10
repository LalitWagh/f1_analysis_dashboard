# f1_analysis_dashboard/src/data_loader.py
import fastf1 as ff1
import fastf1.ergast
import pandas as pd
import os
import logging
import traceback
from typing import Optional, Union
from f1_analysis_dashboard import config # Use relative import
from fastf1.ergast.interface import ErgastError

logger = logging.getLogger(__name__)

def setup_fastf1_cache() -> bool:
    """
    Configures the FastF1 cache according to settings in config.py.

    Returns:
        True if cache setup was successful or not needed, False otherwise.
    """
    if not config.CACHE_ENABLED:
        logger.info("FastF1 cache is disabled in config.")
        return True

    cache_path = config.CACHE_DIR
    try:
        if not cache_path.exists():
            logger.info(f"Cache directory '{cache_path}' not found. Creating...")
            cache_path.mkdir(parents=True, exist_ok=True)
        else:
             logger.info(f"Using existing cache directory: {cache_path}")

        ff1.Cache.enable_cache(str(cache_path)) # enable_cache expects string path
        logger.info(f"Attempting to enable cache at: {cache_path}")
        ff1.Cache.enable_cache(str(cache_path)) # enable_cache expects string path
        # Access the cache_dir attribute *after* enabling it
        # Assume enable_cache provides necessary feedback or errors if it fails.
        logger.info(f"FastF1 cache enabled using path: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to configure FastF1 cache at '{cache_path}': {e}", exc_info=True)
        return False

def load_session_data(year: int, event: Union[str, int], session_type: str) -> Optional[ff1.core.Session]:
    """
    Loads FastF1 session data with specified loading configuration.

    Args:
        year: Championship year.
        event: Event identifier (Name, City, or Round Number).
        session_type: Session identifier (e.g., 'R', 'Q', 'FP1').

    Returns:
        A loaded FastF1 Session object, or None if loading fails.
    """
    logger.info(f"Attempting to load data for: {year} {event} - {session_type}")
    session: Optional[ff1.Session] = None

    # Ensure cache is set up before loading
    if config.CACHE_ENABLED and not setup_fastf1_cache():
        logger.warning("Cache setup failed. Proceeding without cache, but errors might occur.")
        # Optionally, force disable cache if setup fails critically
        # ff1.Cache.disabled = True

    try:
        session = ff1.get_session(year, event, session_type)
        logger.info(f"Session object created for {session.event.year} {session.event['EventName']} - {session.name}")

        # Load data based on config
        logger.info(f"Loading data components: {config.LOAD_CONFIG}")
        session.load(**config.LOAD_CONFIG) # verbose=False to reduce library output

        # Basic validation after load
        if config.LOAD_CONFIG['laps'] and (not hasattr(session, 'laps') or session.laps is None or session.laps.empty):
             logger.warning("Laps data was requested but seems unavailable or empty after loading.")
        #if config.LOAD_CONFIG['results'] and (not hasattr(session, 'results') or session.results is None or session.results.empty):
        #    logger.warning("Results data was requested but seems unavailable or empty after loading.")

        logger.info(f"Data loaded successfully for {session.event['EventName']} {session.name}")
        return session

    except ErgastError as e:
        logger.error(f"Ergast API error for {year} {event} {session_type}: {e}")
        logger.error("This often happens for future events or very old data. Check event details.")
        return None
    except ff1.core.DataNotLoadedError as e:
         logger.error(f"FastF1 DataNotLoadedError: {e}. Check load config and data availability.")
         return None
    except ConnectionError as e:
        logger.error(f"Connection error loading data: {e}. Check internet connection.")
        return None
    except FileNotFoundError as e:
         # This can happen if cache points to a location that suddenly becomes invalid
         logger.error(f"File not found error during loading (potentially cache related): {e}")
         return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading session data: {e}")
        logger.error(traceback.format_exc()) # Log full traceback for unexpected errors
        return None