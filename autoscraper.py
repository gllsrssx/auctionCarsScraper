import logging
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

vavato_url = "https://vavato.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52"
troostwijkauctions_url = "https://www.troostwijkauctions.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52"

# Configure logging
logging.basicConfig(filename='scraping_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_car_info(item, domain):
    car_info = {}
    car_info['name'] = item.select_one('[class^="title-5 LotsOverviewListItem_title_"]').text.strip()
    car_info['location'] = item.select_one('[class^="LotsOverviewListItem_location_"]').text.replace("ë", "e").strip()
    time_string = item.select_one('[class^="Countdown_timer_"]').text.strip()
    time_formatted = convert_time(time_string)
    car_info['time'] = time_formatted
    bids_element = item.select_one('[class^="LotsOverviewListItem_countBids_"]')
    car_info['bids'] = bids_element.text.strip().replace("Biedingen: ", "") if bids_element else -1
    car_info['price'] = item.select_one('[class^="LotsOverviewListItem_wrapperPriceAndAction_"] span').text.strip()
    car_info['img'] = item.select_one('img[src^="https://media.tbauctions.com/image-media/"]')['src']
    car_info['link'] = domain + item.select_one('a[class^="LotsOverviewListItem_link_"]')['href']
    car_info['lot'] = item.select_one('[class^="LotsOverviewListItem_lotNumber_"]').text.strip()
    scrape_additional_info(car_info)
    return car_info


def scrape_car_data(url, domain, existing_car_data):
    car_data = existing_car_data
    new_car_data = []  
    while url:
        print(f"Scraping page: {url}\n")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        car_list_items = soup.select('[class^="LotsOverview_item_"]')
        for item in car_list_items:
            car_info = get_car_info(item, domain)
            scrape_additional_info(car_info)
            new_car_data.append(car_info) 
            print(f"Scraped car: {car_info['name']}\tTime: {car_info['time']}\n")
        next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')
        url = domain + next_page_link['href'] if next_page_link else None
        if not url:
            print("No next page found\n")
    return car_data + new_car_data  # Combine the existing and new car data


def scrape_additional_info(car_info):
    response = requests.get(car_info['link'])
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info['image_links'] = list(set([img['src'] for img in soup.select('img[src^="https://media.tbauctions.com/image-media/"]')]))
        lot_info = {}
        key_elements = soup.select('dt[class*="LotMetadata_key"]')
        value_elements = soup.select('dd[class*="LotMetadata_value"]')
        for item, value in zip(key_elements, value_elements):
            lot_info[item.text.strip()] = value.text.strip()
        car_info.update(lot_info)
        print(lot_info)
    else:
        print("Error:", response.status_code)

existing_car_data = []
if os.path.exists('car_data.json') and os.path.getsize('car_data.json') > 0:
    with open('car_data.json', 'r', encoding='utf-8') as f:
        existing_car_data = {entry['lot']: entry for entry in json.load(f)}

vavato_data = scrape_car_data(vavato_url, "https://vavato.com", existing_car_data)
troostwijkauctions_data = scrape_car_data(troostwijkauctions_url, "https://www.troostwijkauctions.com", existing_car_data)

car_data = {**vavato_data, **troostwijkauctions_data}
unique_car_data = {}

for lot, car_info in car_data.items():
    if lot not in unique_car_data or car_info['time'] > unique_car_data[lot]['time']:
        unique_car_data[lot] = car_info

with open('car_data.json', 'w', encoding='utf-8') as f:
    json.dump(unique_car_data, f, ensure_ascii=False, indent=4)
    f.write('\n')

print("Done")