import logging
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from database import Car, create_database
from sqlalchemy.orm import sessionmaker

# Your constants and URLs
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
    time_string = item.select_one('[class^="Countdown_timer_"]').text.strip()
    time_formatted = convert_time(time_string)
    car_info['time'] = time_formatted
    bids_element = item.select_one('[class^="LotsOverviewListItem_countBids_"]')
    car_info['bids'] = bids_element.text.strip().replace("Biedingen: ", "") if bids_element else -1
    price_string = item.select_one('[class^="LotsOverviewListItem_wrapperPriceAndAction_"] span').text.strip()
    price_digits = ''.join(filter(str.isdigit, price_string.split('.')[0]))
    car_info['price'] = int(int(price_digits) * 1.2) if re.search(r'\d', price_digits) else -1
    car_info['img'] = item.select_one('img[src^="https://media.tbauctions.com/image-media/"]')['src']
    car_info['link'] = domain + item.select_one('a[class^="LotsOverviewListItem_link_"]')['href']
    car_info['lot'] = item.select_one('[class^="LotsOverviewListItem_lotNumber_"]').text.strip()
    scrape_additional_info(car_info)
    return car_info

def scrape_car_data(url, domain, existing_car_data):
    car_data = existing_car_data
    new_car_data = {}
    while url:
        logging.info(f"Scraping page: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        car_list_items = soup.select('[class^="LotsOverview_item_"]')
        for item in car_list_items:
            car_info = get_car_info(item, domain)
            scrape_additional_info(car_info)
            key = car_info['lot']
            new_car_data[key] = car_info
            logging.info(f"Scraped car: {car_info}")
        next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')
        url = domain + next_page_link['href'] if next_page_link else None
        if not url:
            logging.info("No next page found")
    return {**car_data, **new_car_data}

def scrape_additional_info(car_info):
    response = requests.get(car_info['link'])
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info['image_links'] = list(set([img['src'] for img in soup.select('img[src^="https://media.tbauctions.com/image-media/"]')]))
        lot_info = {item.text.strip(): value.text.strip() for item, value in zip(soup.select('dt[class*="LotMetadata_key"]'), soup.select('dd[class*="LotMetadata_value"]'))}
        car_info.update(lot_info)
    else:
        logging.error(f"Error: {response.status_code}")


    car_data = {}

    for data_source in data_sources:
        for lot, car_info in data_source.items():
            if lot not in car_data or car_info['time'] > car_data[lot]['time']:
                car_data[lot] = car_info
    return car_data

    car_data_list = list(car_data.values())
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(car_data_list, f, ensure_ascii=False, indent=4)
        f.write('\n')

def store_data_in_database(car_data):
    try:
        for car_info in car_data.values():
            existing_car = session.query(Car).filter(Car.lot == car_info['lot']).first()
            if existing_car:
                if car_info['time'] > existing_car.time:
                    existing_car.name = car_info['name']
                    existing_car.location = car_info.get('location', existing_car.location)
                    existing_car.time = car_info['time']
                    existing_car.bids = car_info.get('bids', existing_car.bids)
                    existing_car.price = car_info.get('price', existing_car.price)
                    existing_car.img = car_info.get('img', existing_car.img)
                    existing_car.link = car_info['link']
                    for key, value in car_info.items():
                        if key not in ['lot', 'name', 'location', 'time', 'bids', 'price', 'img', 'link']:
                            setattr(existing_car, key, value)
            else:
                new_car = Car(
                    lot=car_info['lot'],
                    name=car_info['name'],
                    location=car_info.get('location'),
                    time=car_info['time'],
                    bids=car_info.get('bids'),
                    price=car_info.get('price'),
                    img=car_info.get('img'),
                    link=car_info['link']
                )  
                for key, value in car_info.items():
                    if key not in ['lot', 'name', 'location', 'time', 'bids', 'price', 'img', 'link']:
                        setattr(new_car, key, value)
                session.add(new_car)
        session.commit()
        logging.info("Data update and save complete")
    except Exception as e:
        session.rollback()
        logging.error(f"Error storing data in the database: {str(e)}")
    finally:
        session.close()

def main():
    session = create_database('h2+tcp://localhost/your_database_name')

    # Query existing data from the database
    existing_car_data = session.query(Car).all()
    existing_car_dict = {car.lot: car for car in existing_car_data}

    # Scrape data and update the database
    vavato_data = scrape_car_data(vavato_url, vavato_domain, existing_car_dict)
    troostwijkauctions_data = scrape_car_data(troostwijkauctions_url, troostwijkauctions_domain, existing_car_dict)

    for lot, car_info in vavato_data.items():
        if lot not in existing_car_dict or car_info['time'] > existing_car_dict[lot].time:
            session.merge(car_info)

    for lot, car_info in troostwijkauctions_data.items():
        if lot not in existing_car_dict or car_info['time'] > existing_car_dict[lot].time:
            session.merge(car_info)

    # Commit changes to the database
    session.commit()
    logging.info("Data update and save complete")

if __name__ == '__main__':
    # Create the session
    session = create_database('h2+tcp://localhost/your_database_name')

    # Call your main function
    main()

    # Close the session
    session.close()