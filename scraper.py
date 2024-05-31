import requests
import json
import os
import shutil
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import logging

# logging.basicConfig(level=logging.INFO)

def scrape_lots_data(domain, endlink):
    base_url = f"{domain}en/c/transport/cars/{endlink}"
    all_results = []

    # Create a session object
    session = requests.Session()

    # Define the retry settings
    retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])

    # Mount it for both http and https usage
    session.mount('http://', HTTPAdapter(max_retries=retry))
    session.mount('https://', HTTPAdapter(max_retries=retry))

    page = 1
    while True:
        page_url = f"{base_url}?page={page}"
        logging.info(f"Scraping data from {page_url}...")
        
        # Use session.get instead of requests.get
        response = session.get(page_url)

        if response.status_code != 200:
            logging.error(f"Failed to retrieve data from {page_url}. Status code: {response.status_code}")
            base_url = f"{domain}en/l/transport/cars/{endlink}"
            page_url = f"{base_url}?page={page}"
            logging.error(f"Retrying with {page_url}...")
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
            response = requests.get(result['link'], headers=headers)
            if response.status_code != 200:
                logging.error(f"Failed to retrieve data from {page_url}. Status code: {response.status_code}")
                break

        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        data_json = json.loads(script.string)
        lots_data = data_json.get('props', {}).get('pageProps', {}).get('lotsData', {})

        if lots_data:
            for result in lots_data.get('results', []):
                result['domain'] = domain
            all_results.extend(lots_data.get('results', []))
        else:
            logging.error("No 'lotsData' found in the JSON data.")
            break

        next_page_link = soup.select_one('[class^="Pagination_nextLink_"]')

        if next_page_link:
            next_page_url = next_page_link.get('href')
            page_url = f"{base_url}{next_page_url}"
        else:
            break

        page += 1

    return all_results

def combine_data(result1, result2):
    if not (result1 and result2):
        logging.error("Error: 'results' key is missing in one or both dictionaries.")
        return None

    combined_results = result1 + result2
    logging.info(f"Combined {len(result1)} results with {len(result2)} results.")
    return combined_results

def scrape_lot_data(results):
    updated_results = []
    i = 0
    total_count = len(results)
    for result in results:
        i+=1
        result['link'] = f"{result['domain']}en/l/{result['urlSlug']}"
        try:
            response = requests.get(result['link'])
            logging.info(f"{i}/{total_count} Scraping data from {result['link']}...")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                script = soup.find('script', id='__NEXT_DATA__')

                if script:
                    data_json = json.loads(script.string)
                    lot_data = data_json.get('props', {}).get('pageProps', {}).get('lot', {})
                    result.update(lot_data)

            updated_results.append(result)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error while scraping {result['link']}: {e}")
    return updated_results

def remove_duplicates(data):
    seen = {}
    for car in data:
        if car['urlSlug'] not in seen or car['currentBidAmount']['cents'] > seen[car['urlSlug']]['currentBidAmount']['cents']:
            seen[car['urlSlug']] = car
    return list(seen.values())

def main():
    logging.warning("Scraping")
    
    url_vavato = ['https://vavato.com/', '5196727d-c14f-48dc-a2f0-e75f50094a52']
    url_troostwijkauctions = ['https://www.troostwijkauctions.com/', '5196727d-c14f-48dc-a2f0-e75f50094a52']

    results_vavato = scrape_lots_data(url_vavato[0], url_vavato[1])
    results_troostwijkauctions = scrape_lots_data(url_troostwijkauctions[0], url_troostwijkauctions[1])

    combined_results = combine_data(results_vavato, results_troostwijkauctions)

    data_results = scrape_lot_data(combined_results)
    
    if os.path.exists('data_results.json'):
            if os.path.exists('old_data_results.json'):
                with open('old_data_results.json', 'r') as f:
                    old_data = json.load(f)
                with open('data_results.json', 'r') as f:
                    new_data = json.load(f)
                combined_data = old_data + new_data
                with open('old_data_results.json', 'w') as f:
                    json.dump(combined_data, f, indent=4)
            else:
                shutil.move('data_results.json', 'old_data_results.json')

    with open('data_results.json', 'w') as f:
        json.dump(data_results, f, indent=4)
    logging.info("Data has been successfully scraped and combined @ data_results.json. len(data_results) = ", len(data_results))
    
    if os.path.exists('data_results.json'):
        with open('data_results.json', 'r') as f:
            data = json.load(f)
        data = remove_duplicates(data)
        with open('data_results.json', 'w') as f:
            json.dump(data, f, indent=4)

    if os.path.exists('old_data_results.json'):
        with open('old_data_results.json', 'r') as f:
            old_data = json.load(f)
        old_data = remove_duplicates(old_data)
        with open('old_data_results.json', 'w') as f:
            json.dump(old_data, f, indent=4)
   

if __name__ == '__main__':
    main()