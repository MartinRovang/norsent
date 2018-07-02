from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine('sqlite:///twitter.db', echo=True)
Base = declarative_base()

########################################################################
class data(Base):
    """"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    data1 = Column(String)
    sent = Column(String)
    what = Column(String)

    def __init__(self,data1,sent,what):
        """"""
        self.data1 = data1
        self.sent = sent
        self.what = what

# create tables
Base.metadata.create_all(engine)