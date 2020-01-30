from peewee import (
    SqliteDatabase,
    ForeignKeyField,
    FixedCharField,
    DecimalField,
    DateField,
    Model,
)

_DATABASE = SqliteDatabase(None)


def create_database(db_filename):
    _DATABASE.init(db_filename)
    _DATABASE.create_tables([Airport, Flight, Distance, Chain, ChainFlight])

    return _DATABASE


class BaseModel(Model):
    class Meta:
        database = _DATABASE


class Airport(BaseModel):
    code = FixedCharField(unique=True, max_length=3)
    country = FixedCharField(max_length=2)
    latitude = DecimalField(max_digits=3, decimal_places=2)
    longitude = DecimalField(max_digits=3, decimal_places=2)


class Flight(BaseModel):
    source = ForeignKeyField(Airport)
    destination = ForeignKeyField(Airport)
    date = DateField(formats='%Y-%m-%d')
    cost = DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        indexes = (
            (('source', 'destination', 'date'), False),
            (('source',), False),
            (('cost',), False),
            (('date',), False),
        )


class Distance(BaseModel):
    source = ForeignKeyField(Airport)
    destination = ForeignKeyField(Airport)
    distance = DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        indexes = (
            (('source', 'destination'), True),
            (('source',), False),
            (('distance',), False),
        )


class Chain(BaseModel):
    cost = DecimalField(max_digits=6, decimal_places=2)


class ChainFlight(BaseModel):
    chain = ForeignKeyField(Chain)
    flight = ForeignKeyField(Flight)

    class Meta:
        indexes = (
            (('chain', 'flight'), True),
            (('chain',), False),
            (('flight',), False),
        )


def get_matching_flights(recent_airport_code, amount_left, lower_range, upper_range):
    return (
        Flight.select()
        .join(Airport, on=Flight.source)
        .where(Flight.source.code == recent_airport_code)
        .where(Flight.cost <= amount_left)
        .where(Flight.date.between(lower_range, upper_range))
    )


def get_recent_airport_and_date(chain_id):
    recent_flight = (
        ChainFlight.select().where(ChainFlight.chain_id == chain_id)
        .order_by(ChainFlight.id.desc()).limit(1)
    )[0].flight

    return recent_flight.destination.code, recent_flight.date


def get_new_chain(old_chain, new_flight):
    new_cost = old_chain.cost + new_flight.cost
    new_chain = Chain.get(Chain.id == Chain.insert(cost=new_cost).execute())

    for chain_flight in ChainFlight.select().where(ChainFlight.chain_id == old_chain.id).order_by(ChainFlight.id):
        ChainFlight.insert(chain_id=new_chain.id, flight_id=chain_flight.flight_id).execute()

    ChainFlight.insert(chain_id=new_chain.id, flight_id=new_flight.id).execute()

    return new_chain
