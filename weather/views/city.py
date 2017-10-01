from collections import defaultdict

import arrow
from flask import Blueprint, jsonify, request

from weather.models import WeatherStation


bp = Blueprint('station', __name__)


@bp.route('/<city_name>')
def get_city_data(city_name):
    """Get weather data for the given city

    :param city_name: Name of the city to get data for
    :type city_name: str
    :param unit: Required URL Param that specifies unit to retrieve temperature
    in. Must be F or C
    :type unit: str
    :returns: JSON response that looks like:
        {
            station: {
                id: 1,
                external_station_id: 'NLE0010247',
                latitude: 42,
                longitude: 42,
                elevation: -2,
            },
            data: {
                daily_ts: {
                    '2017-10-01': {
                        tmin: 24,
                        tmax: 46
                    },
                    .
                    .
                    .
                },
                weekly_ts: {
                    '2017-10-01': {
                        tmin: 24,
                        tmax: 46
                    },
                    .
                    .
                    .

                },
                monthly_ts: {},
                    '2017-10-01': {
                        tmin: 24,
                        tmax: 46
                    },
                    .
                    .
                    .
                },
            },
        }

        Note that daily, weekly, and monthly all return using timestamps.
        Wording of the visualization is left up to the client of the api.
    :rtype: Jsonify Response
    """
    if 'unit' not in request.args or request.args['unit'] not in ['F', 'C']:
        response = jsonify(error='Unit must be provided as a URL param and '
                           'must either be F or C')
        response.status_code = 400
        return response

    is_celcius = request.args['unit'] == 'C'

    station = WeatherStation.query.filter_by(name=city_name).first()
    if not station:
        response = jsonify(error='City {0} is not in the DB'.format(city_name))
        response.status_code = 400
        return response

    timeseries = station.timeseries
    daily_timeseries = {}
    weekly_agg = defaultdict(lambda: defaultdict(list))
    monthly_agg = defaultdict(lambda: defaultdict(list))

    for day in timeseries:
        tmax = day.tmax
        tmin = day.tmin
        if is_celcius:
            tmax = convert_f_to_c(day.tmax) if day.tmax else None
            tmin = convert_f_to_c(day.tmin) if day.tmin else None

        week = arrow.get(day.date).floor('week')
        month = arrow.get(day.date).floor('month')
        day_datum = {'tmax': tmax, 'tmin': tmin}

        daily_timeseries[str(day.date)] = day_datum

        for stat, val in zip(['tmax', 'tmin'], [tmax, tmin]):
            weekly_agg[week][stat].append(val)
            monthly_agg[month][stat].append(val)

    def average_agg(agg):
        """Average the datapoints we have collected per week/month"""
        averages = {}
        for arrow_date, stat_and_data_points in agg.items():
            date_string = str(arrow_date.date())
            averages[date_string] = {}
            for stat, data_points in stat_and_data_points.items():
                # Eliminate Nones
                avg = None
                non_none_data = filter(lambda x: x, data_points)
                if non_none_data:
                    avg = sum(non_none_data) / len(non_none_data)
                averages[date_string][stat] = avg
        return averages

    weekly_averages = average_agg(weekly_agg)
    monthly_averages = average_agg(monthly_agg)

    resp = dict(
        station=station.to_dict(),
        data=dict(
            daily_ts=daily_timeseries,
            weekly_ts=weekly_averages,
            monthly_ts=monthly_averages
        ))
    return jsonify(resp)


def convert_f_to_c(f_temp):
    """Convert a fahrenheit temp to celcius

    :param f_temp: The float fahrenheit temperature to convert
    :type f_temp: float
    :returns: The given temperature in celcius
    :rtype: float
    """
    return (f_temp - 32) / 1.8
