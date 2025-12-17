from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def get_coordinates(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=ko&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]
        return None
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        current_weather = data.get("current_weather", {})
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weathercode = current_weather.get("weathercode")
        
        status_text = "기타"
        # Simple weather code interpretation
        if weathercode == 0:
            status_text = "맑음☀️"
        elif weathercode in [1, 2, 3]:
            status_text = "흐림☁️"
        elif weathercode in [45, 48]:
            status_text = "안개🌫️"
        elif weathercode in [51, 53, 55, 61, 63, 65]:
            status_text = "비🌧️"
        elif weathercode in [71, 73, 75]:
            status_text = "눈❄️"
            
        return {
            "temperature": temperature,
            "windspeed": windspeed,
            "status_text": status_text
        }

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
    app.run(host="0.0.0.0", port=8000, debug=True)
