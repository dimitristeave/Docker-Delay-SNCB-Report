from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import threading
from datetime import datetime
import requests
import csv
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sander1234'

# MySQL Database Configuration
db_config = {
    'host': 'mysql_container',
    'user': 'dimi',
    'password': 'dimi',
    'database': 'sncb_docker',
    'port': 3308
}

# Flask-WTF Form Class
class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Function to get database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Function to read and save departure data
def read_and_save_departures(stationfrom):
    # Same code as your Read_per_station function, just removed the while loop
    def read_and_save_departures(stationfrom):
        # Same code as your Read_per_station function, just removed the while loop
        connection = get_db_connection()
        cursor = connection.cursor()
        ddmmyy = datetime.now()
        ddmmyy = ddmmyy.strftime("%d%m%y")
        hhmm = datetime.now()
        hhmm = hhmm.strftime("%H%M")
        # Lien de l'api iRail avec les champs renseignés, les données seront recupérées en JSON
        url = f"https://api.iRail.be/liveboard/?id=&station={stationfrom}&date={ddmmyy}&time={hhmm}&arrdep=departure&lang=en&format=json&alerts=true"
        response = requests.get(url)  # Requete à l'api pour avoir des données de départ de trains

        if response.status_code == 200:  # Réponse favorable renvoyée par une requete http
            departures_data = response.json()  # Recupération en JSON
            departures = departures_data.get("departures", {})
            departure_list = departures.get("departure", [])  # Liste vide par défaut
            for departure in departure_list:
                if int(departure["delay"]) // 60 > 0:
                    delay = int(departure["delay"]) // 60
                    stationend = departure["station"]
                    time_ = datetime.utcfromtimestamp(int(departure["time"]))
                    hour = time_.strftime("%H%M")
                    date = time_.strftime("%d%m")
                    vehicle = departure["vehicle"]
                    platform = departure["platform"]
                    canceled = departure["canceled"]
                    left = departure["left"]
                    departure_connection = departure["departureConnection"]
                    select_query = """
                                   SELECT * FROM departures
                                   WHERE delay = %s AND stationend = %s AND stationfrom = %s AND date = %s AND hour = %s AND vehicle = %s AND platform = %s AND canceled = %s AND `left` = %s AND departure_connection = %s;
                                   """
                    cursor.execute(select_query, (
                        delay, stationend, stationfrom, date, hour, vehicle, platform, canceled, left,
                        departure_connection))
                    existing_departure = cursor.fetchone()
                    if existing_departure is None:
                        insert_query = """
                                       INSERT INTO departures (delay, stationend, stationfrom, date, hour, vehicle, platform, canceled, `left`, departure_connection)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                       """
                        cursor.execute(insert_query, (
                            delay, stationend, stationfrom, date, hour, vehicle, platform, canceled, left,
                            departure_connection))
                    connection.commit()

                print("Données bien sauvegardées dans la base de données MYSQL")
        else:
            print("La requête a échoué avec le code de statut :", response.status_code)
        cursor.close()
        connection.close()

# Route for the main page
@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()

    if form.validate_on_submit():
        # Get the entered login value
        login = form.login.data

        # Check if login is valid (you can customize this part)
        if login == 'mama':
            # Get the list of stations from the CSV file
            csv_file = 'stations.csv'
            stations = []
            with open(csv_file, mode='r', newline='') as file:
                csv_reader_stations = csv.reader(file)
                headers = next(csv_reader_stations)
                name_column = headers.index('name')
                country_column = headers.index('country-code')

                for row_station in csv_reader_stations:
                    if row_station[country_column] == 'be':
                        stations.append(row_station[name_column])

            # Trigger the read_and_save_departures function for each station
            while True:
                for stationfrom in stations:
                    # threading.Thread(target=Read_per_station, args=(stationfrom,)).start()
                    read_and_save_departures(stationfrom)

            return redirect(url_for('index'))

    # Render the login page with the form
    return render_template('login.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
