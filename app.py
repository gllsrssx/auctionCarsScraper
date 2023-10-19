from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')
def index():
    with open('car_data.json') as json_file:
        car_data = json.load(json_file)
    return render_template('index.html', car_data=car_data)

if __name__ == '__main__':
    app.run(debug=True)
