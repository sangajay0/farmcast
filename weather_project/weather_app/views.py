# Function to map weather descriptions to background images
import requests
from django.shortcuts import render
from django.utils.translation import gettext as _
import os
from googletrans import Translator 


# Translation dictionary for weather descriptions
weather_translations = {
    "clear sky": {"en": "Clear Sky", "mr": "स्वच्छ आकाश", "te": "తేలికపాటి ఆకాశం", "gu": "સ્પષ્ટ આકાશ"},
    "few clouds": {"en": "Few Clouds", "mr": "काही ढग", "te": "కొద్ది మేఘాలు", "gu": "થોડા વાદળો"},
    "scattered clouds": {"en": "Scattered Clouds", "mr": "पसरलेले ढग", "te": "చెదురుముదురు మేఘాలు", "gu": "વિખરાયેલા વાદળો"},
    "broken clouds": {"en": "Broken Clouds", "mr": "फुटलेल्या ढग", "te": "కంటిన్యూ మేఘాలు", "gu": "ટૂટેલા વાદળો"},
    "overcast clouds": {"en": "Overcast Clouds", "mr": "पूर्णपणे ढगलेले आकाश", "te": "మబ్బులతో నిండి", "gu": "આકર્ષક વાદળો"},
    "rain": {"en": "Rain", "mr": "पाऊस", "te": "వర్షం", "gu": "વરસાદ"},
    "moderate rain": {"en": "Moderate Rain", "mr": "मध्यम पाऊस", "te": "మితమైన వర్షం", "gu": "માધ્યમ વરસાદ"},
    "light rain": {"en": "Light Rain", "mr": "हलका पाऊस", "te": "హాస్యమైన వర్షం", "gu": "હળવા વરસાદ"},
    "thunderstorm": {"en": "Thunderstorm", "mr": "वादळ", "te": "ఎదురు గాలి", "gu": "ધમાકેદાર હવામાન"},
    # Add more descriptions as needed
}

# Translation dictionary for "Suggested Crops"
crop_translations = {
    "Suggested Crops": {"en": "Suggested Crops", "mr": "सूचित पिके", "te": "సూచించిన పంటలు", "gu": "સૂચિત પાકો"}
}

# Translation dictionary for "5-Day Weather Forecast"
forecast_translations = {
    "5-Day Weather Forecast": {"en": "5-Day Weather Forecast", "mr": "५-दिवसांचे हवामान अंदाज", "te": "5-రోజుల వాతావరణ అంచనా", "gu": "5-દિવસોના હવામાન પૂર્વાનુમાન"}
}

# Function to map weather descriptions to background images
def get_background_image(main_weather):
    english_main_weather = main_weather.lower()
    print("Main Weather Description:", main_weather)

    if 'clear' in english_main_weather:
        return 'clear_sky.jpg'
    elif 'clouds' in english_main_weather:
        return 'cloudy.jpeg'
    elif 'rain' in english_main_weather:
        return 'rainy.jpg'
    elif 'snow' in english_main_weather:
        return 'snowy.jpg'
    elif 'thunderstorm' in english_main_weather:
        return 'thunderstorm.jpg'
    else:
        return 'default_weather.jpg'

# Translate weather descriptions based on the language code
def translate_weather_description(description, language_code):
    description = description.lower()
    if description in weather_translations:
        return weather_translations[description].get(language_code, weather_translations[description]['en'])
    return description  # Return the original description if not found in translation

def translate_title(title, language_code, title_translations):
    return title_translations.get(title, {}).get(language_code, title)

