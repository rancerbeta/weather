from collections import defaultdict
import csv
import datetime

import click
from flask import Flask

from weather.database import db
from weather.views import city
# Import models to allow construction via initdb
from weather.models import DailyWeatherStationTS, WeatherStation # noqa:F401


def register_blueprints(app):
    """Register all blueprints"""
    app.register_blueprint(city.bp, url_prefix='/api/city')


def register_cli(app):
    """Register all CLIs"""
    @app.cli.command()
    def initdb():
        """Create tables"""
        click.echo('Initialized database')
        db.create_all()

    @app.cli.command()
    def loaddb():
        """Create DB objects from weather.csv"""
        click.echo('Loading data from weather.csv')
        with open('weather.csv', 'r') as f:
            reader = csv.reader(f)
            header = reader.next()
            assert header == ['STATION', 'NAME', 'LATITUDE', 'LONGITUDE',
                              'ELEVATION', 'DATE', 'TMAX', 'TMIN']
            stations = set()
            station_to_ts = defaultdict(list)
            for row in reader:
                station_id, name, latitude, longitude, elevation, \
                        date, tmax, tmin = row
                station = (station_id, name, latitude, longitude, elevation)
                stations.add(station)
                station_to_ts[station].append((date, tmax, tmin))

            if WeatherStation.query.all():
                click.echo('There already exist some weather stations. This'
                           'comamnd is not meant to be run multiple times.'
                           'Clear MySQL tables and then run this')

            station_to_id = {}
            for station in stations:
                station_id, name, latitude, longitude, elevation = station
                s = WeatherStation(external_station_id=station_id,
                                   name=name,
                                   latitude=float(latitude),
                                   longitude=float(longitude),
                                   elevation=float(elevation))
                db.session.add(s)
                # Flush to get the IDs for these Weather Stations
                db.session.flush()
                station_to_id[station] = s.id

            for station, ts in station_to_ts.items():
                for day in ts:
                    station_id = station_to_id[station]
                    date, tmax, tmin = day
                    tmax = float(tmax) if tmax else None
                    tmin = float(tmin) if tmin else None
                    dt = datetime.datetime.strptime(date, '%Y-%m-%d')

                    day_object = DailyWeatherStationTS(station_id=station_id,
                                                       date=dt,
                                                       tmax=tmax,
                                                       tmin=tmin)
                    db.session.add(day_object)
                    db.session.flush()
            db.session.commit()
            click.echo('db load complete')


def create_app(config=None):
    app = Flask(__name__)

    app.config.update(dict(
        SQLALCHEMY_DATABASE_URI='mysql+mysqldb://root:@localhost/weather',
        SECRET_KEY=b'SFMZWXOCH8',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    ))
    if config:
        app.config.update(config)

    db.init_app(app)

    register_blueprints(app)
    register_cli(app)

    return app
