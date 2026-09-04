from datetime import datetime, timezone
from typing import List
import requests
from app.scrapers.base import BaseScraper, ScrapedArticle

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    51: "Light drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    80: "Rain showers",
    95: "Thunderstorm"
}

class WeatherScraper(BaseScraper):
    def __init__(self, city_name: str = "Delhi", topic_name: str = "Weather Update"):
        self.city_name = city_name
        self.topic_name = topic_name

    def get_articles(self, hours: int = 24) -> List[ScrapedArticle]:
        try:
            # 1. Free Geocoding API via Open-Meteo
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.city_name}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5).json()
            if not geo_res.get("results"):
                print(f"   [WARN] Could not find coordinates for {self.city_name}")
                return []

            location = geo_res["results"][0]
            lat, lon = location["latitude"], location["longitude"]
            resolved_name = f"{location.get('name')}, {location.get('admin1', '')} ({location.get('country_code', '')})"

            # 2. Free Forecast API via Open-Meteo
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&timezone=auto"
            )
            w_res = requests.get(weather_url, timeout=5).json()
            current = w_res.get("current", {})
            daily = w_res.get("daily", {})

            condition = WMO_WEATHER_CODES.get(current.get("weather_code", 0), "Fair")
            temp = current.get("temperature_2m", "--")
            feels_like = current.get("apparent_temperature", "--")
            humidity = current.get("relative_humidity_2m", "--")
            wind = current.get("wind_speed_10m", "--")

            max_temp = daily.get("temperature_2m_max", ["--"])[0]
            min_temp = daily.get("temperature_2m_min", ["--"])[0]
            rain_prob = daily.get("precipitation_probability_max", ["0"])[0]

            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            title = f"Weather Briefing for {resolved_name} — {condition}, {temp}°C"
            unique_url = f"https://open-meteo.com/weather/{self.city_name.lower()}/{date_str}"

            content = (
                f"Current weather in {resolved_name}: {condition}.\n"
                f"Temperature: {temp}°C (Feels like {feels_like}°C).\n"
                f"Humidity: {humidity}%, Wind Speed: {wind} km/h.\n"
                f"Today's Forecast: High of {max_temp}°C, Low of {min_temp}°C.\n"
                f"Precipitation Probability: {rain_prob}% chance of rain."
            )

            return [
                ScrapedArticle(
                    title=title,
                    url=unique_url,
                    source="open_meteo",
                    category="weather",
                    topic_name=self.topic_name,
                    raw_content=content,
                    published_at=datetime.now(timezone.utc)
                )
            ]
        except Exception as e:
            print(f"   [ERROR] WeatherScraper error for {self.city_name}: {e}")
            return []
