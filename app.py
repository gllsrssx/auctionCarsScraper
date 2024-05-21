from flask import Flask, render_template, request
from jinja2 import Environment, select_autoescape

import json
import multiprocessing
import scraper
import update
from datetime import datetime
 
app = Flask(__name__)
data_results = update.main()
cars_per_page = 24

def currency_format(value):
    return "{:.2f}".format(value / 100)

app.jinja_env.filters['currency_format'] = currency_format

def is_list(value):
    return isinstance(value, list)

def is_dict(value):
    return isinstance(value, dict)

app.jinja_env.tests['list'] = is_list
app.jinja_env.tests['dict'] = is_dict

@app.route('/', methods=['GET','POST'])
def index():
    page = int(request.args.get('page', 1))
    INP_MAX_PRICE = int(request.args.get('INP_MAX_PRICE', request.form.get('INP_MAX_PRICE', 10000)))
    INP_MAX_KM = int(request.args.get('INP_MAX_KM', request.form.get('INP_MAX_KM', 100000)))
    INP_MAX_YEAR = int(request.args.get('INP_MAX_YEAR', request.form.get('INP_MAX_YEAR', 2015)))
    data_results = update.main(INP_MAX_PRICE, INP_MAX_KM, INP_MAX_YEAR) 

    start_idx = (page - 1) * cars_per_page
    end_idx = start_idx + cars_per_page
    current_page_cars = data_results[start_idx:end_idx]
    total_pages = (len(data_results) + cars_per_page - 1) // cars_per_page
    has_more_pages = end_idx < len(data_results)
    
    with open('old_data_results.json', 'r') as f:
        old_data = json.load(f)
    old_cars = [car for car in old_data if datetime.strptime(car['endDate'], '%Y-%m-%d') < datetime.now()]

    data_to_send = {
        'cars_per_page': cars_per_page, 
        'amount_of_cars': len(data_results),
        'cars': current_page_cars,
        'has_more_pages': has_more_pages,
        'page': page,
        'total_pages': total_pages,
        'INP_MAX_PRICE' : INP_MAX_PRICE,
        'INP_MAX_KM' : INP_MAX_KM,
        'INP_MAX_YEAR' : INP_MAX_YEAR,
        'old_cars': old_cars,  # Add this line
    }

    return render_template('index.html', data=data_to_send)

if __name__ == '__main__':
    app.run(debug=False)

