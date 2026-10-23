"""Local Windows actions, web navigation, date/time, and weather facade."""

import subprocess
import webbrowser
from datetime import date, datetime
from urllib.parse import quote_plus

from actions.weather_actions import WeatherActions


class SystemActions:
    """Runs the supported desktop actions and delegates weather requests."""

    PROGRAMS = {
        "blocco note": ["notepad.exe"],
        "calcolatrice": ["calc.exe"],
        "esplora file": ["explorer.exe"],
        "chrome": ["cmd", "/c", "start", "", "chrome"],
        "google chrome": ["cmd", "/c", "start", "", "chrome"],
    }
    WEBSITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "wikipedia": "https://www.wikipedia.org",
    }
    ARTICLES = ("il ", "lo ", "la ", "l'", "i ", "gli ", "le ")

    def __init__(self, weather: WeatherActions | None = None):
        self.weather = weather or WeatherActions()

    def open_program(self, program: str) -> str:
        program = program.strip().lower()
        for article in self.ARTICLES:
            if program.startswith(article):
                program = program[len(article):]
                break
        command = self.PROGRAMS.get(program)
        if command is None:
            return f"Non conosco il programma: {program}."
        try:
            subprocess.Popen(command)
            return f"Ho aperto {program}."
        except OSError:
            return f"Non sono riuscito ad aprire {program}."

    def search_google(self, query: str) -> str:
        query = query.strip()
        if not query:
            return "Dimmi cosa vuoi cercare."
        webbrowser.open("https://www.google.com/search?q=" + quote_plus(query))
        return f"Sto cercando su Google: {query}"

    def open_website(self, website: str) -> str:
        website = website.strip().lower()
        url = self.WEBSITES.get(website)
        if url is None:
            return f"Non conosco il sito: {website}."
        webbrowser.open(url)
        return f"Sto aprendo {website}."

    @staticmethod
    def get_time() -> str:
        return f"Sono le {datetime.now():%H:%M}."

    @staticmethod
    def get_date() -> str:
        return f"Oggi è il {datetime.now():%d/%m/%Y}."

    def get_location(self) -> dict:
        return self.weather.get_location()

    def get_weather(self) -> str:
        return self.weather.get_weather()

    def get_weather_for_date(self, requested_date: date, city_name: str | None = None) -> str:
        return self.weather.get_weather_for_date(requested_date, city_name)

    def get_city_coordinates(self, city_name: str) -> dict:
        return self.weather.get_city_coordinates(city_name)
