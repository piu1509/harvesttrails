from django.shortcuts import render, redirect
import openai
from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.assistantapp.models import *
from apps.farms.models import *
from apps.field.models import *
from geopy.geocoders import Nominatim
import requests
from django.http import StreamingHttpResponse
from datetime import datetime, timedelta
import time
from pytz import timezone
import math
from timezonefinder import TimezoneFinder

# Create your views here.

@login_required()
def helpapi(request):
    if 'Grower' in request.user.get_role() and not request.user.is_superuser :
        if request.method == 'POST':
            question = request.POST.get('qes')     
            # prompt = "what is best cotton variety in usa"
            if question :
                response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=question,
                temperature=0.5,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
                )
                if response.choices:
                    generated_text = response.choices[0].text
                    user_id = request.user.id
                    user_name = User.objects.get(id=user_id).username
                    save_assistantApp = AssistantApp(user_id=user_id,user_name=user_name,user_role='Grower',
                                                     question=question,answer=generated_text)
                    save_assistantApp.save()
                    return JsonResponse ({"ans":generated_text})
                else:
                    generated_text = "Error generating text"
                    return JsonResponse ({"ans":""})
            else:
                return JsonResponse ({"ans":""})
        else:
            return JsonResponse ({"ans":""})
    else:
        return redirect('dashboard')
    

def location_details(lat,lon):
    geolocator = Nominatim(user_agent="timezone_app")
    coordinates = f"{lat} , {lon}"
    location = geolocator.reverse(coordinates)
    address = location.raw['address']
    return address

def get_climate_report_current(latitude, longitude):
    send_data = []
    api_key = "869bf5c36bd136408ba382cd5fea0f1e"  # Replace with your OpenWeatherMap API key
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    # Create the API request URL
    url = f"{base_url}?lat={latitude}&lon={longitude}&appid={api_key}"
    # Send the GET request to the API
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Extract the relevant climate information
        # temperature = float(data['main']['temp']) - 273.15
        temperature = float(data['main']['temp'])
        f = (temperature - 273.15) * (9/5) + 32
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        wind = data['wind']['speed']
        temperature_ceil = math.ceil(float(f))
        wind_ceil = math.ceil(float(wind))
        # send_data =  [{"f_temperature":round(temperature, 2),"f_humidity":humidity,"f_wind":wind,"f_description":description}]
        send_data =  [{"f_temperature":int(temperature_ceil),"f_humidity":humidity,"f_wind":int(wind_ceil),"f_description":description}]
    else:
        send_data =  [{"f_temperature":None,"f_humidity":None,"f_wind":None,"f_description":None}]
    
    return send_data

# New 26-07-23
def get_climate_report_forecast(latitude, longitude):
    send_data = []
    base_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data['properties']['forecast']
        forecast_hourly_api = data['properties']['forecastHourly']
        forecastZone = str(data["properties"]["forecastZone"]).split("/")[-1] if str(data["properties"]["forecastZone"]).split("/") else None
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            get_forecast_data = forecast_data["properties"]["periods"]
            
            for i in get_forecast_data :
                temperature = i["temperature"]
                startTime, shortForecast = i["startTime"], i["shortForecast"]
                relativeHumidity, windSpeed = i["relativeHumidity"]["value"], i["windSpeed"]
                # f_temperature =round(float(i["temperature"]), 2) 
                # c_temperature = round((5/9) * (f_temperature-32))
                if "Cloudy" in shortForecast :
                    get_shortForecast="cloudy"
                elif "Fog" in shortForecast :
                    get_shortForecast="cloudy"
                elif "Sunny" in shortForecast :
                    get_shortForecast="sunny"
                elif "Clear" in shortForecast :
                    get_shortForecast="sunny"
                elif "Rainy" in shortForecast :
                    get_shortForecast="rainy"
                elif "Rain" in shortForecast :
                    get_shortForecast="rainy"
                elif "Snow" in shortForecast :
                    get_shortForecast="snow"
                else:
                    get_shortForecast="sunny"
                send_data.append({"startTime":startTime,"temperature":temperature,"shortForecast":shortForecast,"get_shortForecast":get_shortForecast,"relativeHumidity":relativeHumidity,"windSpeed":windSpeed,
                                  "forecastZone":forecastZone,"forecast_hourly_api":forecast_hourly_api})
    return send_data


