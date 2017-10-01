from database import db

from sqlalchemy import PrimaryKeyConstraint


"""
Note: See README for detailed explanation of why this table structure was
chosen
"""


class DailyWeatherStationTS(db.Model):
    """Each row represents a datapoint in the tmax/tmin timeseries"""
    __tablename__ = 'daily_weather_station_ts'
    __table_args__ = (
        PrimaryKeyConstraint('station_id', 'date', name='timeseries_pk'),
        {'mysql_engine': 'InnoDB'})

    station_id = db.Column(db.Integer, db.ForeignKey('weather_station.id'),
                           nullable=False)
    date = db.Column(db.Date, nullable=False)
    tmax = db.Column(db.Float)
    tmin = db.Column(db.Float)


class WeatherStation(db.Model):
    """Each row represents a single weather station"""
    __tablename__ = 'weather_station'

    id = db.Column(db.Integer, primary_key=True)
    external_station_id = db.Column(db.String(255), unique=True,
                                    nullable=False)
    name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elevation = db.Column(db.Float)
    timeseries = db.relationship('DailyWeatherStationTS', backref='station',
                                 lazy=True)

    def to_dict(self):
        """Return a dict representation of self"""
        return dict(id=self.id,
                    external_station_id=self.external_station_id,
                    name=self.name,
                    latitude=self.latitude,
                    longitude=self.longitude,
                    elevation=self.elevation)
