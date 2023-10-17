from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

# Load the car data from the JSON file
with open('car_data.json', 'r') as f:
    car_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html', car_data=car_data)

if __name__ == '__main__':
    app.run(debug=True)
