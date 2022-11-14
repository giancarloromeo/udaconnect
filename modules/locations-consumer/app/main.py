import json
import logging
import os
from datetime import datetime

from kafka import KafkaConsumer
from geoalchemy2.functions import ST_Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Location

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]

KAFKA_SERVICE_HOST = os.environ["KAFKA_SERVICE_HOST"]
KAFKA_SERVICE_PORT = os.environ["KAFKA_SERVICE_PORT"]

LOCATIONS_KAFKA_TOPIC = os.environ["LOCATIONS_KAFKA_TOPIC"]

Session = sessionmaker()
engine = create_engine(f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session.configure(bind=engine)

kafka_consumer = KafkaConsumer(
    LOCATIONS_KAFKA_TOPIC,
    bootstrap_servers=f"{KAFKA_SERVICE_HOST}:{KAFKA_SERVICE_PORT}"
)

logging.basicConfig(level=logging.WARNING)

for location_msg in kafka_consumer:
    location_json = json.loads(location_msg.value)

    logging.debug("Received new location %s", location_msg.value)

    # create a new location
    new_location = Location()
    new_location.person_id = location_json["person_id"]
    new_location.creation_time = datetime.fromisoformat(location_json["creation_time"])
    new_location.coordinate = ST_Point(location_json["latitude"], location_json["longitude"])

    with Session() as session:
        # write the location to the DB
        session.add(new_location)
        session.commit()
