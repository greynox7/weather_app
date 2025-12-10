from flask import Flask, render_template
import requests

app = Flask(__name__)

def get_weather_data():
    # Seoul coordinates: latitude 37.5665, longitude 126.9780
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&current_weather=true&timezone=Asia%2FSeoul"
    
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
            status_text = "맑음    ☀️"
        elif weathercode in [1, 2, 3]:
            status_text = "흐림    ☁️"
        elif weathercode in [45, 48]:
            status_text = "안개    🌫️"
        elif weathercode in [51, 53, 55, 61, 63, 65]:
            status_text = "비    🌧️"
        elif weathercode in [71, 73, 75]:
            status_text = "눈    ❄️"
            
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
    weather_data = get_weather_data()
    
    if weather_data:
        return render_template("index.html", 
            temperature=weather_data["temperature"],
            windspeed=weather_data["windspeed"],
            status_text=weather_data["status_text"]
        )
    else:
        return render_template("index.html", 
            temperature="-",
            windspeed="-",
            status_text="데이터를 가져올 수 없습니다"
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
