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
    _DATABASE.create_tables([Country, Airport, Flight, Distance, Chain, ChainCountry, ChainFlight])

    return _DATABASE


class BaseModel(Model):
    class Meta:
        database = _DATABASE


class Country(BaseModel):
    code = FixedCharField(unique=True, max_length=2)


class Airport(BaseModel):
    code = FixedCharField(unique=True, max_length=3)
    country = ForeignKeyField(Country, backref='airports')
    latitude = DecimalField(max_digits=3, decimal_places=2)
    longitude = DecimalField(max_digits=3, decimal_places=2)


class Flight(BaseModel):
    source = ForeignKeyField(Airport)
    destination = ForeignKeyField(Airport)
    date = DateField(formats='%Y-%m-%d')
    cost = DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        indexes = (
            (('source', 'destination', 'date'), True),
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


class ChainCountry(BaseModel):
    chain = ForeignKeyField(Chain)
    country = ForeignKeyField(Country)

    class Meta:
        indexes = (
            (('chain', 'country'), True),
            (('chain',), False),
            (('country',), False),
        )


class ChainFlight(BaseModel):
    chain = ForeignKeyField(Chain)
    flight = ForeignKeyField(Flight)

    class Meta:
        indexes = (
            (('chain', 'flight'), True),
            (('chain',), False),
            (('flight',), False),
        )
