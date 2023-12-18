import json
from datetime import datetime

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
        car['total_price'] = int(car['nextMinimalBid']['cents'] * 0.012)
        car['formatted_endDate'] = datetime.utcfromtimestamp(car['endDate']).strftime('%H:%M %d/%m')
        # Check if mileage is in miles and convert it
        if 'mileage' in car and car['mileage'].get('unit', '').lower() == 'mi':
            car['mileage'] = {'unit': 'km', 'value': int(float(car['mileage'].get('value', 0)) * 1.60934)}
        elif 'mileage' not in car or not car['mileage'].get('value', '').isdigit():
            car['mileage'] = {'unit': 'km', 'value': 0}
        car['mileage']['value'] = int(car['mileage']['value'])
    return data

def filter_cars(data):
    filtered_cars = []
    for car in data:
        # print(car['id'])
        if (car['total_price'] <= 15000 
            and car['mileage']['value'] <= 150000 
            and 'Transmission' in car and car['Transmission']['value'].lower() == 'automatic'
            and car['location']['countryCode'] in ['be', 'de', 'nl']):
            filtered_cars.append(car)
    # Sort cars by endDate
    filtered_cars.sort(key=lambda car: car['endDate'])
    return filtered_cars

def main():
    with open('data_results.json', 'r') as f:
        data_results = json.load(f)

    data_results = attribute_cars(data_results)
    data_results = update_cars(data_results)
    data_results = filter_cars(data_results)
    
    return data_results