# Fetch weather data from OpenWeatherMap API and apply translation
def get_weather(city, country, language_code):
    API_key = '1b2f8c4cbcbd0ee0ce628c4130e28dc2'  # Replace with your API key
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city},{country}&appid={API_key}&units=metric"
    res = requests.get(url)

    if res.status_code != 200:
        return None
    
    weather_data = res.json()
    
    if 'list' not in weather_data:
        return None
    
    forecast = []
    for i in range(0, min(len(weather_data['list']), 40), 8):  # Every 8th item (24 hours)
        day_data = weather_data['list'][i]
        icon_id = day_data['weather'][0]['icon']
        temperature = day_data['main']['temp']
        description = day_data['weather'][0]['description']
        date = day_data['dt_txt'].split(" ")[0]
        
        icon_url = f"http://openweathermap.org/img/wn/{icon_id}@2x.png"
        forecast.append((icon_url, temperature, description, date))
    
    city = weather_data['city']['name']
    country = weather_data['city']['country']
    
    return forecast, city, country

# Modified weather view to handle city and country input
def weather_view(request):
    if request.method == "POST":
        city = request.POST.get("city")
        country = request.POST.get("country")
        soil_type = request.POST.get("soil_type")
        language_code = request.POST.get("language")

        weather_data = get_weather(city, country, language_code)
        if weather_data is None:
            return render(request, "weather_app/index.html", {"error": _("City or Country not found")})
        
        forecast, city, country = weather_data
        avg_temperature = sum(temp for _, temp, _, _ in forecast) / len(forecast)
        climate = determine_climate(avg_temperature)
        suggested_crops = suggest_crops(soil_type, climate, language_code)
        
        # Fetch translations for titles
        suggested_crops_heading = translate_title("Suggested Crops", language_code, crop_translations)
        five_day_forecast_heading = translate_title("5-Day Weather Forecast", language_code, forecast_translations)
        
        # Translate weather descriptions for display
        translated_forecast = [
            {
                "date": date,
                "temperature": temperature,
                "description": translate_weather_description(description, language_code),
                "icon": icon,
            }
            for icon, temperature, description, date in forecast
        ]

        # Determine background image based on the main weather condition of the first forecast item
        current_weather_main = forecast[0][2]  # This assumes description is at index 2
        background_image = get_background_image(current_weather_main)
        
        # Translate city and country names
        translator = Translator()
        city_translation = translator.translate(city, dest=language_code)
        country_translation = translator.translate(country, dest=language_code)

        # Ensure city and country translation (if needed, based on user input)
        city_translation_text = city_translation.text
        country_translation_text = country_translation.text

        context = {
            "forecast": translated_forecast,
            "city": city_translation_text,  # Translated city name
            "country": country_translation_text,  # Translated country name
            "crops": suggested_crops,
            "climate": climate,
            "background_image": background_image,
            "language": language_code,  # Pass the language to the template
            "suggested_crops_heading": suggested_crops_heading,  # Translated heading for crops
            "five_day_forecast_heading": five_day_forecast_heading,  # Translated heading for forecast
        }
        return render(request, "weather_app/index.html", context)
    
    return render(request, "weather_app/index.html")


# Function to determine climate type based on temperature
def determine_climate(temperature):
    if temperature > 25:
        return "Tropical"
    elif 10 <= temperature <= 25:
        return "Temperate"
    else:
        return "Arid"

