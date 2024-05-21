import requests
import json
import os
import shutil
from bs4 import BeautifulSoup

def scrape_lots_data(domain, endlink):
    base_url = f"{domain}en/c/transport/cars/{endlink}"
    all_results = []

    page = 1
    while True:
        page_url = f"{base_url}?page={page}"
        print(f"Scraping data from {page_url}...")
        response = requests.get(page_url)

        if response.status_code != 200:
            print(f"Failed to retrieve data from {page_url}. Status code: {response.status_code}")
            base_url = f"{domain}en/l/transport/cars/{endlink}"
            page_url = f"{base_url}?page={page}"
            print(f"Retrying with {page_url}...")
            response = requests.get(page_url)
            if response.status_code != 200:
                print(f"Failed to retrieve data from {page_url}. Status code: {response.status_code}")
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
            print("No 'lotsData' found in the JSON data.")
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
        print("Error: 'results' key is missing in one or both dictionaries.")
        return None

    combined_results = result1 + result2
    print(f"Combined {len(result1)} results with {len(result2)} results.")
    return combined_results

def scrape_lot_data(results):
    updated_results = []
    i = 0
    total_count = len(results)
    for result in results:
        i+=1
        result['link'] = f"{result['domain']}en/l/{result['urlSlug']}"
        response = requests.get(result['link'])
        print(f"{i}/{total_count} Scraping data from {result['link']}...")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script = soup.find('script', id='__NEXT_DATA__')

            if script:
                data_json = json.loads(script.string)
                lot_data = data_json.get('props', {}).get('pageProps', {}).get('lot', {})
                result.update(lot_data)

        updated_results.append(result)

    return updated_results

def main():
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
    print("Data has been successfully scraped and combined @ data_results.json. len(data_results) = ", len(data_results))

if __name__ == '__main__':
    main()