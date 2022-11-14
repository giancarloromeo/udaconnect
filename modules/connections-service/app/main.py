import logging
import os
import time
from concurrent import futures

import grpc

import connection_pb2
import connection_pb2_grpc
import person_pb2
import person_pb2_grpc
import location_pb2
import location_pb2_grpc

CONNECTIONS_SERVICE_PORT = os.environ["CONNECTIONS_SERVICE_PORT"]

PERSONS_SERVICE_HOST = os.environ["PERSONS_SERVICE_HOST"]
PERSONS_SERVICE_PORT = os.environ["PERSONS_SERVICE_PORT"]

LOCATIONS_SERVICE_HOST = os.environ["LOCATIONS_SERVICE_HOST"]
LOCATIONS_SERVICE_PORT = os.environ["LOCATIONS_SERVICE_PORT"]

logging.basicConfig(level=logging.WARNING)
logging.getLogger("connections-service")

persons_service_channel = grpc.insecure_channel(f"{PERSONS_SERVICE_HOST}:{PERSONS_SERVICE_PORT}")
persons_service_stub = person_pb2_grpc.PersonServiceStub(persons_service_channel)

locations_service_channel = grpc.insecure_channel(f"{LOCATIONS_SERVICE_HOST}:{LOCATIONS_SERVICE_PORT}")
locations_service_stub = location_pb2_grpc.LocationServiceStub(locations_service_channel)


class ConnectionServicer(connection_pb2_grpc.ConnectionServiceServicer):
    def FindConnections(self, request, _):
        """
        Finds all Person who have been within a given distance of a given Person within a date range.
        """

        result = connection_pb2.ConnectionMessageList()
        location_msg_list = locations_service_stub.GetNearby(
            location_pb2.GetNearbyMessage(
                person_id=request.person_id,
                start_date=request.start_date,
                end_date=request.end_date,
                radius=request.meters or 5
            )
        )

        person_id_list = set()
        for location_msg in location_msg_list.locations:
            person_id_list.add(location_msg.person_id)

        person_msg_map = {person_msg.id: person_msg
                          for person_msg in
                          persons_service_stub.Get(person_pb2.GetPersonMessage(
                              id_list=list(person_id_list)
                          )).persons}

        for location_msg in location_msg_list.locations:
            person_msg = person_msg_map[location_msg.person_id]
            connection_msg = connection_pb2.ConnectionMessage(
                location=connection_pb2.ConnectionLocationMessage(
                    id=location_msg.id,
                    person_id=location_msg.person_id,
                    latitude=location_msg.latitude,
                    longitude=location_msg.longitude,
                    creation_time=location_msg.creation_time
                ),
                person=connection_pb2.ConnectionPersonMessage(
                    id=person_msg.id,
                    first_name=person_msg.first_name,
                    last_name=person_msg.last_name,
                    company_name=person_msg.company_name
                )
            )
            result.connections.append(connection_msg)

        return result


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
connection_pb2_grpc.add_ConnectionServiceServicer_to_server(ConnectionServicer(), server)

logging.info("Server starting on port %s...", CONNECTIONS_SERVICE_PORT)
server.add_insecure_port(f"[::]:{CONNECTIONS_SERVICE_PORT}")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)
