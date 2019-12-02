from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

session = None
Base = None


def create_session(database):
    global session, Base

    Base = automap_base()
    engine = create_engine(database)
    Base.prepare(engine, reflect=True)
    session = Session(engine)

    return session
