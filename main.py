from flask import Flask, render_template, request
from pymongo import MongoClient
import requests
import matplotlib.pyplot as plt
from datetime import datetime 


app = Flask(__name__)
# api_key

api_key = 'ab5dde60f7824f56a11103549231112'
# connexion a MongoDB:
client = MongoClient('mongodb://localhost:27017/')
db = client['weather_db']
collection = db['weather_collection']

# Création d'application 
@app.route("/")
def index():
    return render_template('index.html', title= "Weather", style='index')
@app.route('/about')
def about():
    return render_template('about.html', title='About', style='about')

# ------------========--------------------------
def fetch_data_from_api(city):
        url = f'https://api.weatherapi.com/v1/forecast.json?q={city}&key={api_key}&days=7'
        response = requests.get(url)
        return response.json()

def error_city_not_exist(data):
    if 'error' in data:
        error_message = f'Error: {data["error"]["message"]}'
        return True, render_template('index.html', error_message=error_message, style="index")
    return False, None
    
def insert_data_into_mongodb(city, data):
        collection.delete_many({'city': city})
        data_to_insert = {
                'city' : city,
                'api_response' : data
            }
        # insert the data into mongoDB
        collection.insert_one(data_to_insert)




def generate_plot(city):
    weather_data = list(collection.find({'city': city},{"_id":0}))
    humidity =[day['day']['avghumidity'] for day in weather_data[0]['api_response']['forecast']['forecastday']]
    max_temperature_week = [week['day']['maxtemp_c'] for week in weather_data[0]['api_response']['forecast']['forecastday']]
    min_temperature_week = [week['day']['mintemp_c'] for week in weather_data[0]['api_response']['forecast']['forecastday']]
    temperature_hour = [hour['temp_c'] for hour in weather_data[0]['api_response']['forecast']['forecastday'][0]['hour']]
    timestamp = [hour['time_epoch'] for hour in weather_data[0]['api_response']['forecast']['forecastday'][0]['hour']]
    time = [datetime.utcfromtimestamp(ts).strftime('%H:%M') for ts in timestamp]
    day = [day['date'] for day in weather_data[0]['api_response']['forecast']['forecastday']]


    # print(len(temperature_hour))
    # print(len(timestamp))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
    fig.set_facecolor('#e7e7e7')

    # Plotting humidity
    ax1.plot(day, humidity, color='r', label='Humidity')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Humidity')
    ax1.legend()

    # Plotting temperature
    ax2.plot(time, temperature_hour, color='b', label='Temperature')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Temperature')
    ax2.set_title('Forecast for today')
    ax2.legend()

    # Plotting min and max temperature over time
    ax3.plot(day, max_temperature_week, color='y', label='Temperature Max')
    ax3.plot(day, min_temperature_week, color='g', label='Temperature Min')
    ax3.set_xlabel('Day')
    ax3.set_ylabel('Temperature')
    ax3.legend()

    # Save the plot to an image file
    plt.savefig('static/forecast_plot.png')
    return 'static/forecast_plot.png'
     
@app.route('/', methods=['POST'])
def search():
    if request.method == "POST":
        city = request.form['city'].lower()
        data = fetch_data_from_api(city)
        # clear existing city
        # collection.delete_many({'city': city})
        has_error, error_template = error_city_not_exist(data)
        if has_error:
            return error_template
        insert_data_into_mongodb(city, data)

        weather_data = list(collection.find({'city': city},{"_id":0}))

        generate_plot(city)





    return render_template('index.html', title="Search",  data=weather_data, style='index', image='static/forecast_plot.png', now=datetime.now())


if __name__ == '__main__':
    app.run(debug=True)
