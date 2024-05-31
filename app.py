from flask import Flask, render_template, request
from jinja2 import Environment, select_autoescape

import json
from multiprocessing import Process
import scraper
import update
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
 
app = Flask(__name__)
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

scraper_process = None

@app.route('/', methods=['GET','POST'])
def index():
    global scraper_process
    if scraper_process is None or not scraper_process.is_alive():
        logging.info("Starting scraper process")
        scraper_process = Process(target=run_scraper)
        scraper_process.start()

    page = int(request.args.get('page', 1))
    INP_MAX_PRICE = int(request.args.get('INP_MAX_PRICE', request.form.get('INP_MAX_PRICE', 10000)))
    INP_MAX_KM = int(request.args.get('INP_MAX_KM', request.form.get('INP_MAX_KM', 100000)))
    INP_MAX_YEAR = int(request.args.get('INP_MAX_YEAR', request.form.get('INP_MAX_YEAR', 2014)))
    
    # Get the data source from the request
    data_source = request.args.get('data_source', 'new')
    # Load the data from the appropriate source
    if data_source == 'old':
        with open('old_data_results.json') as f:
            data_results = json.load(f)
        data_results = update.main('old_data_results.json',INP_MAX_PRICE, INP_MAX_KM, INP_MAX_YEAR)
    else:
        data_results = update.main('data_results.json',INP_MAX_PRICE, INP_MAX_KM, INP_MAX_YEAR)

    start_idx = (page - 1) * cars_per_page
    end_idx = start_idx + cars_per_page
    current_page_cars = data_results[start_idx:end_idx]
    total_pages = (len(data_results) + cars_per_page - 1) // cars_per_page
    has_more_pages = end_idx < len(data_results)
    
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
        'data_source': data_source
    }

    return render_template('index.html', data=data_to_send)

def run_scraper():
    while True:
        scraper.main()
        
if __name__ == '__main__':
    p = Process(target=run_scraper)
    p.start()
    app.run(debug=False)
    p.join()

