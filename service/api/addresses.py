import logging
from datetime import datetime, timedelta
import pprint
from datetime import datetime, timedelta
import json
from flask import abort, jsonify
from webargs.flaskparser import use_args

from marshmallow import Schema, fields

from service.server import app, db
from service.models import AddressSegment
from service.models import Person

# Get the address schema


class GetAddressQueryArgsSchema(Schema):
    date = fields.Date(required=False, missing=datetime.utcnow().date())


# Address schema
class AddressSchema(Schema):
    class Meta:
        ordered = True

    street_one = fields.Str(required=True, max=128)
    street_two = fields.Str(max=128)
    city = fields.Str(required=True, max=128)
    state = fields.Str(required=True, max=2)
    zip_code = fields.Str(required=True, max=10)

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False)

# Get the person address


@app.route("/api/persons/<uuid:person_id>/address", methods=["GET"])
@use_args(GetAddressQueryArgsSchema(), location="querystring")
def get_address(args, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    elif len(person.address_segments) == 0:
        abort(404, description="person does not have an address, please create one")

    address_segment = person.address_segments[-1]  # What the heck is this
    return jsonify(AddressSchema().dump(address_segment))


# Update a person address
@app.route("/api/persons/<uuid:person_id>/address", methods=["PUT"])
@use_args(AddressSchema())
def create_address(payload, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    # If there are no AddressSegment records present for the person, we can go
    # ahead and create with no additional logic.
    elif len(person.address_segments) == 0:
        address_segment = AddressSegment(
            street_one=payload.get("street_one"),
            street_two=payload.get("street_two"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
            start_date=payload.get("start_date"),
            person_id=person_id,
        )

        db.session.add(address_segment)
        db.session.commit()
        db.session.refresh(address_segment)

    else:
        # TODO: Implementation
        address_segment = AddressSegment(
            street_one=payload.get("street_one"),
            street_two=payload.get("street_two"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
            start_date=payload.get("start_date"),
            person_id=person_id,
        )
        logging.info(len(person.address_segments))
        date_dict = {}  # empty dict to house address_segment
        address_segment = person.address_segments
        for address in address_segment:
            # The Date logic works fine
            if address.start_date > payload.get('start_date'):
                return jsonify({'message': 'A record already exists with start_date greater than what was provided!'}), 409
            elif address.start_date == payload.get('start_date'):
                return jsonify({'error': 'Address segment already exists with start_date ' + payload.get('start_date').isoformat()}), 422
            else:
                isStreetOneDuplicate = payload.get('street_one') == address.street_one
                isStreetTwoDuplicate = payload.get('street_two') == address.street_two
                isCityDuplicate = payload.get('city') == address.city
                isStateDuplicate = payload.get('state') == address.state
                isZipCodeDuplicate = payload.get('zip_code') == address.zip_code

                # Checking for duplicate address
                if isStreetOneDuplicate and isStreetTwoDuplicate and isCityDuplicate and isStateDuplicate and isZipCodeDuplicate:
                    abort(409, description='Address already exists')
        # If there are one or more existing AddressSegments, create a new AddressSegment
        # that begins on the start_date provided in the API request and continues
        # into the future. If the start_date provided is not greater than most recent
        # address segment start_date, raise an Exception.
        address_segment = AddressSegment(
            street_one=payload.get("street_one"),
            street_two=payload.get("street_two"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
            start_date=payload.get("start_date"),
            person_id=person_id,
        )
        db.session.add(address_segment)
        db.session.commit()
        db.session.refresh(address_segment)
        return jsonify(AddressSchema().dump(address_segment))

    return jsonify(AddressSchema().dump(address_segment))
