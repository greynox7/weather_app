from flask import Flask, render_template, request
import requests
import redis
import json
import os
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, path='/metrics')
print("PrometheusMetrics initialized")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    cache.ping() # Test connection
    print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError:
    print("Warning: Could not connect to Redis. Caching disabled.")
    cache = None

def get_coordinates(city_name):
    # Check cache first
    if cache:
        try:
            cached_data = cache.get(f"geo:{city_name}")
            if cached_data:
                print(f"Cache hit for coordinates: {city_name}")
                return json.loads(cached_data)
        except redis.RedisError as e:
            print(f"Redis error: {e}")

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=ko&format=json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            result = data["results"][0]
            # Save to cache
            if cache:
                try:
                    cache.setex(f"geo:{city_name}", 86400, json.dumps(result)) # Cache for 24 hours
                except redis.RedisError as e:
                    print(f"Redis error saving cache: {e}")
            return result
        return None
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None

def get_weather_data(lat, lon):
    # Check cache first
    cache_key = f"weather:{lat}:{lon}"
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                print(f"Cache hit for weather: {lat}, {lon}")
                return json.loads(cached_data)
        except redis.RedisError as e:
            print(f"Redis error: {e}")

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        current_weather = data.get("current_weather", {})
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weathercode = current_weather.get("weathercode")
        
        status_text = "기타"
        # Simple weather code interpretation
        if weathercode == 0:
            status_text = "맑음 ☀️"
        elif weathercode in [1, 2, 3]:
            status_text = "흐림 ☁️"
        elif weathercode in [45, 48]:
            status_text = "안개 🌫️"
        elif weathercode in [51, 53, 55, 61, 63, 65]:
            status_text = "비 🌧️"
        elif weathercode in [71, 73, 75]:
            status_text = "눈 ❄️"
            
        result = {
            "temperature": temperature,
            "windspeed": windspeed,
            "status_text": status_text
        }

        # Save to cache
        if cache:
            try:
                cache.setex(cache_key, 600, json.dumps(result)) # Cache for 10 minutes
            except redis.RedisError as e:
                print(f"Redis error saving cache: {e}")
        
        return result

    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

@app.route("/")
def read_root():
    city = request.args.get("city", "Seoul")
    city_name = city
    
    # Default to Seoul coordinates
    lat = 37.5665
    lon = 126.9780
    
    if city != "Seoul":
        location = get_coordinates(city)
        if location:
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location["name"]
            if "country" in location:
                city_name += f", {location['country']}"
        else:
            city_name = f"{city} (찾을 수 없음)"

    weather_data = get_weather_data(lat, lon)
    
    if weather_data:
        return render_template("index.html", 
            city_name=city_name,
            temperature=weather_data["temperature"],
            windspeed=weather_data["windspeed"],
            status_text=weather_data["status_text"]
        )
    else:
        return render_template("index.html", 
            city_name=city_name,
            temperature="-",
            windspeed="-",
            status_text="데이터를 가져올 수 없습니다"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
