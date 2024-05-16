import json
from datetime import datetime

INP_MAX_PRICE = 15000
INP_MAX_KM = 150000

def attribute_cars(data):
    for car in data:
        # Create a new dictionary for car attributes
        car_attributes = {}
        if 'attributes' in car:
            for attribute in car['attributes']:
                name = attribute['name']
                value = attribute['value']
                unit = attribute['unit']
                if 'mileage' in name.lower():
                    name = 'mileage'
                    unit = 'km'
                if ('transmission' in name.lower() or 'driving' in name.lower()) and 'automa' in value.lower():
                    name = 'Transmission'
                    value = 'Automatic'
                car_attributes[name] = {'unit': unit, 'value': value}
            # Update the car dictionary with attributes
            car.update(car_attributes)
            # Remove the 'attributes' key
            del car['attributes']
    return data

def update_cars(data):
    for car in data:
        next_bid = car.get('nextMinimalBid') or car.get('currentBidAmount')
        car['total_price'] = int(next_bid.get('cents', 0) * 0.012) if next_bid else 0
        car['formatted_endDate'] = datetime.utcfromtimestamp(car['endDate']).strftime('%H:%M %d/%m')
        # Check if mileage is in miles and convert it
        if 'mileage' in car and car['mileage'].get('unit', '').lower() == 'mi':
            car['mileage'] = {'unit': 'km', 'value': int(float(car['mileage'].get('value', 0)) * 1.60934)}
        elif 'mileage' not in car or not car['mileage'].get('value', '').isdigit():
            car['mileage'] = {'unit': 'km', 'value': 0}
        car['mileage']['value'] = int(car['mileage']['value'])
    return data

def filter_cars(data, INP_MAX_PRICE, INP_MAX_KM):
    filtered_cars = []
    for car in data:
        # print(car['id'])
        if (car['total_price'] <= INP_MAX_PRICE 
            and car['mileage']['value'] <= INP_MAX_KM 
            and 'Transmission' in car and car['Transmission']['value'].lower() == 'automatic'
            and car['location']['countryCode'] in ['be', 'de', 'nl']):
            filtered_cars.append(car)
    # Sort cars by endDate
    filtered_cars.sort(key=lambda car: car['endDate'])
    return filtered_cars

def main(INP_MAX_PRICE=15000, INP_MAX_KM=150000):  
    with open('data_results.json', 'r') as f:
        data_results = json.load(f)

    data_results = attribute_cars(data_results)
    data_results = update_cars(data_results)
    data_results = filter_cars(data_results, INP_MAX_PRICE, INP_MAX_KM)  # Pass max_price and max_km to filter_cars
    
    return data_results
