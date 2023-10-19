from flask import Flask, render_template
from database import create_database  # Import your database code
from carScraper import main  # Import your scraping script

app = Flask(__name)

@app.route('/')
def index():
    # Call your scraping script to update the database
    main()

    # Query the car data from the database (you'll need to implement this)
    car_data = query_car_data_from_database()

    return render_template('index.html', car_data=car_data)

if __name__ == '__main__':
    app.run(debug=True)
