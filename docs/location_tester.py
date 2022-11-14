from datetime import datetime

import grpc

import location_pb2
import location_pb2_grpc

# Once it's deployed, the Location service is exposed as Node port (30005).
channel = grpc.insecure_channel("localhost:30005")
stub = location_pb2_grpc.LocationServiceStub(channel)

# Update this with desired payload
location = location_pb2.LocationMessage(
    person_id=1,
    latitude="37.49223",   # Catania's coords
    longitude="15.07041",
    creation_time=datetime.utcnow().isoformat()
)

stub.Create(location)
