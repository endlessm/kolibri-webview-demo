import os

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

session = None
Base = None


def create_session(dbfile):
    global session, Base

    if not os.path.isfile(dbfile):
        raise IOError('{dbfile} does not exist or it is not accesible'.format(dbfile=dbfile))

    Base = automap_base()
    engine = create_engine('sqlite:///{dbfile}'.format(dbfile=dbfile))
    Base.prepare(engine, reflect=True)
    session = Session(engine)

    return session
