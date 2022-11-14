import logging
import os
import time
from concurrent import futures

import grpc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import person_pb2, person_pb2_grpc
from models import Person

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]

PERSONS_SERVICE_PORT = os.environ["PERSONS_SERVICE_PORT"]


Session = sessionmaker()
engine = create_engine(f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session.configure(bind=engine)

logging.basicConfig(level=logging.WARNING)
logging.getLogger("persons-service")


class PersonServicer(person_pb2_grpc.PersonServiceServicer):
    def Create(self, request, _):
        """Creates a new Person."""
        new_person = Person(
            first_name=request.first_name,
            last_name=request.last_name,
            company_name=request.company_name
        )

        with Session() as session:
            session.add(new_person)
            session.commit()

        return request

    def Get(self, request, _):
        """Gets selected persons (by IDs)."""
        with Session() as session:
            persons = session.query(Person).filter(
                Person.id.in_(request.id_list)
            ).all()

        result = person_pb2.PersonMessageList()
        for person in persons:
            person_message = person_pb2.PersonMessage(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            result.persons.append(person_message)

        return result

    def GetAll(self, request, context):
        """Gets all the persons."""
        with Session() as session:
            persons = session.query(Person).all()

        result = person_pb2.PersonMessageList()
        for person in persons:
            person_message = person_pb2.PersonMessage(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            result.persons.append(person_message)

        return result


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
person_pb2_grpc.add_PersonServiceServicer_to_server(PersonServicer(), server)

logging.info("Server starting on port %s...", PERSONS_SERVICE_PORT)
server.add_insecure_port(f"[::]:{PERSONS_SERVICE_PORT}")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)