def suggest_crops(soil_type, climate, language_code):
    crops = {
        "Clay": {
            "Tropical": {"Rice": {"en": "Rice", "mr": "तांदूळ", "te": "బియ్యం", "gu": "ચોખા"}, 
                         "Sugarcane": {"en": "Sugarcane", "mr": "ऊस", "te": "చెరుకు", "gu": "શરદ"},
                         "Cassava": {"en": "Cassava", "mr": "माण", "te": "కసవా", "gu": "કેસાવા"}},
            "Temperate": {"Potatoes": {"en": "Potatoes", "mr": "बटाटे", "te": "ఆలుగడ్డలు", "gu": "બટાકા"},
                          "Carrots": {"en": "Carrots", "mr": "गाजर", "te": "కారెట్", "gu": "ગાજર"},
                          "Onions": {"en": "Onions", "mr": "कांदा", "te": "ఉల్లిపాయలు", "gu": "ડુંગળી"}},
            "Arid": {"Millet": {"en": "Millet", "mr": "बाजरी", "te": "సజ్జ", "gu": "બાજરી"},
                     "Sorghum": {"en": "Sorghum", "mr": "ज्वारी", "te": "జొన్న", "gu": "જવાર"}}
        },
        "Sandy": {
            "Tropical": {"Pineapple": {"en": "Pineapple", "mr": "अननस", "te": "అనాస", "gu": "અનનસ"},
                         "Coconut": {"en": "Coconut", "mr": "नारळ", "te": "కొబ్బరి", "gu": "નાળિયેર"},
                         "Cassava": {"en": "Cassava", "mr": "माण", "te": "కసవా", "gu": "કેસાવા"}},
            "Temperate": {"Corn": {"en": "Corn", "mr": "मका", "te": "మొక్కజొన్న", "gu": "મકાઈ"},
                          "Peas": {"en": "Peas", "mr": "वाटाणा", "te": "బటాని", "gu": "વટાણા"},
                          "Lettuce": {"en": "Lettuce", "mr": "लेट्टुस", "te": "లెట్టుస", "gu": "લેટસ"}},
            "Arid": {"Cactus": {"en": "Cactus", "mr": "कैक्टस", "te": "కాక్టస్", "gu": "કેક્ટસ"},
                     "Date Palm": {"en": "Date Palm", "mr": "खजूर", "te": "ఖర్జూరం", "gu": "ખજુર"}}
        },
        "Loamy": {
            "Tropical": {"Banana": {"en": "Banana", "mr": "केळी", "te": "అరటిపండు", "gu": "કેળુ"},
                         "Cacao": {"en": "Cacao", "mr": "कोको", "te": "కాకావ్", "gu": "કોકો"},
                         "Coffee": {"en": "Coffee", "mr": "कॉफी", "te": "కాఫీ", "gu": "કોફી"}},
            "Temperate": {"Wheat": {"en": "Wheat", "mr": "गहू", "te": "గోధుమలు", "gu": "ગહું"},
                          "Barley": {"en": "Barley", "mr": "ज्वारी", "te": "జొన్న", "gu": "જવાર"},
                          "Tomatoes": {"en": "Tomatoes", "mr": "टोमॅटो", "te": "టమోటాలు", "gu": "ટમેટાં"}},
            "Arid": {"Olives": {"en": "Olives", "mr": "जैतून", "te": "ఆలివ్", "gu": "ઓલિવ્સ"},
                     "Grapes": {"en": "Grapes", "mr": "द्राक्षे", "te": "ద్రాక్ష", "gu": "દ્રાક્ષ"}}
        },
        "Silty": {
            "Tropical": {"Rice": {"en": "Rice", "mr": "तांदूळ", "te": "బియ్యం", "gu": "ચોખા"},
                         "Taro": {"en": "Taro", "mr": "मुगाची", "te": "చెప్పగడ్డ", "gu": "ટારોએ"},
                         "Sugarcane": {"en": "Sugarcane", "mr": "ऊस", "te": "చెరుకు", "gu": "શરદ"}},
            "Temperate": {"Cabbage": {"en": "Cabbage", "mr": "कोबी", "te": "కోసుగడ్డ", "gu": "કોબી"},
                          "Spinach": {"en": "Spinach", "mr": "पालक", "te": "పాలకూర", "gu": "પાલક"},
                          "Broccoli": {"en": "Broccoli", "mr": "ब्रोकली", "te": "బ్రోకోలి", "gu": "બ્રોકોલી"}},
            "Arid": {"Quinoa": {"en": "Quinoa", "mr": "क्विनोआ", "te": "క్వినోవా", "gu": "ક્વિનોઆ"},
                     "Barley": {"en": "Barley", "mr": "ज्वारी", "te": "జొన్న", "gu": "જવાર"}}
        },
    }
    
    selected_crops = crops.get(soil_type, {}).get(climate, {})
    return [
        crop.get(language_code, crop['en'])  # Fallback to 'en' if language key is not found
        for crop in selected_crops.values()
    ] if selected_crops else [_("No suitable crops found.")]




