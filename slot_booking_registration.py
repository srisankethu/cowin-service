from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///slotbooking.db', echo=True)
Base = declarative_base()

class SlotBooking(Base):

    __tablename__ = "slotbooking"

    id = Column(Integer, primary_key=True)
    phone_no = Column(String, unique=True)
    age = Column(Integer)
    vaccine = Column(String)
    dose = Column(Integer)
    pincodes = Column(String)

    def __init__(self, phone_no, age, vaccine, dose, pincodes):

        self.phone_no = phone_no
        self.age = age
        self.vaccine = vaccine
        self.dose = dose
        self.pincodes = pincodes

Base.metadata.create_all(engine)