def generate_image(climate_report):
    response = openai.Image.create(
    prompt=climate_report,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']

    # # Generate filename with current date and time
    # current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"image_{current_datetime}.jpg"
    # media_folder = settings.MEDIA_ROOT + '/' + 'chatgpt_img'
    # filepath = os.path.join(media_folder, filename)
    # # Download the image
    # response = requests.get(image_url)
    # response.raise_for_status()
    # # Save the image to the specified path
    # with open(filepath, "wb") as f:
    #     f.write(response.content)
    # return filename
    return image_url

def get_current_time(latitude, longitude):
    obj = TimezoneFinder()
    get_timezone = obj.timezone_at(lng=longitude, lat=latitude)
    # Get the current time in the specified timezone
    current_time = datetime.now(timezone(get_timezone))
    return current_time

def chatGptApi(question):
    generated_text = ''
    response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=question,
    temperature=0.5,
    max_tokens=200,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.5
    )

    if response.choices:
        generated_text = response.choices[0].text
        # def stream_response():
        #     yield f'{generated_text}'
    return generated_text

@login_required()
def digital_crop_consultant(request):
    context = {}
    if 'Grower' in request.user.get_role() and not request.user.is_superuser :
        grower_id = User.objects.get(id=request.user.id).grower.id
        # farm = Farm.objects.filter(grower_id=grower_id)
        field = Field.objects.filter(grower_id=grower_id)
        context['fields'] = field
        
        if request.method == 'POST' :
            field_id = request.POST.get('fieldid')
            if field_id != 'all' :
                get_chat = AssistantApp.objects.filter(user_id=request.user.id).order_by('-asking_datetime')[:10][::-1]
                context['get_chat'] = get_chat
                context['selectedField'] = Field.objects.get(id=field_id)
                shapfile = ShapeFileDataCo.objects.filter(field_id=field_id)
                # Field Loction Taking From ShapFile
                if shapfile.exists():
                    lat_lon = [i.coordinates for i in shapfile][0][0]
                    lat = lat_lon[0]
                    lon = lat_lon[1]
                # Field Loction Taking From Field Model Latitude and Longitude
                else:
                    lat = context['selectedField'].latitude
                    lon = context['selectedField'].longitude

                current_time = get_current_time(lat, lon)
                f_climate_current = get_climate_report_current(lat, lon)
                try:
                    f_climate_forecast = get_climate_report_forecast(lat, lon)
                except:
                    f_climate_forecast = []
                
                # Extract only Time from the given time
                given_time = f"{current_time}"
                time_obj = datetime.strptime(given_time, "%Y-%m-%d %H:%M:%S.%f%z")
                time_in_am_pm = time_obj.strftime('%I:%M:%S %p')
                weather_description = f_climate_current[0]['f_description']

                # climate_img = generate_image(f'Generate an image of {weather_description}')
                climate_img = generate_image(f'Generate an image of {weather_description}, time is {time_in_am_pm}.')
                context['f_climate_current'] = f_climate_current
                
                forecast_lst = []
                for i in f_climate_forecast :
                    startTime, temperature, get_shortForecast = i["startTime"], i["temperature"], i["get_shortForecast"]
                    relativeHumidity,shortForecast = i["relativeHumidity"], i["shortForecast"]
                    # spt = startTime.split('T')
                    # var_date, var_time = spt[0], spt[1]
                    # spt_var_date = var_date.split('-')
                    # yyyy, mm, dd = int(spt_var_date[0]), int(spt_var_date[1]), int(spt_var_date[2])
                    # spt_var_time = var_time.split(':')
                    # t1,t2 = int(spt_var_time[0]), int(spt_var_time[1])
                    # f_temperature =round(float(i["temperature"]), 2) 
                    # c_temperature = round((5/9) * (f_temperature-32)) math.ceil(float(wind))
                    temperature_Celsius = math.ceil(round((5/9) * (round(float(temperature),2)-32)))
                    var_windSpeed = i["windSpeed"].split(" ")
                    windSpeed = var_windSpeed[0]
                    # forecast_lst.append({"yyyy":yyyy,"mm":mm,"dd":dd,"t1":t1,"t2":t2, "startTime":startTime, "temperature":temperature,"get_shortForecast":get_shortForecast,"shortForecast":shortForecast,"relativeHumidity":relativeHumidity,"windSpeed":windSpeed})
                    forecast_lst.append({"startTime":startTime, "temperature":temperature,"temperature_Celsius":temperature_Celsius,"get_shortForecast":get_shortForecast,"shortForecast":shortForecast,"relativeHumidity":relativeHumidity,"windSpeed":windSpeed})
                
                context['f_climate_forecast'] = f_climate_forecast
                context['forecast_lst'] = forecast_lst
                                
                context['climate_img'] = climate_img
                context['current_time'] = current_time
                # f_loc = location_details(lat,lon)
                # context['f_loc'] = f_loc
                try:
                    f_loc = location_details(lat,lon)
                    context['f_loc'] = f_loc
                except:
                    pass
                try:
                    context['f_county'] = f_loc['county']
                except:
                    pass
                try:
                    context['f_state'] = f_loc['state']
                except:
                    pass
                try:
                    context['f_country'] = f_loc['country']
                except:
                    pass
                try:
                    context['f_postcode'] = f_loc['postcode']
                except:
                    pass
                
                context['f_crop'] = context['selectedField'].crop
                context['f_acreage'] = context['selectedField'].acreage
                context['f_variety'] = context['selectedField'].variety
                context['f_previous_crop'] = context['selectedField'].previous_crop.upper() if context['selectedField'].previous_crop else None

                context['f_fsa_farm_number'] = context['selectedField'].fsa_farm_number
                context['f_fsa_tract_number'] = context['selectedField'].fsa_tract_number
                context['f_fsa_field_number'] = context['selectedField'].fsa_field_number
                context['f_eschlon_id'] = context['selectedField'].eschlon_id
                    
            else :
                pass
        
        return render(request,"assistantapp/digital_crop_consutant.html",context)
    else:
        return redirect('/')

