# server.py
from mcp.server.fastmcp import FastMCP
import httpx
import fitz  # for PyMuPDF
import os

# =======================================================================================
import sys

# Get API key from environment variable
API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not API_KEY:
    print("Error: OPENWEATHER_API_KEY environment variable must be set", file=sys.stderr)
    sys.exit(1)
# =======================================================================================

# Create an MCP server
mcp = FastMCP("MCP Demo")

#==========
# Resources
#==========
@mcp.resource("text://{file_path}")    
def get_file(file_path: str) -> str:
    # Ensure correct path
    actual_path = os.path.abspath(file_path)  # Convert to absolute path
    
    if not os.path.exists(actual_path):
        raise FileNotFoundError(f"Error: File '{actual_path}' not found!")
    
    with open(actual_path, "r", encoding="utf-8") as file:
        return file.read()

@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "Version 1.1"

@mcp.resource("pdf://{file_path}")
def get_pdf_data(file_path: str) -> str:    
    text = ""
    # Ensure correct path
    actual_path = os.path.abspath(file_path)  # Convert to absolute path    
    if not os.path.exists(actual_path):
        raise FileNotFoundError(f"Error: File '{actual_path}' not found!")
    with fitz.open(actual_path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text

#======
# Tools
#======

@mcp.tool()
async def fetch_weather(city: str, units: str = "metric") -> dict:    
    async with httpx.AsyncClient() as client:

        # API_KEY = "xxxxxxxxxxxxxxxxxxxxxx"
        # Using OpenWeatherMap API
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "units": units,
                "appid": API_KEY
            }
        )        
        if response.status_code == 200:
            data = response.json()            
            weather_data = {
                "location": {
                    "name": data["name"],
                    "country": data["sys"]["country"],
                    "coordinates": {
                        "lat": data["coord"]["lat"],
                        "lon": data["coord"]["lon"]
                    }
                },
                "current": {
                    "temp": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "icon_code": data["weather"][0]["icon"]
                },
                "wind": {
                    "speed": data["wind"]["speed"],
                    "direction": data["wind"]["deg"]
                },
                "sun": {
                    "sunrise": data["sys"]["sunrise"],
                    "sunset": data["sys"]["sunset"]
                },
                "units": units,
                "timestamp": data["dt"]
            }            
            return weather_data
        else:
            return {
                "error": f"Weather data not available. Status code: {response.status_code}",
                "message": response.text
            }

# Add a helper tool for temperature conversion
@mcp.tool()
def convert_temperature(temp: float, from_unit: str, to_unit: str) -> float:    
    # First convert to Kelvin as intermediate step
    if from_unit.lower() == "celsius":
        kelvin = temp + 273.15
    elif from_unit.lower() == "fahrenheit":
        kelvin = (temp + 459.67) * 5/9
    elif from_unit.lower() == "kelvin":
        kelvin = temp
    else:
        raise ValueError(f"Unsupported unit: {from_unit}")
    
    # Convert from Kelvin to target unit
    if to_unit.lower() == "celsius":
        return kelvin - 273.15
    elif to_unit.lower() == "fahrenheit":
        return kelvin * 9/5 - 459.67
    elif to_unit.lower() == "kelvin":
        return kelvin
    else:
        raise ValueError(f"Unsupported unit: {to_unit}")

@mcp.tool()
def get_pdf(file_path: str) -> str:    
    return get_pdf_data(file_path)

@mcp.tool()
def get_text(file_path: str) -> str:    
    return get_file(file_path)

#=======
# Prompt
#=======
# Add a weather_report prompt template
@mcp.prompt()
def weather_report(city: str) -> str:
    return f"""
    Please provide a weather report for {city}.
    
    You can use the fetch_weather tool to get current weather data.
    If needed, you can convert temperature units using the convert_temperature tool.
    
    Please include:
    - Current temperature
    - Weather conditions
    - Humidity
    - Wind speed
    - Any relevant weather advice for the conditions
    """

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
