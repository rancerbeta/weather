import datetime
import json

from weather.app_factory import create_app
from weather.database import db
from weather.models import DailyWeatherStationTS, WeatherStation
from weather.views.city import convert_f_to_c


ONE_DAY = 86400


class TestWeatherStationStories(object):
    def setup_method(self):
        """Create application and add some objects"""
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://'
        })
        app.testing = True
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

            s = WeatherStation(external_station_id='E123',
                               name='BERKHOUT, NL',
                               latitude=23.0,
                               longitude=24.0,
                               elevation=2.0)
            db.session.add(s)
            db.session.flush()

            self.daily_ts = {}
            base_date = datetime.date(2017, 6, 1)
            day = base_date
            for x in range(10):
                day = day + datetime.timedelta(days=1)
                ts = DailyWeatherStationTS(
                    date=day,
                    tmin=x,
                    tmax=x + 10,
                    station_id=s.id
                )
                self.daily_ts[str(day)] = dict(tmin=x,
                                               tmax=x + 10)
                db.session.add(ts)

            db.session.commit()

    def teardown_method(self):
        """Remove application"""
        with self.app.app_context():
            db.drop_all()

    def test_unit_must_be_provided(self):
        """Make sure that a 400 response is received if no unit provided"""
        test_response = self.client.get('/api/city/chicago')
        assert test_response.status_code == 400
        assert json.loads(test_response.data)['error'] == (
            'Unit must be provided as a URL param and must either be F or C'
        )

    def test_city_in_db_must_be_provided(self):
        """Make sure that a 400 response is received if city not in DB"""
        test_response = self.client.get('/api/city/krypton',
                                        query_string={'unit': 'F'})
        assert test_response.status_code == 400
        assert json.loads(test_response.data)['error'] == (
            'City krypton is not in the DB'
        )

    def test_station_data_returned(self):
        """Make sure station data was sent properly"""
        test_response = self.client.get('/api/city/BERKHOUT, NL',
                                        query_string={'unit': 'F'})
        assert test_response.status_code == 200
        data = json.loads(test_response.data)
        assert data['station'] == dict(id=1,
                                       external_station_id='E123',
                                       name='BERKHOUT, NL',
                                       latitude=23.0,
                                       longitude=24.0,
                                       elevation=2.0)

    def test_daily_data_returned(self):
        """Make sure that the response has all the daily data for a city"""
        test_response = self.client.get('/api/city/BERKHOUT, NL',
                                        query_string={'unit': 'F'})
        assert test_response.status_code == 200
        data = json.loads(test_response.data)
        assert data['data']['daily_ts'] == self.daily_ts

        test_response = self.client.get('/api/city/BERKHOUT, NL',
                                        query_string={'unit': 'C'})
        assert test_response.status_code == 200

    def test_weekly_data_returned(self):
        test_response = self.client.get('/api/city/BERKHOUT, NL',
                                        query_string={'unit': 'F'})
        assert test_response.status_code == 200
        data = json.loads(test_response.data)
        weekly_ts = {u'2017-06-05': {u'tmax': 16.0, u'tmin': 6.0},
                     u'2017-05-29': {u'tmax': 11.0, u'tmin': 1.5}}
        assert data['data']['weekly_ts'] == weekly_ts

    def test_monthly_data_returned(self):
        test_response = self.client.get('/api/city/BERKHOUT, NL',
                                        query_string={'unit': 'F'})
        assert test_response.status_code == 200
        data = json.loads(test_response.data)
        monthly_ts = {u'2017-06-01': {u'tmax': 14.5, u'tmin': 5.0}}
        assert data['data']['monthly_ts'] == monthly_ts

    def test_temp_conversion(self):
        """Test conversion from faherenheit to Celcius"""
        assert convert_f_to_c(32) == 0
        assert convert_f_to_c(212) == 100
        assert abs(convert_f_to_c(150) - 65.5) < 0.1
