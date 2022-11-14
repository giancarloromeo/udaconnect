import json
import logging
import os
import time
from concurrent import futures
from datetime import datetime, timedelta

import grpc
from kafka import KafkaProducer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import location_pb2
import location_pb2_grpc
from models import Location

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]

KAFKA_SERVICE_HOST = os.environ["KAFKA_SERVICE_HOST"]
KAFKA_SERVICE_PORT = os.environ["KAFKA_SERVICE_PORT"]

LOCATIONS_SERVICE_PORT = os.environ["LOCATIONS_SERVICE_PORT"]
LOCATIONS_KAFKA_TOPIC = os.environ["LOCATIONS_KAFKA_TOPIC"]

# Kafka
kafka_producer = KafkaProducer(bootstrap_servers=f"{KAFKA_SERVICE_HOST}:{KAFKA_SERVICE_PORT}")

# DB
Session = sessionmaker()
engine = create_engine(f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session.configure(bind=engine)

logging.basicConfig(level=logging.WARNING)
logging.getLogger("locations-service")


class LocationServicer(location_pb2_grpc.LocationServiceServicer):
    def Create(self, request, _):
        json_data = {
            "person_id": request.person_id,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "creation_time": request.creation_time
        }
        kafka_data = json.dumps(json_data).encode()
        kafka_producer.send(LOCATIONS_KAFKA_TOPIC, kafka_data)

        return request

    def Get(self, request, _):
        with Session() as session:
            query = session.query(Location)
            if request.id:
                query = query.filter(Location.id == request.id)
            if request.start_date:
                query = query.filter(Location.creation_time > request.start_date)
            if request.end_date:
                query = query.filter(Location.creation_time < request.end_date)

            locations = query.all()

        result = location_pb2.LocationMessageList()
        for location in locations:
            location_msg = location_pb2.LocationMessage(
                id=location.id,
                person_id=location.person_id,
                latitude=location.latitude,
                longitude=location.longitude,
                creation_time=location.creation_time
            )
            result.locations.append(location_msg)

        return result

    def GetNearby(self, request, _):
        with Session() as session:
            locations = session.query(Location).filter(
                Location.person_id == request.person_id
            ).filter(Location.creation_time < request.end_date).filter(
                Location.creation_time >= request.start_date
            ).all()

            # Prepare arguments for queries
            data = []
            for location in locations:
                data.append(
                    {
                        "person_id": request.person_id,
                        "longitude": location.longitude,
                        "latitude": location.latitude,
                        "meters": request.radius,
                        "start_date": request.start_date,
                        "end_date": (datetime.strptime(request.end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                    }
                )

            query = text(
                """
            SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
            FROM    location
            WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
            AND     person_id != :person_id
            AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
            AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
            """
            )
            result = location_pb2.LocationMessageList()
            for line in tuple(data):
                for (
                        exposed_person_id,
                        location_id,
                        exposed_lat,
                        exposed_long,
                        exposed_time,
                ) in engine.execute(query, **line):
                    location = Location()
                    location.set_wkt_with_coords(exposed_lat, exposed_long)

                    result.locations.append(
                        location_pb2.LocationMessage(
                            id=location_id,
                            person_id=exposed_person_id,
                            latitude=location.latitude,
                            longitude=location.longitude,
                            creation_time=exposed_time.isoformat(),
                        )
                    )

        return result


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
location_pb2_grpc.add_LocationServiceServicer_to_server(LocationServicer(), server)

logging.info("Server starting on port %s...", LOCATIONS_SERVICE_PORT)
server.add_insecure_port(f"[::]:{LOCATIONS_SERVICE_PORT}")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)
