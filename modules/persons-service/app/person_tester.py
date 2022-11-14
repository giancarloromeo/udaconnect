import grpc

from app import person_pb2, person_pb2_grpc

print("Sending sample payload...")

channel = grpc.insecure_channel("localhost:5005")
stub = person_pb2_grpc.PersonServiceStub(channel)

# Update this with desired payload
person = person_pb2.PersonMessage(
    first_name="Blabla"
)


response = stub.Create(person)
