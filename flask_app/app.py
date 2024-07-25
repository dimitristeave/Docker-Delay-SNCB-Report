from flask import Flask, jsonify
import pymysql
import mysql.connector
import os
from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sander1234'

def get_db_connection():
    return mysql.connector.connect(host='mysql_container',
                           user='dimi',
                           password='dimi',
                           db='sncb_docker',
                          )

def fetch_departures(stationfrom, stationend, date, choice, hourinf=None, hoursup=None, hour=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if choice == "1":
        select_query = """
            SELECT MAX(delay) AS max_delay, stationend, stationfrom, date, hour, vehicle, platform FROM departures
            WHERE stationend = %s AND stationfrom = %s AND date = %s AND hour > %s AND hour < %s
            GROUP BY stationend, stationfrom, date, hour, vehicle, platform ;
        """
        cursor.execute(select_query, (stationend, stationfrom, date, hourinf, hoursup))
    elif choice == "2":
        select_query = """
            SELECT MAX(delay) AS max_delay, stationend, stationfrom, date, hour, vehicle, platform FROM departures
            WHERE stationend = %s AND stationfrom = %s AND date = %s AND hour = %s
            GROUP BY stationend, stationfrom, date, hour, vehicle, platform ;
        """
        cursor.execute(select_query, (stationend, stationfrom, date, hour))

    return cursor.fetchall()

class DepartureForm(FlaskForm):
    stationfrom = StringField('Station de départ', validators=[DataRequired()])
    stationend = StringField('Station d\'arrivée', validators=[DataRequired()])
    date = StringField('Date de départ', validators=[DataRequired()])
    choice = SelectField('Choix', choices=[('1', 'Période'), ('2', 'Date exacte')], validators=[DataRequired()])
    hourinf = StringField('Heure inférieure')
    hoursup = StringField('Heure supérieure')
    hour = StringField('Heure exacte')
    submit = SubmitField('Rechercher')

def create_departures_pdf(departures):
    pdf_filename = f"departures_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    pdf_path = f"static/{pdf_filename}"
    # Créez un document PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Titre du PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Liste des Départs")

    # Informations de départ
    y = 720  # Position verticale initiale
    vertical_spacing = 140  # Espacement vertical entre les départs
    max_y = 135  # Hauteur maximale avant de créer une nouvelle page
    i = 0
    for departure in departures:
        if y < max_y:  # Créez une nouvelle page si la hauteur est dépassée
            c.showPage()
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "Liste des Départs (suite)")
            y = 720
        i += 1
        c.setFont("Helvetica", 15)
        c.drawString(100, y - 3, f"Departure N°{i}")
        # departure_date = datetime.utcfromtimestamp(departure[3]).strftime("%d/%m")
        # departure_hour = datetime.utcfromtimestamp(departure[4]).strftime("%H:%M")
        c.setFont("Helvetica", 12)
        c.drawString(100, y - 15, f"Delay: {departure[0]} minutes")
        c.drawString(100, y - 30, f"From station: {departure[1]}")
        c.drawString(100, y - 45, f"End station: {departure[2]}")
        c.drawString(100, y - 60, f"Date: {departure[3]}")
        c.drawString(100, y - 75, f"Hour: {departure[4]}")
        c.drawString(100, y - 90, f"Vehicle: {departure[5]}")
        c.drawString(100, y - 105, f"Platform: {departure[6]}")
        y -= vertical_spacing  # Ajout de l'espacement vertical

    # Enregistrez le PDF
    c.save()
    return pdf_filename

@app.route('/', methods=['GET', 'POST'])
def index():
    form = DepartureForm()

    if form.validate_on_submit():
        stationfrom = form.stationfrom.data
        stationend = form.stationend.data
        date = form.date.data
        choice = form.choice.data

        if choice == "1":
            hourinf = form.hourinf.data
            hoursup = form.hoursup.data
            hour=''
        elif choice == "2":
            hour = form.hour.data

        departures = fetch_departures(stationfrom, stationend, date, choice, hourinf, hoursup, hour)

        pdf_filename = create_departures_pdf(departures)

        return render_template('result.html', pdf_filename=pdf_filename)

    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
