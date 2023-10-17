import os
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

# Clear the console
os.system('cls' if os.name == 'nt' else 'clear')

def convert_time(time_string):
    """
    Converts a time string to the format "HH:MM:SS DD/MM".

    Args:
        time_string: A string representing the time.

    Returns:
        A string representing the time in the format "HH:MM:SS DD/MM".
    """
    try:
        countdown_time = datetime.strptime(time_string, "%H:%M:%S").time()
        current_time = datetime.now().time()
        current_datetime = datetime.combine(datetime.now().date(), current_time)
        countdown_datetime = datetime.combine(datetime.now().date(), countdown_time)
        if countdown_time < current_time:
            countdown_datetime += timedelta(days=1)
        result_datetime = current_datetime + (countdown_datetime - datetime.combine(datetime.now().date(), datetime.min.time()))
        return result_datetime.strftime("%H:%M:%S %d/%m")
    except ValueError:
        pass

    try:
        day, time_string = time_string.split(" om ")
        time_object = datetime.strptime(time_string, "%H:%M").time()
        date_object = datetime.now() + timedelta(days=(datetime.strptime(day, "%A").weekday() - datetime.now().weekday()) % 7)
        return f"{time_object.strftime('%H:%M:%S')} {date_object.strftime('%d/%m')}"
    except ValueError:
        pass

    try:
        time_string = time_string.replace("Opent ", "")
        time_object = datetime.strptime(time_string, "%d %b %H:%M").time()
        date_string = datetime.now().strftime("%Y") + " " + time_string[:6]
        return f"{time_object.strftime('%H:%M:%S')} {datetime.strptime(date_string, '%Y %d %b').strftime('%d/%m')}"
    except ValueError:
        pass

    return None

def get_car_info(item, domain, f):
    """
    Extracts car information from a single item on the page.

    Args:
        item: A BeautifulSoup object representing a single item on the page.
        domain: The domain of the website being scraped.
        f: The file object to write the car information to.

    Returns:
        A dictionary containing the car information.
    """
    car_info = {}

    # Extract the car information from the item
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

    # Call the function to scrape additional info from the link page
    scrape_additional_info(car_info)

    # Write the car info to the JSON file
    json.dump(car_info, f, ensure_ascii=False)
    f.write('\n')

    return car_info

def scrape_car_data(url, domain):
    """
    Scrapes car information from a given URL.

    Args:
        url: The URL to scrape car information from.
        domain: The domain of the website being scraped.

    Returns:
        A dictionary containing the scraped car information.
    """
    car_data = {}

    with open('car_data.json', 'w', encoding='utf-8') as f:
        while url:
            # Print the URL of the page being scraped
            print(f"Scraping page: {url}\n...\n")

            # Send a request to the page and parse the HTML
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the car information from each item on the page
            car_list_items = soup.select('[class^="LotsOverview_item_"]')
            for item in car_list_items:
                # Extract the basic car information
                car_info = get_car_info(item, domain, f)
                print(f"Got all info for car: {car_info['name']}")
                # Extract the additional car information
                scrape_additional_info(car_info)
                print("saved to file ...\n")

                # If the car lot number already exists in the dictionary, update the existing entry
                if car_info['lot'] in car_data:
                    existing_info = car_data[car_info['lot']]
                    existing_info['time'] = car_info['time']
                    existing_info['bids'] = car_info['bids']
                    existing_info['image_links'] = car_info['image_links']
                    existing_info['lot_info'] = car_info['lot_info']
                # Otherwise, add a new entry to the dictionary
                else:
                    car_data[car_info['lot']] = car_info

            # Find the link to the next page
            next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')
            url = domain + next_page_link['href'] if next_page_link else None

            # Print whether or not there's a next page
            if not url:
                print("No next page found\n...\n")

    return car_data

def scrape_additional_info(car_info):
    """
    Scrapes additional car information from the link page.

    Args:
        car_info: A dictionary containing the car information.

    Returns:
        None.
    """
    response = requests.get(car_info['link'])
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the image links from the link page
        car_info['image_links'] = list(set([img['src'] for img in soup.select('img[src^="https://media.tbauctions.com/image-media/"]')]))

        # Extract the lot information from the link page
        lot_info = {}
        key_elements = soup.select('dt[class*="LotMetadata_key"]')
        value_elements = soup.select('dd[class*="LotMetadata_value"]')
        for item, value in zip(key_elements, value_elements):
            lot_info[item.text.strip()] = value.text.strip()
        car_info.update(lot_info)
    else:
        print("Error:", response.status_code)

# URLs of the websites
vavato_url = "https://vavato.com/c/vervoer/auto's/5196727d-c14f-48dc-a2f0-e75f50094a52"
troostwijkauctions_url = "https://www.troostwijkauctions.com/c/vervoer/auto's/5196727d-c14f-48dc-a2f0-e75f50094a52"

# Scrape car information from both websites
vavato_data = scrape_car_data(vavato_url, "https://vavato.com")
troostwijkauctions_data = scrape_car_data(troostwijkauctions_url, "https://www.troostwijkauctions.com")

# Combine the data from both websites
car_data = {**vavato_data, **troostwijkauctions_data}

# Save all car data to a JSON file
with open('car_data.json', 'w', encoding='utf-8') as f:
    for car_info in car_data.values():
        # Write the car info to the JSON file
        json.dump(car_info, f, ensure_ascii=False)
        f.write('\n')
        print(f"Wrote car info to file.")
