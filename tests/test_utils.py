# f1_analysis_dashboard/tests/test_utils.py
import unittest
import pandas as pd

# Adjust import path based on how you run tests (e.g., from project root)
# If running with `python -m unittest discover` from root:
from src.utils import formatting
# If tests dir is not automatically added to path, might need sys.path manipulation or better test runner setup

class TestFormatting(unittest.TestCase):

    def test_format_timedelta_valid(self):
        td = pd.Timedelta(minutes=1, seconds=35, milliseconds=456)
        self.assertEqual(formatting.format_timedelta(td), "01:35.456")

    def test_format_timedelta_zero(self):
        td = pd.Timedelta(seconds=0)
        self.assertEqual(formatting.format_timedelta(td), "00:00.000")

    def test_format_timedelta_from_seconds_float(self):
         seconds = 90.123
         self.assertEqual(formatting.format_timedelta(seconds), "01:30.123")

    def test_format_timedelta_from_seconds_int(self):
         seconds = 125
         self.assertEqual(formatting.format_timedelta(seconds), "02:05.000")

    def test_format_timedelta_string(self):
        # Test common string representations if needed, though direct conversion is safer
        time_str = "0 days 00:01:22.345000" # Example pandas string output
        td = pd.to_timedelta(time_str)
        self.assertEqual(formatting.format_timedelta(td), "01:22.345")
        # Test direct string conversion if supported/intended (might be risky)
        # self.assertEqual(formatting.format_timedelta("01:15.500"), "01:15.500") # Depends on implementation

    def test_format_timedelta_none_nan(self):
        self.assertEqual(formatting.format_timedelta(None), "N/A")
        self.assertEqual(formatting.format_timedelta(pd.NaT), "N/A")
        self.assertEqual(formatting.format_timedelta(float('nan')), "N/A")


    def test_format_timedelta_invalid_type(self):
        self.assertEqual(formatting.format_timedelta([1, 2]), "Invalid Time") # Example invalid type
        self.assertEqual(formatting.format_timedelta("invalid string"), "Invalid Time")

    def test_format_timedelta_edge_seconds(self):
         # Test near 60 seconds due to potential float issues
         td = pd.Timedelta(seconds=59, milliseconds=999)
         self.assertEqual(formatting.format_timedelta(td), "00:59.999")
         td_slightly_over = pd.Timedelta(seconds=59, microseconds=999999) # Almost 60
         self.assertEqual(formatting.format_timedelta(td_slightly_over), "00:59.999")
         td_minute = pd.Timedelta(seconds=60)
         self.assertEqual(formatting.format_timedelta(td_minute), "01:00.000")


# Example placeholder for helper tests (would need mocking)
# class TestHelpers(unittest.TestCase):
#     def test_ensure_team_info_missing_col(self):
#         # Requires creating mock session.results and laps DataFrame
#         pass
#     def test_ensure_team_info_partial_nan(self):
#         # Requires creating mock session.results and laps DataFrame
#         pass
#     def test_ensure_team_info_no_results(self):
#         # Requires creating mock session with no results
#         pass

if __name__ == '__main__':
    unittest.main()