from app.udaconnect.person_pb2 import PersonMessage
from app.udaconnect.location_pb2 import LocationMessage

from marshmallow import Schema, fields


class LocationSchema(Schema):
    id = fields.Integer()
    person_id = fields.Integer()
    longitude = fields.String(attribute="longitude")
    latitude = fields.String(attribute="latitude")
    creation_time = fields.String()

    class Meta:
        model = LocationMessage


class PersonSchema(Schema):
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    company_name = fields.String()

    class Meta:
        model = PersonMessage


class ConnectionSchema(Schema):
    location = fields.Nested(LocationSchema)
    person = fields.Nested(PersonSchema)
