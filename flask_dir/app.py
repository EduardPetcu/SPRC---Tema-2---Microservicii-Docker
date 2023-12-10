from flask import Flask, Blueprint, request, jsonify, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
from os import environ
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
db = SQLAlchemy(app)
payload_country_keys = ['id', 'nume', 'lat', 'lon']
payload_city_keys = ['id', 'nume', 'lat', 'lon', 'idTara']

'''
Tari reprezinta schema tabelului Tari din baza de date
Am folosit autoincrement pentru id, iar pentru nume am folosit unique=True
De asemenea, am folosit cascade="all,delete" pentru a sterge si orasele din tara respectiva
'''
class Tari(db.Model):
    __tablename__ = 'Tari'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    nume = db.Column(db.String(100), nullable=False, unique=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    orase = db.relationship('Orase', cascade="all,delete")
    def json(self):
        return {"id": self.id, "nume": self.nume, "lat": self.lat, "lon": self.lon}

'''
Orase reprezinta schema tabelului Orase din baza de date
Am folosit autoincrement pentru id, iar pentru constrangerea de unicitate am 
folosit UniqueConstraint intre idTara si nume De asemenea, am folosit 
cascade="all,delete" pentru a sterge si temperaturile din orasul respectiv
'''
class Orase(db.Model):
    __tablename__ = 'Orase'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    idTara = db.Column(db.Integer, db.ForeignKey('Tari.id', ondelete='CASCADE'), nullable=False)
    nume = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    temp = db.relationship('Temperaturi', cascade="all,delete")
    __table_args__ = (db.UniqueConstraint('idTara', 'nume', name='unique_tara_nume'),)

    def json(self):
        return {"id": self.id, "nume": self.nume, "lat": self.lat, "lon": self.lon, "idTara": self.idTara}
    
'''
Temperaturi reprezinta schema tabelului Temperaturi din baza de date
Am folosit autoincrement pentru id, iar pentru constrangerea de unicitate 
am folosit UniqueConstraint. 
Timestamp este de tip DateTime si se pune automat prin flag-ul default=func.now()
func reprezentand o functie din sqlalchemy care returneaza data curenta cu 
precizie de 1 microsecunda Afisarea temperaturii se face in formatul YYYY-MM-DD 
prin functia strftime din datetime
'''
class Temperaturi(db.Model):
    __tablename__ = 'Temperaturi'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    idOras = db.Column(db.Integer, db.ForeignKey('Orase.id', ondelete='CASCADE'), nullable=False)
    valoare = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=func.now())
    __table_args__ = (db.UniqueConstraint('idOras', 'timestamp', name='unique_oras_timestamp'),)

    def json(self):
        return {"id": self.id, "valoare": self.valoare, "timestamp": self.timestamp.strftime("%Y-%m-%d")}

'''
Returneaza o lista pe baza filtrelor date ca parametrii
'''
def get_filters(lat, lon, from_date, until_date):
    filter_list = []
    if lat is not None:
        lat = float(lat)
        filter_list.append(Orase.lat==lat)
    if lon is not None:
        lon = float(lon)
        filter_list.append(Orase.lon==lon)
    
    if from_date is not None:
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        filter_list.append(Temperaturi.timestamp>=from_date)

    if until_date is not None:
        until_date = datetime.datetime.strptime(until_date, '%Y-%m-%d')
        filter_list.append(Temperaturi.timestamp<=until_date)
    return filter_list

# creaza tabelele in baza de date
db.create_all()

@app.route("/api/countries", methods=['POST'])
def create_country():
    try: 
        payload = request.get_json(silent=True)
        # verificam daca campurile exista
        for key in payload_country_keys:
            if key not in payload and key != 'id':
                return make_response(jsonify({'error': 'Campuri invalide!'}), 400)
        # verificam daca campurile sunt de tipul asteptat
        if not(
            isinstance(payload['lat'], (int, float)) and 
            isinstance(payload['lon'], (int, float)) and 
            type(payload['nume']) is str
        ):
            return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
        # convertim lat si lon la float in cazul in care sunt int
        lat_country = float(payload['lat'])
        lon_country = float(payload['lon'])
        # verificam daca tara exista deja
        countries = Tari.query.filter_by(nume=payload['nume'])
        if countries.count() > 0:
            return make_response(jsonify({'error': 'Tara exista deja!'}), 409)
        # cream tara
        new_country = Tari(nume=payload['nume'], lat=lat_country, lon=lon_country)
        db.session.add(new_country)
        db.session.commit()
        return make_response(jsonify({'id': new_country.id}), 201)
    except:
        return make_response(jsonify({'error': 'Eroare la crearea tarii'}), 500)
    
