"""Location lookup and weather forecasts from the Open-Meteo APIs."""

import json
from datetime import date
from urllib.parse import quote_plus
from urllib.request import urlopen


WEATHER_DESCRIPTIONS = {
    0: "sereno",
    1: "prevalentemente sereno",
    2: "parzialmente nuvoloso",
    3: "coperto",
    45: "nebbia",
    48: "nebbia con brina",
    51: "pioviggine leggera",
    53: "pioviggine moderata",
    55: "pioviggine intensa",
    61: "pioggia leggera",
    63: "pioggia moderata",
    65: "pioggia intensa",
    71: "neve leggera",
    73: "neve moderata",
    75: "neve intensa",
    80: "rovesci leggeri",
    81: "rovesci moderati",
    82: "rovesci intensi",
    95: "temporale",
    96: "temporale con grandine",
    99: "temporale con grandine intensa",
}


class WeatherActions:
    """Retrieves a location and formats current or forecast weather."""

    @staticmethod
    def _empty_location() -> dict:
        return {"city": None, "latitude": None, "longitude": None}

    def get_location(self) -> dict:
        try:
            with urlopen("https://ipwho.is/", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not data.get("success", False):
                return self._empty_location()
            return {
                "city": data.get("city"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }
        except Exception as error:
            print(f"Errore nel rilevamento della posizione: {error}")
            return self._empty_location()

    def get_city_coordinates(self, city_name: str) -> dict:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={quote_plus(city_name)}&count=1&language=it&format=json"
        )
        try:
            with urlopen(url, timeout=10) as response:
                results = json.loads(response.read().decode("utf-8")).get("results", [])
            if not results:
                return self._empty_location()
            place = results[0]
            return {
                "city": place.get("name"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
            }
        except Exception as error:
            print(f"Errore nella ricerca della città: {error}")
            return self._empty_location()

    def get_weather(self) -> str:
        location = self.get_location()
        latitude, longitude, city = (
            location.get("latitude"), location.get("longitude"), location.get("city")
        )
        if latitude is None or longitude is None:
            return "Non riesco a rilevare la tua posizione."

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m&timezone=auto"
        )
        try:
            with urlopen(url, timeout=10) as response:
                current = json.loads(response.read().decode("utf-8"))["current"]
            description = WEATHER_DESCRIPTIONS.get(current["weather_code"], "condizioni variabili")
            return (
                f"A {city}, al momento è {description}, con {current['temperature_2m']} gradi. "
                f"Temperatura percepita: {current['apparent_temperature']} gradi. "
                f"Umidità: {current['relative_humidity_2m']} per cento. "
                f"Vento: {current['wind_speed_10m']} chilometri orari."
            )
        except Exception as error:
            print(f"Errore nel recupero del meteo: {error}")
            return "Non riesco a recuperare il meteo in questo momento."

    def get_weather_for_date(self, requested_date: date, city_name: str | None = None) -> str:
        location = self.get_city_coordinates(city_name) if city_name else self.get_location()
        latitude, longitude, city = (
            location.get("latitude"), location.get("longitude"), location.get("city")
        )
        if latitude is None or longitude is None:
            return "Non riesco a rilevare la tua posizione."

        days_ahead = (requested_date - date.today()).days
        if days_ahead < 0:
            return "Non posso recuperare previsioni per una data passata."
        if days_ahead > 15:
            return "Posso recuperare previsioni fino a circa 15 giorni."

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_probability_max&forecast_days={max(1, days_ahead + 1)}"
            "&timezone=auto"
        )
        try:
            with urlopen(url, timeout=10) as response:
                daily = json.loads(response.read().decode("utf-8"))["daily"]
            description = WEATHER_DESCRIPTIONS.get(
                daily["weather_code"][days_ahead], "condizioni variabili"
            )
            minimum = daily["temperature_2m_min"][days_ahead]
            maximum = daily["temperature_2m_max"][days_ahead]
            rain = daily["precipitation_probability_max"][days_ahead]
            return (
                f"Previsioni per {requested_date:%d/%m/%Y} a {city}: {description}. "
                f"Minima {minimum} gradi, massima {maximum} gradi. "
                f"Probabilità massima di pioggia: {rain} per cento."
            )
        except Exception as error:
            print(f"Errore nel recupero delle previsioni: {error}")
            return "Non riesco a recuperare le previsioni per questa data."
