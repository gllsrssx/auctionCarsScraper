import json
import re
from datetime import datetime
import logging

# logging.basicConfig(level=logging.INFO)

INP_MAX_PRICE = 10000
INP_MAX_KM = 100000
INP_MAX_YEAR = 2015

def attribute_cars(data):
    for car in data:
        # Create a new dictionary for car attributes
        car_attributes = {}
        transmission_set = False
        mileage_set = False
        if 'attributes' in car:
            for attribute in car['attributes']:
                name = attribute['name'].lower()
                value = attribute['value']
                unit = attribute['unit']
                if 'mileage' in name:
                    name = 'mileage'
                    unit = 'km'
                    mileage_set = True
                if ('transmission' in name or 'driving' in name) and 'automa' in value.lower():
                    name = 'Transmission'
                    value = 'Automatic'
                    transmission_set = True
                elif ('transmission' in name or 'driving' in name) and 'manual' in value.lower():
                    name = 'Transmission'
                    value = 'Manual'
                    transmission_set = True
                if 'first registration date' in name.lower() and 'nl' not in name.lower():                    
                    name = 'firstRegistrationYear'
                    match = re.search(r'\b\d{4}\b', value)
                    if match:
                        value = int(match.group())
                    else:
                        value = datetime.now().year  # default value
                car_attributes[name] = {'unit': unit, 'value': value}
            if not transmission_set:
                car_attributes['Transmission'] = {'unit': '', 'value': 'Unknown'}
            if not mileage_set:
                car_attributes['mileage'] = {'unit': 'km', 'value': 0}
            # Update the car dictionary with attributes
            car.update(car_attributes)
            # Remove the 'attributes' key
            del car['attributes']
    return data

def update_cars(data):
    for car in data:
        next_bid = car.get('nextMinimalBid') or car.get('currentBidAmount')
        car['total_price'] = int(next_bid.get('cents', 0) * 0.012) if next_bid else 0
        car['formatted_endDate'] = datetime.fromtimestamp(car['endDate']).strftime('%H:%M %d/%m')
        # Check if mileage is in miles and convert it
        if 'mileage' in car and car['mileage'].get('unit', '').lower() == 'mi':
            car['mileage'] = {'unit': 'km', 'value': int(float(car['mileage'].get('value', 0)) * 1.60934)}
        elif 'mileage' not in car or not str(car['mileage'].get('value', '')).isdigit():
            car['mileage'] = {'unit': 'km', 'value': 0}
        car['mileage']['value'] = int(car['mileage']['value'])
    return data

def filter_cars(data, INP_MAX_PRICE, INP_MAX_KM, INP_MAX_YEAR):
    filtered_cars = []
    for car in data:
        # print(car['id'])
        if (car['total_price'] <= INP_MAX_PRICE 
            and car['mileage']['value'] <= INP_MAX_KM 
            and 'Transmission' in car and (car['Transmission']['value'].lower() == 'automatic' or car['Transmission']['value'].lower() == 'unknown')
            and car['location']['countryCode'] in ['be', 'de', 'nl']
            and 'firstRegistrationYear' in car and car['firstRegistrationYear']['value'] >= INP_MAX_YEAR):  
            filtered_cars.append(car)
    # Sort cars by endDate
    filtered_cars.sort(key=lambda car: car['endDate'])
    return filtered_cars

def main(data_file, INP_MAX_PRICE=10000, INP_MAX_KM=100000, INP_MAX_YEAR=2015):  
    with open(data_file, 'r') as f:
        data_results = json.load(f)

    data_results = attribute_cars(data_results)
    data_results = update_cars(data_results)
    data_results = filter_cars(data_results, INP_MAX_PRICE, INP_MAX_KM, INP_MAX_YEAR)  # Pass max_price and max_km to filter_cars
    
    return data_results