@app.route("/api/countries", methods=['GET'])
def get_countries():
    try:
        countries = Tari.query.all()
        return make_response(jsonify([country.json() for country in countries]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea tarilor'}), 500)

@app.route("/api/countries/<int:id>", methods=['PUT'])
def update_country(id):
    try:
        country = Tari.query.filter_by(id=id).first()
        if country: 
            payload = request.get_json(silent=True)
            # verificam daca campurile exista
            for key in payload_country_keys:
                if key not in payload:
                    return make_response(jsonify({'error': 'Campuri invalide'}), 400)
            # verificam daca campurile sunt de tipul asteptat
            if not (
                isinstance(payload['lat'], (int, float)) and 
                isinstance(payload['lon'], (int, float)) and 
                type(payload['nume']) is str and 
                type(payload['id']) is int):
                return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
            payload['lat'] = float(payload['lat'])
            payload['lon'] = float(payload['lon'])
            # verificam daca tara exista deja
            countries = Tari.query.filter_by(nume=payload['nume'])
            if countries.count() > 0:
                return make_response(jsonify({'error': 'Tara exista deja'}), 409)
            for key in payload_country_keys:
                setattr(country, key, payload[key])
            db.session.commit()
            return make_response(jsonify({'message': 'Tara a fost actualizata'}), 200)
        return make_response(jsonify({'error': 'Tara nu a fost gasita'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la update'}), 500)

@app.route("/api/countries/<int:id>", methods=['DELETE'])
def delete_country(id):
    try:
        country = Tari.query.filter_by(id=id).first()
        if country:
            db.session.delete(country)
            db.session.commit()
            return make_response(jsonify({'message': 'Tara a fost stearsa'}), 200)
        return make_response(jsonify({'error': 'Tara nu a fost gasita'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la delete'}), 500)

@app.route("/api/cities", methods=['POST'])
def create_city():
    try: 
        payload = request.get_json(silent=True)
        for key in payload_city_keys:
            if key not in payload and key != 'id':
                return make_response(jsonify({'error': 'Campuri invalide'}), 400)
        if not (
            isinstance(payload['lat'], (int, float)) and 
            isinstance(payload['lon'], (int, float)) and 
            type(payload['nume']) is str and 
            type(payload['idTara']) is int):
            return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
        countries = Tari.query.filter_by(id=payload['idTara'])
        if countries.count() == 0:
            return make_response(jsonify({'error': 'Tara nu exista'}), 404)
        cities = Orase.query.filter_by(idTara=payload['idTara'], nume=payload['nume'])
        if cities.count() > 0:
            return make_response(jsonify({'error': 'Orasul exista deja'}), 409)
        lat_city = float(payload['lat'])
        lon_city = float(payload['lon'])
        new_city = Orase(idTara=payload['idTara'], nume=payload['nume'], lat=lat_city, lon=lon_city)
        db.session.add(new_city)
        db.session.commit()
        return make_response(jsonify({'id': new_city.id}), 201)
    except:
        return make_response(jsonify({'error': 'Eroare la crearea tarii'}), 500)

@app.route("/api/cities", methods=['GET'])
def get_cities():
    try:
        cities = Orase.query.all()
        return make_response(jsonify([city.json() for city in cities]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea tarilor'}), 500)

@app.route("/api/cities/country/<int:id>", methods=['GET'])
def get_city_by_countryid(id):
    try:
        cities = Orase.query.filter_by(idTara=id).all()
        return make_response(jsonify([city.json() for city in cities]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea tarilor'}), 500)

@app.route("/api/cities/<int:id>", methods=['PUT'])
def update_city(id):
    try:
        city = Orase.query.filter_by(id=id).first()
        if city: 
            payload = request.get_json(silent=True)
            for key in payload_city_keys:
                if key not in payload:
                    return make_response(jsonify({'error': 'Campuri invalide'}), 400)
            if not (
                isinstance(payload['lat'], (int, float)) and 
                isinstance(payload['lon'], (int, float)) and 
                type(payload['nume']) is str and 
                type(payload['idTara']) is int and 
                type(payload['id']) is int):
                return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
            orase = Orase.query.filter_by(nume=payload['nume'])
            if orase.count() > 0:
                return make_response(jsonify({'error': 'Orasul exista deja'}), 409)
            
            for key in payload_city_keys:
                if key in payload:
                    setattr(city, key, payload[key])
            db.session.commit()
            return make_response(jsonify({'message': 'Orasul a fost actualizat!'}), 200)
        return make_response(jsonify({'error': 'Orasul nu a fost gasit!'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la update'}), 500)
    
@app.route("/api/cities/<int:id>", methods=['DELETE'])
def delete_city(id):
    try:
        city = Orase.query.filter_by(id=id).first()
        if city:
            db.session.delete(city)
            db.session.commit()
            return make_response(jsonify({'message': 'Orasul a fost sters!'}), 200)
        return make_response(jsonify({'error': 'Orasul nu a fost gasit!'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la delete'}), 500)

@app.route("/api/temperatures", methods=['POST'])
def add_temperature():
    try:
        payload = request.get_json(silent=True)
        if 'idOras' not in payload:
            return make_response(jsonify({'error': 'Orasul nu poate fi null'}), 400)
        if 'valoare' not in payload:
            return make_response(jsonify({'error': 'Valoarea nu poate fi null'}), 400)
        if not (
            type(payload['idOras']) is int and
            isinstance(payload['valoare'], (int, float))
        ):
            return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
        cities = Orase.query.filter_by(id=payload['idOras'])
        if cities.count() == 0:
            return make_response(jsonify({'error': 'Orasul nu exista'}), 404)
        new_temperature = Temperaturi(idOras=payload['idOras'], valoare=payload['valoare'])
        db.session.add(new_temperature)
        db.session.commit()
        return make_response(jsonify({'id': new_temperature.id}), 201)
    except:
        return make_response(jsonify({'error': 'Eroare la crearea temperaturii'}), 500)

@app.route("/api/temperatures", methods=['GET'])
def get_temperatures_by_filters():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        from_date = request.args.get('from')
        until_date = request.args.get('until')
        filter_list = get_filters(lat, lon, from_date, until_date)
            
        temperatures = Temperaturi.query.join(Orase).filter(and_(*filter_list)).all()
        return make_response(jsonify([temperature.json() for temperature in temperatures]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea temperaturilor'}), 500)

@app.route("/api/temperatures/cities/<int:id>", methods=['GET'])
def get_temperature_by_cityid(id):
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        from_date = request.args.get('from')
        until_date = request.args.get('until')
        filter_list = get_filters(lat, lon, from_date, until_date)

        filter_list.append(Temperaturi.idOras==id)
        temperatures = Temperaturi.query.join(Orase).filter(and_(*filter_list)).all()
        return make_response(jsonify([temperature.json() for temperature in temperatures]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea temperaturii'}), 500)

@app.route("/api/temperatures/countries/<int:id>", methods=['GET'])
def get_temperature_by_countryid(id):
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        from_date = request.args.get('from')
        until_date = request.args.get('until')
        filter_list = get_filters(lat, lon, from_date, until_date)

        filter_list.append(Orase.idTara==id)
        temperatures = Temperaturi.query.join(Orase).filter(and_(*filter_list)).all()
        return make_response(jsonify([temperature.json() for temperature in temperatures]), 200)
    except:
        return make_response(jsonify({'error': 'Eroare la preluarea temperaturii'}), 500)
    
@app.route("/api/temperatures/<int:id>", methods=['PUT'])
def update_temperature(id):
    try:
        temperature = Temperaturi.query.filter_by(id=id).first()
        if temperature: 
            payload = request.get_json(silent=True)
            if 'valoare' not in payload:
                return make_response(jsonify({'error': 'Valoarea nu poate fi null'}), 400)
            if 'idOras' not in payload:
                return make_response(jsonify({'error': 'Orasul nu poate fi null'}), 400)
            
            if not (
                type(payload['idOras']) is int and
                isinstance(payload['valoare'], (int, float))
            ):
                return make_response(jsonify({'error': 'Campurile nu respecta formatul admis'}), 400)
            temperature.valoare = payload['valoare']
            temperature.idOras = payload['idOras']
            db.session.commit()
            return make_response(jsonify({'message': 'Temperatura a fost adaugata'}), 200)
        return make_response(jsonify({'error': 'Temperatura nu a fost gasita'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la update'}), 500)
    
@app.route("/api/temperatures/<int:id>", methods=['DELETE'])
def delete_temperature(id):
    try:
        temperature = Temperaturi.query.filter_by(id=id).first()
        if temperature:
            db.session.delete(temperature)
            db.session.commit()
            return make_response(jsonify({'message': 'Temperatura a fost stearsa'}), 200)
        return make_response(jsonify({'error': 'Temperatura nu a fost gasita'}), 404)
    except:
        return make_response(jsonify({'error': 'Eroare la delete'}), 500)
