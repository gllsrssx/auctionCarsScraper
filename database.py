from sqlalchemy import create_engine, Column, String, Integer, DateTime, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import re

Base = declarative_base()

class Car(Base):
    __tablename__ = 'cars'

    lot = Column(String, primary_key=True)
    name = Column(String)
    location = Column(String)
    time = Column(DateTime)
    bids = Column(Integer)
    price = Column(Integer)
    img = Column(String)
    link = Column(String)

    def __init__(self, lot, name, location, time, bids, price, img, link):
        self.lot = lot
        self.name = name
        self.location = location
        self.time = time
        self.bids = bids
        self.price = price
        self.img = img
        self.link = link

def create_database(engine_url):
    engine = create_engine(engine_url, echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

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

    # Your existing time conversion function
    # ...

# Rest of your code (data scraping) remains the same

