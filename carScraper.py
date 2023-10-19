import logging
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

vavato_url = "https://vavato.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52?page=12"
troostwijkauctions_url = "https://www.troostwijkauctions.com/en/c/transport/cars/5196727d-c14f-48dc-a2f0-e75f50094a52?page=54"
vavato_domain = "https://vavato.com"
troostwijkauctions_domain = "https://www.troostwijkauctions.com"
log_file = 'scraping_log.txt'
data_file = 'car_data.json'

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_time(input_string):
    time_pattern = r'\d{2}:\d{2}(:\d{2})?'
    weekday_pattern = r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday'
    daynumber_pattern = r'\d{2}'
    month_pattern = r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'

    time_match = re.search(time_pattern, input_string)
    weekday_match = re.search(weekday_pattern, input_string)
    daynumber_match = re.search(daynumber_pattern, input_string)
    month_match = re.search(month_pattern, input_string)

    current_datetime = datetime.now()
    result_datetime = current_datetime

    if time_match:
        while len(time_match.group(0)) < 8:
            time_match = re.search(time_pattern, time_match.group(0) + ":00"[:8])
        time = datetime.strptime(time_match.group(0), '%H:%M:%S')

        if weekday_match:
            day = weekday_match.group(0)
            weekday_indices = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}
            day_difference = (weekday_indices[day] - current_datetime.weekday()) % 7
            result_datetime += timedelta(days=day_difference)
            result_datetime = result_datetime.replace(hour=time.hour, minute=time.minute, second=time.second)
            return result_datetime.strftime("%H:%M:%S %d/%m")
        
        elif month_match:        
            month_indices = {month: i for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov','Dec'])}
            month = month_indices[month_match.group(0)]+1
            result_datetime = result_datetime.replace(month=month)
            day = daynumber_match.group(0)
            result_datetime = result_datetime.replace(day=int(day))
            result_datetime = result_datetime.replace(hour=time.hour, minute=time.minute, second=time.second) 
            return result_datetime.strftime("%H:%M:%S %d/%m")

        else:
            result_datetime += timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
            return result_datetime.strftime("%H:%M:%S %d/%m")
    else:
        return None

def get_car_info(item, domain):
    car_info = {}
    car_info['name'] = item.select_one('[class^="title-5 LotsOverviewListItem_title_"]').text.strip()
    car_info['location'] = item.select_one('[class^="LotsOverviewListItem_location_"]').text.replace("ë", "e").strip()
    car_info['time'] = convert_time(item.select_one('[class^="Countdown_timer_"]').text.strip())
    bids_element = item.select_one('[class^="LotsOverviewListItem_countBids_"]')
    car_info['bids'] = int(bids_element.text.strip().replace("Biedingen: ", "")) if bids_element else -1
    price_string = item.select_one('[class^="LotsOverviewListItem_wrapperPriceAndAction_"] span').text.strip()
    price_digits = ''.join(filter(str.isdigit, price_string.split('.')[0]))
    car_info['price'] = int(price_digits) * 1.2 if price_digits.isdigit() else -1
    car_info['img'] = item.select_one('img[src^="https://media.tbauctions.com/image-media/"]')['src']
    car_info['link'] = domain + item.select_one('a[class^="LotsOverviewListItem_link_"]')['href']
    car_info['lot'] = item.select_one('[class^="LotsOverviewListItem_lotNumber_"]').text.strip()
    car_info['image_links'] = []
    return car_info

def scrape_car_data(url, domain):
    car_data = {}
    while url:
        logging.info(f"Scraping page: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the response status code is not 200
            soup = BeautifulSoup(response.text, 'html.parser')
            car_list_items = soup.select('[class^="LotsOverview_item_"]')
            for item in car_list_items:
                car_info = get_car_info(item, domain)
                car_info['image_links'] = scrape_additional_info(car_info['link'])
                key = car_info['lot']
                car_data[key] = car_info
                logging.info(f"Scraped car: {car_info}")
            next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')
            url = domain + next_page_link['href'] if next_page_link else None
            if not url:
                logging.info("No next page found")
        except Exception as e:
            logging.error(f"Error while scraping: {str(e)}")
    return car_data

def scrape_additional_info(car_link):
    image_links = []
    try:
        response = requests.get(car_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        image_links = [img['src'] for img in soup.select('img[src^="https://media.tbauctions.com/image-media/"]')]
    except Exception as e:
        logging.error(f"Error while scraping additional info: {str(e)}")
    return image_links

def load_existing_data():
    car_data = {}
    try:
        if os.path.exists(data_file) and os.path.getsize(data_file) > 0:
            with open(data_file, 'r', encoding='utf-8') as f:
                car_data = {entry['lot']: entry for entry in json.load(f)}
    except Exception as e:
        logging.error(f"Error while loading existing data: {str(e)}")
    return car_data

def save_data(car_data):
    try:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(list(car_data.values()), f, ensure_ascii=False, indent=4)
            f.write('\n')
    except Exception as e:
        logging.error(f"Error while saving data: {str(e)}")

def main():
    existing_car_data = load_existing_data()
    vavato_data = scrape_car_data(vavato_url, vavato_domain)
    troostwijkauctions_data = scrape_car_data(troostwijkauctions_url, troostwijkauctions_domain)
    car_data = {**existing_car_data, **vavato_data, **troostwijkauctions_data}
    save_data(car_data)
    logging.info("Data update and save complete")

if __name__ == '__main__':
    main()