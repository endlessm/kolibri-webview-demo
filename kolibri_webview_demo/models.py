import os

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

session = None
Base = None


def create_session(dbfile):
    global session, Base

    if not os.path.isfile(dbfile):
        raise IOError(f'{dbfile} does not exist or it is not accesible')

    Base = automap_base()
    engine = create_engine(f'sqlite:///{dbfile}')
    Base.prepare(engine, reflect=True)
    session = Session(engine)

    return session
