from app.udaconnect import person_pb2
from app.udaconnect.schemas import (
    ConnectionSchema,
    PersonSchema
)
from app.udaconnect.services import (
    ConnectionService,
    PersonService
)

from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from typing import List, Optional

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via GeoLocation.")  # noqa


@api.route("/persons")
class PersonsResource(Resource):
    @accepts(schema=PersonSchema)
    @responds(schema=PersonSchema)
    def post(self) -> person_pb2.PersonMessage:
        person_msg = person_pb2.PersonMessage(
            first_name=request.json["first_name"],
            last_name=request.json["last_name"],
            company_name=request.json["company_name"]
        )

        return PersonService.create(person_msg)

    @responds(schema=PersonSchema, many=True)
    def get(self) -> List[person_pb2.PersonMessage]:
        return PersonService.get_all()


@api.route("/persons/<person_id>/connection")
@api.param("start_date", "Lower bound of date range", _in="query")
@api.param("end_date", "Upper bound of date range", _in="query")
@api.param("distance", "Proximity to a given user in meters", _in="query")
class ConnectionDataResource(Resource):
    @responds(schema=ConnectionSchema, many=True)
    def get(self, person_id) -> ConnectionSchema:
        distance: Optional[int] = request.args.get("distance", 5)

        return ConnectionService.find_contacts(
            person_id=int(person_id),
            start_date=request.args["start_date"],
            end_date=request.args["end_date"],
            meters=int(distance),
        ).connections
