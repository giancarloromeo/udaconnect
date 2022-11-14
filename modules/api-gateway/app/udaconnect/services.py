import logging
from typing import List

import grpc

from app.udaconnect import person_pb2, person_pb2_grpc
from app.udaconnect import connection_pb2, connection_pb2_grpc

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("api-gateway")

# Initialize stub for Persons service
persons_service_channel = grpc.insecure_channel("persons-service:5005")
persons_service_stub = person_pb2_grpc.PersonServiceStub(persons_service_channel)


# Initialize stub for Connections service
connections_service_channel = grpc.insecure_channel("connections-service:5005")
connections_service_stub = connection_pb2_grpc.ConnectionServiceStub(connections_service_channel)


class ConnectionService:
    @staticmethod
    def find_contacts(person_id: int, start_date: str, end_date: str, meters=5):
        return connections_service_stub.FindConnections(
            connection_pb2.FindConnectionsMessage(
                person_id=person_id,
                start_date=start_date,
                end_date=end_date,
                meters=meters
            )
        )


# class LocationService:
#     @staticmethod
#     def retrieve(location_id) -> Location:
#         location, coord_text = (
#             db.session.query(Location, Location.coordinate.ST_AsText())
#             .filter(Location.id == location_id)
#             .one()
#         )
#
#         # Rely on database to return text form of point to reduce overhead of conversion in app code
#         location.wkt_shape = coord_text
#         return location
#
#     @staticmethod
#     def create(location: Dict) -> Location:
#         validation_results: Dict = LocationSchema().validate(location)
#         if validation_results:
#             logger.warning(f"Unexpected data format in payload: {validation_results}")
#             raise Exception(f"Invalid payload: {validation_results}")
#
#         new_location = Location()
#         new_location.person_id = location["person_id"]
#         new_location.creation_time = location["creation_time"]
#         new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
#         db.session.add(new_location)
#         db.session.commit()
#
#         return new_location


class PersonService:
    @staticmethod
    def create(person_msg: person_pb2.PersonMessage) -> person_pb2.PersonMessage:
        persons_service_stub.Create(person_msg)
        return person_msg

    @staticmethod
    def get(ids: List[int]) -> List[person_pb2.PersonMessage]:
        result = []
        for person_msg in persons_service_stub.Get(ids):
            result.append(
                person_pb2.PersonMessage(
                    id=person_msg.id,
                    first_name=person_msg.first_name,
                    last_name=person_msg.last_name,
                    company_name=person_msg.company_name
                )
            )
        return result

    @staticmethod
    def get_all() -> List[person_pb2.PersonMessage]:
        return persons_service_stub.GetAll(person_pb2.EmptyPersonMessage()).persons
