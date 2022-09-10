#!/usr/bin/env python
'''Description here'''

import logging
import argparse
import requests
import time
import json
import redis
import datetime


config = {}

def read_config():
    with open("/cfg/config.json") as json_file:
        config = json.load(json_file)    


def getNextHour(lat, lon, key):

    url = 'https://api.weatherbit.io/v2.0/forecast/minutely'
    params = dict(
        lat=lat,
        lon=lon,
        key=key
    )
    #'data':[{'timestamp_utc': '2022-09-01T18:38:00', 'snow': 0, 'temp': 12.9, 'timestamp_local': '2022-09-01T20:38:00', 'ts': 1662057480, 'precip': 0}
    resp = requests.get(url=url, params=params)
    data = resp.json() # Check the JSON Response Content documentation below

    cnt = 0
    five_min_avg_temp = 0

    if len(data['data']) < 1:
        return

    for row in data['data']:
        if cnt < 6:
            five_min_avg_temp = five_min_avg_temp + float(row['temp'])
            cnt = cnt + 1
        

    current_temp = 0.0
    
    if cnt > 0:
        current_temp = round(five_min_avg_temp / cnt, 1)
    temp_trend = "and falling"
    if float(data['data'][0]['temp']) < float(data['data'][-1]['temp']):
        temp_trend = "and rising"

    
    return current_temp, temp_trend 


day_index_to_string = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

def getNext8Days(lat, lon, key):

    url = 'https://api.weatherbit.io/v2.0/forecast/daily'
    params = dict(
        lat=lat,
        lon=lon,
        key=key,
        days=8
    )
    #{"moonrise_ts":1662212260,"wind_cdir":"ESE","rh":70,"pres":1015.7,"high_temp":14.8,"sunset_ts":1662227406,"ozone":315.1,"moon_phase":0.624751,"wind_gust_spd":3.1,"snow_depth":0,"clouds":89,"ts":1662188460,"sunrise_ts":1662177623,"app_min_temp":3.8,"wind_spd":1.4,"pop":55,"wind_cdir_full":"east-southeast","moon_phase_lunation":0.26,"slp":1025.3,"app_max_temp":14.8,"valid_date":"2022-09-03","vis":24.128,"snow":0,"dewpt":7.5,"uv":1,"weather":{"icon":"r04d","code":520,"description":"Light shower rain"},"wind_dir":121,"max_dhi":null,"clouds_hi":0,"precip":2.29761,"low_temp":9.1,"max_temp":14.8,"moonset_ts":1662235446,"datetime":"2022-09-03","temp":12.8,"min_temp":7,"clouds_mid":91,"clouds_low":82},
    resp = requests.get(url=url, params=params)
    data = resp.json() # Check the JSON Response Content documentation below

    cnt = 0

    if len(data['data']) < 1:
        return

    days = dict()


    for row in data['data']:    
        day = dict()
        day['datetime'] = row['datetime']
        day['day_of_week'] = day_index_to_string[datetime.datetime.strptime(day['datetime'], '%Y-%m-%d').date().weekday()]
        day['max_temp'] = round(float(row['max_temp']))
        day['min_temp'] = round(float(row['min_temp']))
        day['pop'] = row['pop']
        day['precip'] = round(float(row['precip']), 1)
        day['icon'] = getIconMapping(row['weather']['icon'])
        day['code'] = row['weather']['code']

        days[cnt] = day
        cnt = cnt + 1
            
    return days 

def getIconMapping(icon):
    #https://www.weatherbit.io/api/codes

    if icon[0] == 't':
        return 'Skycons.THUNDER_RAIN'
    if icon[0] == 'd':
        if icon[3] == 'd':
            return 'Skycons.SHOWERS_DAY'
        else:   
            return 'Skycons.SHOWERS_NIGHT'
    if icon[0] == 'r':
        return 'Skycons.RAIN'
    if icon[0] == 's':
        if icon[2] == '4':
            return 'Skycons.RAIN_SNOW'
        else:
            return 'Skycons.SNOW'
    if icon[0] == 'a':
        return 'Skycons.FOG'
    if icon == 'c01d':
        return 'Skycons.CLEAR_DAY'
    if icon == 'c01n':
        return 'Skycons.CLEAR_NIGHT'
    if icon == 'c02d':
        return 'Skycons.PARTLY_CLOUDY_DAY'
    if icon == 'c02n':
        return 'Skycons.PARTLY_CLOUDY_NIGHT'
    if icon == 'c03d' or icon == 'c04d':
        return 'Skycons.CLOUDY'
    if icon == 'c03n' or icon == 'c04n':
        return 'Skycons.CLOUDY'

    return 'Skycons.RAIN'

def getCurrent(lat, lon, key):

    url = 'https://api.weatherbit.io/v2.0/current'
    params = dict(
        lat=lat,
        lon=lon,
        key=key
    )
    #.....w":0,"dewpt":9.1,"uv":1.5,"weather":{"icon":"c03d","code":803,"description":"Uppsprickande moln"},"wind_dir":27,
    resp = requests.get(url=url, params=params)
    data = resp.json() # Check the JSON Response Content documentation below

    cnt = 0
    five_min_avg_temp = 0

    if len(data['data']) < 1:
        return

    w = data['data'][0]['weather']

    wind_dir = data['data'][0]['wind_cdir']
    date_time = data['data'][0]['ob_time']
    wind_speed = data['data'][0]['wind_spd']
    return w['description'], w['code'], w['icon'], wind_dir, wind_speed, date_time 

def set_logging(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    return logger

if __name__ == "__main__":
    with open("/cfg/config.json") as json_file:
        config = json.load(json_file) 
        logger = set_logging()

        while 1 == 1:

            lat = str(config['general']['lat'])
            lon = str(config['general']['lon'])
            key = str(config['weatherbit']['key'])

            current_temp, temp_trend = getNextHour(lat, lon, key)
            description, code, icon, wind_dir, wind_speed,  date_time = getCurrent(lat, lon, key)
            days = getNext8Days(lat,lon,key)

            r = redis.Redis(host=str(config['redis']['url']), port=config['redis']['port'])
            new_data = dict()
            new_data['date_time'] = date_time
            new_data['lat'] = lat
            new_data['lon'] = lon
            new_data['title'] = str(config['general']['title'])
            new_data['radar_url'] = str(config['general']['radar_url'])
            new_data['description'] = description
            new_data['code'] = code
            new_data['current_temp'] = current_temp
            new_data['temp_trend'] = temp_trend
            new_data['wind_dir'] = wind_dir
            new_data['wind_speed'] = wind_speed
            new_data['icon'] = getIconMapping(icon)
            logger.info(new_data)

            new_data['days'] = days


            r.set(str(config['redis']['key']), json.dumps(new_data))
            time.sleep(600)