"""Backward-compatible entry point for the original voice assistant."""

from core.weather import extract_weather_city, interpret_weather_date
from main import main

__all__ = ["extract_weather_city", "interpret_weather_date", "main"]


if __name__ == "__main__":
    main()
