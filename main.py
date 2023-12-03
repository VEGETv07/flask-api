from flask import Flask, render_template, request
from pymongo import MongoClient
import requests
import matplotlib.pyplot as plt


app = Flask(__name__)
# api_key
# https://api.weatherapi.com/v1/forecast.json?q=agadir&key=db36df6e32e943a8b65204853233011
api_key = 'db36df6e32e943a8b65204853233011'
# connexion a MongoDB:
client = MongoClient('mongodb://localhost:27017/')
db = client['weather_db']
collection = db['weather_collection']
# Création d'une application web avec Flask
@app.route("/")
def index():
    return render_template('index.html', title= "Weather", style='forecast')

@app.route('/search', methods=['POST'])
def search():
    if request.method == "POST":
        city = request.form['city']
        url = f'https://api.weatherapi.com/v1/forecast.json?q={city}&key={api_key}&days=7'

        response = requests.get(url)
        data = response.json()
        # clear existing city
        collection.delete_many({'city': city})
        data_to_insert = {
                'city' : city,
                'api_response' : data
            }
        # insert the data into mongoDB
        collection.insert_one(data_to_insert)

        ddd = request.form.get('city')
        weather_data = list(collection.find({'city': ddd},{"_id":0}))

        humidity =[day['day']['avghumidity'] for day in weather_data[0]['api_response']['forecast']['forecastday']]
        max_temperature_week = [week['day']['maxtemp_c'] for week in weather_data[0]['api_response']['forecast']['forecastday']]
        min_temperature_week = [week['day']['mintemp_c'] for week in weather_data[0]['api_response']['forecast']['forecastday']]
        temperature_hour = [hour['temp_c'] for day in weather_data[0]['api_response']['forecast']['forecastday'] if 'hour' in day for hour in day['hour']]
        time = [hour['time'] for day in weather_data[0]['api_response']['forecast']['forecastday'] if 'hour' in day for hour in day['hour']]
        day = [day['date'] for day in weather_data[0]['api_response']['forecast']['forecastday']]

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

        # Plotting humidity
        ax1.plot(day, humidity, color='r', label='Humidity')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Humidity')
        ax1.legend()

        # Plotting temperature
        ax2.plot(time, temperature_hour, color='b', label='Temperature')
        ax2.set_xlabel('Day')
        ax2.set_ylabel('Temperature')
        ax2.legend()

        # Plotting min and max temperature over time
        ax3.plot(day, min_temperature_week, color='g', label='Min Temperature')
        ax3.plot(day, max_temperature_week, color='y', label='Max Temperature')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Temperature')
        ax3.legend()

        # Save the plot to an image file
        plt.savefig('static/forecast_plot.png')

    return render_template('index.html', title="Search",  data=weather_data, style='forecast', image='static/forecast_plot.png')


if __name__ == '__main__':
    app.run(debug=True)