@login_required()
def digital_crop_consultant_chatgpt(request):
    ans = ''
    if 'Grower' in request.user.get_role() and not request.user.is_superuser:
        # if request.method == 'GET':
        ans = ''
        get_user = User.objects.get(id=request.user.id)
        user_name = f"{get_user.first_name} {get_user.last_name}"
        questionText = request.GET.get('questionText')
        if questionText and len(questionText) > 0 and get_user:
            ans = chatGptApi(questionText)
            save_qus_ans = AssistantApp(user_id=request.user.id,user_name=user_name,user_role='Grower',question=questionText,answer=ans)
            save_qus_ans.save()
            return StreamingHttpResponse(ans, content_type='text/event-stream')
    else:
        pass
    
    return JsonResponse ({"ans":ans})

@login_required()
def weather_section_outline(request):
    context = {}
    try:
        context["growers"] = Grower.objects.all().order_by("name")
        if request.method == 'POST' :
            growerSelction = request.POST.get('growerSelction')
            fieldSelction = request.POST.get('fieldSelction')
            if growerSelction and growerSelction !="" :
                check_grower = Grower.objects.filter(id=growerSelction)
                if check_grower.exists():
                    get_grower = check_grower.first()
                    context["selectedGrower"]  = get_grower
                    context["fields"]  = Field.objects.filter(grower_id=get_grower.id)
                    if fieldSelction and fieldSelction !="" :
                        check_field = context["fields"].filter(id=fieldSelction)
                        if check_field.exists():
                            get_field = check_field.first()
                            context["selectedField"] = get_field
                            shapfile = ShapeFileDataCo.objects.filter(field_id=get_field.id)
                            # Field Loction Taking From ShapFile
                            if shapfile.exists():
                                lat_lon = [i.coordinates for i in shapfile][0][0]
                                lat = lat_lon[0]
                                lon = lat_lon[1]
                            # Field Loction Taking From Field Model Latitude and Longitude
                            else:
                                lat = context['selectedField'].latitude
                                lon = context['selectedField'].longitude

                            context['latitude'] = lat
                            context['longitude'] = lon
                            f_climate_current = get_climate_report_current(lat, lon)
                            context['f_climate_current'] = f_climate_current[0]
                            
                            if "cloudy" in context['f_climate_current']['f_description'] :
                                get_currentForecast="cloudy"
                            elif "fog" in context['f_climate_current']['f_description'] :
                                get_currentForecast="cloudy"
                            elif "sunny" in context['f_climate_current']['f_description'] :
                                get_currentForecast="sunny"
                            elif "clear" in context['f_climate_current']['f_description'] :
                                get_currentForecast="sunny"
                            elif "rainy" in context['f_climate_current']['f_description'] :
                                get_currentForecast="rainy"
                            elif "rain" in context['f_climate_current']['f_description'] :
                                get_currentForecast="rainy"
                            elif "snow" in context['f_climate_current']['f_description'] :
                                get_currentForecast="snow"
                            else:
                                get_currentForecast="sunny" 
                            context['f_climate_current']['f_get_currentForecast'] = get_currentForecast
                            try:
                                f_loc = location_details(lat,lon)
                                context['f_loc'] = f_loc
                            except:
                                pass
                            try:
                                context['f_county'] = f_loc['county']
                            except:
                                pass
                            try:
                                context['f_state'] = f_loc['state']
                            except:
                                pass
                            try:
                                context['f_country'] = f_loc['country']
                            except:
                                pass
                            try:
                                context['f_postcode'] = f_loc['postcode']
                            except:
                                pass
                            state_code = str(f_loc['ISO3166-2-lvl4']).split("-")   
                            try:
                                state_code = str(f_loc['ISO3166-2-lvl4']).split("-")[1]
                                context['state_code'] = state_code
                            except:
                                state_code = 'GA'
                                context['f_state'] = 'Atlanta'
                                context['state_code'] = state_code
                            time.sleep(1)
                            forecast_data = get_climate_report_forecast(lat,lon)
                            
                            time.sleep(1)
                            # alerts_url = requests.get(f"https://api.weather.gov/alerts/active?area={state_code}").json()
                            # time.sleep(1)

                            forecastZone = forecast_data[0]["forecastZone"]
                            forecast_hourly_api = forecast_data[0]["forecast_hourly_api"]
                            
                            alerts_url2 = requests.get(f"https://api.weather.gov/alerts/active/zone/{forecastZone}")
                            time.sleep(1)
                            forecast_hourly_url3 = requests.get(f"{forecast_hourly_api}")
                            # alerts_url2 = requests.get(f"https://api.weather.gov/alerts/active/zone/FLZ141")
                            
                            if alerts_url2.status_code == 200 :
                                alerts_url2 = alerts_url2.json()
                                context["alerts_data_title"] = alerts_url2['title']
                                alerts_data = []
                                if len(alerts_url2['features']) > 0:
                                    for i in alerts_url2['features'] :
                                        alerts_data.append({"headline":i['properties']['headline'],
                                        "description":i['properties']['description'],
                                        "areaDesc":i['properties']['instruction']})
                                    context["alerts_data"] = alerts_data
                                else:
                                    context["alerts_data"] = {}
                            
                            
                            if forecast_hourly_url3.status_code == 200 :
                                forecast_hourly_url3 = forecast_hourly_url3.json()
                                url3_properties_periods =forecast_hourly_url3["properties"]["periods"] 
                                result_url3 = {}
                                for url3 in url3_properties_periods:
                                    start_times = datetime.fromisoformat(url3['startTime'][:-6])
                                    days = start_times.strftime('%A')

                                    # Convert the string to a datetime object
                                    original_datetime_obj = datetime.strptime(str(start_times), "%Y-%m-%d %H:%M:%S")
                                    # Get the desired format
                                    formatted_date = original_datetime_obj.strftime("%d %b %Y at %I %p")
                                    # cal wind speed
                                    windSpeed_values = 0
                                    raw_windSpeeds = str(url3["windSpeed"]).replace("mph","").split(" ")
                                    try:
                                        raw_windSpeeds = str(url3["windSpeed"]).replace("mph","").split(" ")
                                        elements_to_removes = ["", "to"]
                                        updated_raw_windSpeeds = [d for d in raw_windSpeeds if d not in elements_to_removes]
                                        if len(updated_raw_windSpeeds) == 1 :
                                            windSpeed_values = int(updated_raw_windSpeeds[0])
                                        else:
                                            w11 = updated_raw_windSpeeds[0]
                                            w22 = updated_raw_windSpeeds[1]
                                            windSpeed_values = round((int(w11) + int(w22)) / 2,2)
                                    except:
                                        pass
                                    
                                    
                                    shortForecast = url3['shortForecast']
                                    try:
                                        if "Cloudy" in shortForecast :
                                            get_shortForecast="cloudy"
                                        elif "Fog" in shortForecast :
                                            get_shortForecast="cloudy"
                                        elif "Sunny" in shortForecast :
                                            get_shortForecast="sunny"
                                        elif "Clear" in shortForecast :
                                            get_shortForecast="sunny"
                                        elif "Rainy" in shortForecast :
                                            get_shortForecast="rainy"
                                        elif "Rain" in shortForecast :
                                            get_shortForecast="rainy"
                                        elif "Snow" in shortForecast :
                                            get_shortForecast="snow"
                                        else:
                                            get_shortForecast="sunny"
                                    except:
                                        get_shortForecast="sunny"

                                    if days not in result_url3:
                                        result_url3[days] = {
                                            "day": days,
                                            "temperatures": [url3['temperature']],
                                            # "get_shortForecast": [url3['shortForecast']],
                                            "get_shortForecast": [get_shortForecast],
                                            "relativeHumidity": [url3['relativeHumidity']['value']],
                                            "windSpeed_values": [windSpeed_values],
                                            "formatted_date":[formatted_date],
                                        }
                                    else:
                                        result_url3[days]["temperatures"].append(url3['temperature'])
                                        # result_url3[days]["get_shortForecast"].append(url3['shortForecast'])
                                        result_url3[days]["get_shortForecast"].append(get_shortForecast)
                                        result_url3[days]["relativeHumidity"].append(url3['relativeHumidity']['value'])
                                        result_url3[days]["windSpeed_values"].append(windSpeed_values)
                                        result_url3[days]["formatted_date"].append(formatted_date)
                                
                                # Convert dictionary to a list of dictionaries
                                combined_data = []
                                if len(result_url3) > 0 :
                                    result_url3 = [value for key, value in result_url3.items()]
                                    for item in result_url3:
                                        combined_data.append({
                                            'day': item['day'],
                                            'data_points': [
                                                {'temperature': temp, 'get_shortForecast': forecast, 'relativeHumidity': humidity, 'windSpeed': wind,'formatted_date':formatted_date}
                                                for temp, forecast, humidity, wind, formatted_date in zip(item['temperatures'], item['get_shortForecast'], item['relativeHumidity'], item['windSpeed_values'], item['formatted_date'])
                                            ]
                                        })                                    
                                    # print("combined_data....",combined_data)
                                context["result_url3"] = result_url3
                                context["combined_data"] = combined_data
                                # print("forecast_hourly_url3  day...............",combined_data)
                            # if alerts_url2.response  PZZ535

                            # event = []
                            # alerts_data = []
                            # for i in alerts_url['features'] :
                            #     alerts_data.append({"headline":i['properties']['headline'],
                            #     "description":i['properties']['description'],
                            #     "areaDesc":i['properties']['areaDesc']})
                            #     event.append(i['properties']['event'])

                            # context["alerts_data"] = alerts_data
                            # context["alerts_data_title"] = alerts_url['title']
                            # context["alerts_data_event"] = event[0]
                            # context['f_climate_current'] = forecast_data[0]
                            '''forecast_data'''
                            result = {}
                            for entry in forecast_data:
                                start_time = datetime.fromisoformat(entry['startTime'][:-6])
                                day = start_time.strftime('%A')

                                # If the day is not already in the result, add it f_climate_current
                                if day not in result:
                                    # cal wind speed
                                    windSpeed_value = 0
                                    raw_windSpeed = str(entry["windSpeed"]).replace("mph","").split(" ")
                                    try:
                                        raw_windSpeed = str(entry["windSpeed"]).replace("mph","").split(" ")
                                        elements_to_remove = ["", "to"]
                                        updated_raw_windSpeed = [x for x in raw_windSpeed if x not in elements_to_remove]
                                        if len(updated_raw_windSpeed) == 1 :
                                            windSpeed_value = int(updated_raw_windSpeed[0])
                                        else:
                                            w1 = updated_raw_windSpeed[0]
                                            w2 = updated_raw_windSpeed[1]
                                            windSpeed_value = round((int(w1) + int(w2)) / 2,2)
                                    except:
                                        pass
                                    
                                    result[day] = {
                                        "day": day,
                                        "max_temp": entry['temperature'],
                                        "min_temp": entry['temperature'],
                                        "get_shortForecast": entry['get_shortForecast'],
                                        "shortForecast":entry["shortForecast"],
                                        "relativeHumidity":entry["relativeHumidity"],
                                        "windSpeed":entry["windSpeed"],
                                        "windSpeed_value": windSpeed_value,
                                    }
                                else:
                                    # Update max and min temperatures if needed
                                    result[day]['max_temp'] = max(result[day]['max_temp'], entry['temperature'])
                                    result[day]['min_temp'] = min(result[day]['min_temp'], entry['temperature'])
                            '''Radar section'''
                            time.sleep(1)
                            # main_text = {"agenda":{"id":"weather","center":[lon,lat],"location":[lon,lat],"zoom":5},"animating":False,"base":"standard","artcc":False,"county":False,"cwa":False,"rfc":False,"state":False,"menu":False,"shortFusedOnly":False,"opacity":{"alerts":0.8,"local":0.6,"localStations":0.8,"national":0.6}}
                            main_text = {"agenda":{"id":"weather","center":[lon,lat],"location":[lon,lat],"zoom":5,"layer":"bref_qcd"},"animating":False,"base":"standard","artcc":False,"county":False,"cwa":False,"rfc":False,"state":False,"menu":True,"shortFusedOnly":True,"opacity":{"alerts":0.8,"local":0.6,"localStations":0.8,"national":0.6}}
                            
                            import json
                            json_data = json.dumps(main_text)
                            str_json_data = str(json_data).replace(" ","")
                            import base64
                            encoded_text = base64.b64encode(str_json_data.encode('utf-8')).decode('utf-8')
                            rader_url_format = f"https://radar.weather.gov/?settings=v1_{encoded_text}"   
                                                
                            context['rader_url_format'] = rader_url_format
                            context['result_forecast_data'] = list(result.values())
    except Exception as e:
        context["error_msg"] = "Latitiude and Longitude not found"
        
    return render(request,"assistantapp/weather_section_outline.html",context)