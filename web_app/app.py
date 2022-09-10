from typing import List, Dict
from flask import Flask
from flask import render_template
from flask import request
import time
import calendar
import json
import re
import os
import datetime
from datetime import date, timedelta
import redis

config = {}

app = Flask(__name__, static_url_path='/static')
            
@app.route('/forecast')
def forecast():
    place = request.args.get('place', default = None, type = str)

    if place is None:
        return 'missing mandatory place!', 400

    r = redis.Redis(host=str(config['redis']['url']), port=config['redis']['port'])

    if not r.exists(place):
        return 'place does not exist!', 400

    data =  json.loads(r.get(place).decode("utf-8")) 
    print(data)
    
    max_v = -100.0
    min_v = 100.0

    for day in data['days']:
        if float(data['days'][day]['min_temp']) < min_v:
            min_v = float(data['days'][day]['min_temp'])
        if float(data['days'][day]['max_temp']) > max_v:
            max_v = float(data['days'][day]['max_temp'])
    diff = max_v - min_v

    step = 82.0 / diff
    days = dict()
    cnt = 0
    for day in data['days']:
        d = dict() 
        d['top'] = (max_v - float(data['days'][day]['max_temp'])) * step
        d['height'] = (float(data['days'][day]['max_temp']) - float(data['days'][day]['min_temp'])) * step
        d['icon'] = data['days'][day]['icon']
        d['day_of_week'] = data['days'][day]['day_of_week']
        d['max_temp'] = data['days'][day]['max_temp']
        d['min_temp'] = data['days'][day]['min_temp']

        days[cnt] = d
        cnt = cnt + 1

    dt = date.today()
    return render_template('forecast.html',
                           title=data['title'],
                           radar_url=data['radar_url'],
                           fe_wind_dir=data['wind_dir'],
                           fe_wind_speed=data['wind_speed'],
                           fe_description=data['description'],
                           fe_temp_trend=data['temp_trend'],
                           fe_current_temp=data['current_temp'],
                           fe_current_icon=data['icon'],
                           days=days)

if __name__ == '__main__':
    with open("/cfg/config.json") as json_file:
        config = json.load(json_file)    
        app.run(host='0.0.0.0')


