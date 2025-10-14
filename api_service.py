import requests
import json
import csv
import os
from datetime import datetime

# --- Configuration ---
LOG_FILE_PATH = os.path.join("data_logs", "wellbeing_log.csv")
QUOTE_API_URL = "https://zenquotes.io/api/today"
LOCATION_API_URL = "http://ip-api.com/json/"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
# --- End Configuration ---

# NOTE: get_current_location() is no longer needed/used in app.py due to hardcoding, but is kept for completeness.
def get_current_location():
    """Fetches the current city based on IP address."""
    try:
        response = requests.get(LOCATION_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'success':
            return data.get('city', 'Unknown Location')
        return "Unknown Location"
    except (requests.RequestException, json.JSONDecodeError):
        return "Unknown Location"

def fetch_wellbeing_quote():
    """Fetches a daily quote and returns a dictionary."""
    # Print statement kept for terminal debugging/logging
    print("\n*** Your Daily Dose of Wellbeing ***") 
    try:
        response = requests.get(QUOTE_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()[0] 
        quote = data.get('q', 'No quote available.')
        author = data.get('a', 'Unknown')
        print(f"Quote: {quote} — {author}")
        return {'quote': quote, 'author': author}
    except requests.RequestException as e:
        print(f"[Quote API Error] Could not fetch quote. Using default. Error: {e}")
        return {'quote': 'Knowing yourself is the beginning of all wisdom.', 'author': 'Aristotle'}

def fetch_weather(city):
    """Fetches current weather data for the detected city and returns a dictionary."""
    LAT = 51.5074
    LON = 0.1278
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "snowfall", "wind_speed_10m", "wind_direction_10m", "apparent_temperature"],
        "timezone": "Europe/London"
    }
    
    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=5)
        response.raise_for_status()
        current = response.json()['current']
        
        return {
            'temp': current['temperature_2m'],
            'humidity': current['relative_humidity_2m'],
            'wind_speed': current['wind_speed_10m'],
            'rain': current['rain'],
            'snowfall': current['snowfall'],
            'feels_like': current.get('apparent_temperature', current['temperature_2m'])
        }
    except requests.RequestException as e:
        print(f"[Weather API Error] Could not fetch weather data. Error: {e}")
        return None


def fetch_forecast(city):
    """
    MODIFIED: Fetches the 7-day weather forecast and returns a list of dictionaries 
    for the API, instead of printing.
    """
    LAT = 51.5074
    LON = 0.1278
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "Europe/London",
        "forecast_days": 7
    }
    
    forecast_list = []
    
    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=5)
        response.raise_for_status()
        daily = response.json()['daily']
        
        for i in range(7):
            date = daily['time'][i]
            max_temp = daily['temperature_2m_max'][i]
            min_temp = daily['temperature_2m_min'][i]
            precip = daily['precipitation_sum'][i]
            
            if precip > 5.0:
                icon = 'heavy_rain'
            elif precip > 0.1:
                icon = 'rain'
            else:
                icon = 'sun'
            
            forecast_list.append({
                "date": date,
                "max_temp": f"{max_temp:.1f}",
                "min_temp": f"{min_temp:.1f}",
                "precipitation_mm": f"{precip:.1f}",
                "icon_key": icon
            })

        return {"city": city, "forecast": forecast_list}

    except requests.RequestException as e:
        return {"error": f"Could not fetch forecast data: {e}"}

def log_wellbeing_data(quote, author, city, temp, mood, sleep_hours, exercise_done, exercise_minutes): 
    """Logs daily wellbeing data to a CSV file."""
    
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    file_exists = os.path.exists(LOG_FILE_PATH)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = ["Timestamp", "City", "Temperature", "MoodScore", "SleepHours", "ExerciseDone", "ExerciseMinutes", "Quote", "Author"]
    data_row = [timestamp, city, temp, mood, sleep_hours, exercise_done, exercise_minutes, quote, author]

    try:
        with open(LOG_FILE_PATH, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(data_row)
            
        print(f"[Log] Data successfully logged to {LOG_FILE_PATH}")
    
    except Exception as e:
        print(f"[Log Error] Failed to write data: {e}")
