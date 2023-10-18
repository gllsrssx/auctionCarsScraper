import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import logging

# URLs for scraping
urls = [
    "https://vavato.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52",
    "https://www.troostwijkauctions.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52"
]

# Initialize existing data
existing_car_data = []

# Configure logging
logging.basicConfig(filename='scraping_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to convert time string to a formatted datetime
def convert_time(time_string):
    current_datetime = datetime.now()
    try:
        countdown_time = datetime.strptime(time_string, "%H:%M:%S").time()
        current_time = current_datetime.time()
        countdown_datetime = datetime.combine(current_datetime.date(), countdown_time)
        if countdown_time < current_time:
            countdown_datetime += timedelta(days=1)
        result_datetime = current_datetime + (countdown_datetime - datetime.combine(current_datetime.date(), datetime.min.time()))
        return f"{result_datetime.strftime('%H:%M:%S %d/%m')}"

    except ValueError:
        pass
    try:
        if "Opens" in time_string:
            day, time_string = time_string.replace("Opens","").split(" at ")
            day, time_string = day.strip(), time_string.strip()
            time_object = datetime.strptime(time_string, "%H:%M").time()
            date_object = current_datetime + timedelta(days=(datetime.strptime(day, "%A").weekday() - current_datetime.weekday()) % 7)
            return f"{time_object.strftime('%H:%M:%S %d/%m')}"
    except ValueError:
        pass
    try:
        if "Closes" in time_string:
            day, time_string = time_string.replace("Closes","").split(" at ")
            day, time_string = day.strip(), time_string.strip()
            time_object = datetime.strptime(time_string, "%H:%M").time()
            date_object = current_datetime + timedelta(days=(datetime.strptime(day, "%A").weekday() - current_datetime.weekday()) % 7)
            return f"{time_object.strftime('%H:%M:%S %d/%m')}"
    except ValueError:
        pass
    return None

# Function to get car information from a page
def get_car_info(item, domain):
    car_info = {}
    car_info['name'] = item.select_one('[class^="title-5 LotsOverviewListItem_title_"]').text.strip()
    car_info['location'] = item.select_one('[class^="LotsOverviewListItem_location_"]').text.replace("ë", "e").strip()
    time_string = item.select_one('[class^="Countdown_timer_"]').text.strip()
    time_formatted = convert_time(time_string)
    car_info['time'] = time_formatted
    car_info['link'] = domain + item.select_one('a[class^="LotsOverviewListItem_link_"]')['href']
    car_info['lot'] = item.select_one('[class^="LotsOverviewListItem_lotNumber_"]').text.strip()
    # Extract other car information here
    scrape_additional_info(car_info)
    return car_info

# Function to scrape additional information from the car's page
def scrape_additional_info(car_info):
    response = requests.get(car_info['link'], headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info['image_links'] = list(set([img['src'] for img in soup.select('img[src^="https://media.tbauctions.com/image-media/"]')]))
        lot_info = {}
        key_elements = soup.select('dt[class*="LotMetadata_key"]')
        value_elements = soup.select('dd[class*="LotMetadata_value"]')
        for item, value in zip(key_elements, value_elements):
            lot_info[item.text.strip()] = value.text.strip()
        car_info.update(lot_info)
    else:
        print("Error: ", response.status_code)

# Function to scrape and store car data
def scrape_and_store_car_data(url, domain, existing_car_data):
    car_data = existing_car_data
    
    while url:
        logging.info(f"Scraping page: {url}")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            car_list_items = soup.select('[class^="LotsOverview_item_"]')
            
            for item in car_list_items:
                car_info = get_car_info(item, domain)
                lot_number = car_info['lot']
                if lot_number in car_data:
                    existing_info = car_data[lot_number]
                    if car_info['time'] > existing_info['time']:
                        existing_info.update(car_info)
                else:
                    car_data[lot_number] = car_info
            
            next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')
            url = domain + next_page_link['href'] if next_page_link else None
            if not url:
                logging.info("No next page found")
            time.sleep(1) 
        else:
            logging.error(f"Error while scraping {url}. Status code: {response.status_code}")

    return car_data

# Load existing data from the JSON file
existing_car_data = {}
if os.path.exists('car_data.json'):
    with open('car_data.json', 'r', encoding='utf-8') as f:
        existing_car_data = json.load(f)

# Scrape and store data for all URLs
for url in urls:
    existing_car_data = scrape_and_store_car_data(url, url, existing_car_data)

# Combine and store unique car data
with open('car_data.json', 'w', encoding='utf-8') as f:
    json.dump(existing_car_data, f, ensure_ascii=False, indent=4)

print("Done")