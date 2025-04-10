# f1_analysis_dashboard/src/utils/formatting.py
import pandas as pd
from typing import Union, Optional

def format_timedelta(td: Optional[Union[pd.Timedelta, float, int, str]]) -> str:
    """
    Formats a pandas Timedelta object, or a value representing seconds,
    into MM:SS.ms string format. Handles None, NaT, or invalid inputs.

    Args:
        td: The input timedelta, numeric (seconds), string, or None.

    Returns:
        Formatted time string (MM:SS.ms), "N/A", or "Invalid Time".
    """
    if pd.isna(td):
        return "N/A"

    try:
        if not isinstance(td, pd.Timedelta):
            # Attempt conversion assuming seconds if numeric, or direct if string
            td = pd.to_timedelta(td, unit='s', errors='coerce')

        if pd.isna(td): # Check again after conversion
            return "N/A"

        # Proceed with formatting
        total_seconds = td.total_seconds()
        minutes, seconds = divmod(total_seconds, 60)
        milliseconds = td.microseconds // 1000 # Get milliseconds part

        # Ensure seconds don't exceed 59 due to floating point nuances with microseconds
        if seconds >= 60:
             seconds = 59.999 # Cap at near 60 to avoid 60.xxx display
             milliseconds = td.microseconds // 1000 # Recalculate ms if needed

        return f"{int(minutes):02d}:{int(seconds):02d}.{milliseconds:03d}"

    except (ValueError, TypeError, AttributeError):
        # Catch potential errors during conversion or attribute access
        return "Invalid Time"