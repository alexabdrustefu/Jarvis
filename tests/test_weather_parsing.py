import unittest
from datetime import date, timedelta

from core.weather import extract_weather_city, interpret_weather_date


class WeatherParsingTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2025, 5, 5)  # Monday

    def test_relative_dates(self):
        self.assertEqual(
            interpret_weather_date("meteo oggi", self.today), self.today
        )
        self.assertEqual(
            interpret_weather_date("meteo domani", self.today),
            self.today + timedelta(days=1),
        )
        self.assertEqual(
            interpret_weather_date("meteo dopodomani", self.today),
            self.today + timedelta(days=2),
        )

    def test_accented_weekday_is_normalized(self):
        self.assertEqual(
            interpret_weather_date("meteo mercoledì", self.today),
            self.today + timedelta(days=2),
        )

    def test_weekday_means_the_next_occurrence(self):
        self.assertEqual(
            interpret_weather_date("meteo lunedì", self.today),
            self.today + timedelta(days=7),
        )

    def test_numeric_date_and_year_rollover(self):
        self.assertEqual(
            interpret_weather_date("meteo 12/05", self.today),
            date(2025, 5, 12),
        )
        new_year = date(2025, 12, 31)
        self.assertEqual(
            interpret_weather_date("meteo 02/01", new_year),
            date(2026, 1, 2),
        )

    def test_named_month_date(self):
        self.assertEqual(
            interpret_weather_date("meteo 12 maggio 2025", self.today),
            date(2025, 5, 12),
        )

    def test_invalid_date_is_not_interpreted(self):
        self.assertIsNone(interpret_weather_date("meteo 31/02/2025", self.today))

    def test_city_is_extracted_and_capitalized(self):
        self.assertEqual(extract_weather_city("meteo domani a milano?"), "Milano")

    def test_relative_date_is_not_misread_as_a_city(self):
        self.assertIsNone(extract_weather_city("meteo a domani"))
        self.assertIsNone(extract_weather_city("meteo oggi"))


if __name__ == "__main__":
    unittest.main()
