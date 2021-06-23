from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from slot_notification_registration import SlotNotification
from slot_booking_registration import SlotBooking
from cowin import Cowin
from utils import get_slot_dates
from twilio_notification import TwilioNotification
import os
import requests
import time
import multiprocessing

class Notifications:

    def __init__(self):
        self.model = None
        self.sleep_time = 30

    def add_notification_entry(self, booking, phone_no, age, vaccine, dose, pincodes):

        engine = create_engine('sqlite:///' + str(booking) + '.db')
        Session = sessionmaker(bind=engine)
        db_session = Session()
        #results = db_session.query(SlotNotification).all()
        db_session.add(self.model(phone_no, age, vaccine, dose, pincodes))
        db_session.commit()
        db_session.close()

    def delete_notification_entries(self, booking, phone_nos):

        engine = create_engine('sqlite:///' + str(booking) + '.db')
        Session = sessionmaker(bind=engine)
        db_session = Session()
        for phone_no in phone_nos:
            db_session.query(self.model).filter(self.model.phone_no == phone_no).delete()
        db_session.commit()
        db_session.close()

    def get_dose_check(self, result, slot):

        if int(result.dose) == 1 and slot['available_capacity_dose1'] > 0:
            return True
        elif int(result.dose) == 2 and slot['available_capacity_dose2'] > 0:
            return True
        return False

    def get_vaccine_check(self, result, slot):

        vaccines = result.vaccine.split("*")
        for vaccine in vaccines:
            if int(vaccine) == 1 and slot['vaccine'] == 'COVISHIELD':
                return True
            elif int(vaccine) == 2 and slot['vaccine'] == 'COVAXIN':
                return True
            elif int(vaccine) == 3 and slot['vaccine'] == 'SPUTNIK V':
                return True

        return False

    def get_age_check(self, result, slot):

        age = int(result.age)
        age_limit = 0
        if age >= 18 and age<45:
            age_limit = 18
        elif age >= 45:
            age_limit = 45

        if age_limit == slot['min_age_limit']:
            return True
        
        return False

    def get_notifications_map(self, booking):

        if str(booking) == "slotnotification":
            self.model = SlotNotification
        elif str(booking) == "slotbooking":
            self.model = SlotBooking

        engine = create_engine('sqlite:///' + str(booking) + '.db')
        Session = sessionmaker(bind=engine)
        db_session = Session()
        results = db_session.query(self.model).all()
        notifications = {}
        for result in results:
            pincodes = result.pincodes.split("*")
            phone_no = str(result.phone_no)
            for pincode in pincodes:
                pincode = str(pincode)
                if pincode in notifications.keys():
                    notifications[pincode].append(phone_no)
                else:
                    notifications[pincode] = [phone_no]

        try:
            self.sleep_time = int(300/int(100/(2*4*len(notifications.keys()))))
        except:
            self.sleep_time = 30
            return {}
        cowin = Cowin()
        dates = get_slot_dates(2)
        preferred_vaccines = ['COVISHIELD', 'COVAXIN', 'SPUTNIK V']
        slots_map = {}
        for pincode in notifications.keys():
            slots = []
            slots = slots + cowin.find_available_slots(dates, [pincode], 18, True, False, preferred_vaccines)
            slots = slots + cowin.find_available_slots(dates, [pincode], 18, False, True, preferred_vaccines)
            slots = slots + cowin.find_available_slots(dates, [pincode], 45, True, False, preferred_vaccines)
            slots = slots + cowin.find_available_slots(dates, [pincode], 45, False, True, preferred_vaccines)
            slots_map[pincode] = slots


        notifications_map = {}
        for result in results:
            pincodes = result.pincodes.split("*")
            phone_no = str(result.phone_no)
            for pincode in pincodes:
                pincode = str(pincode)
                slots = []
                for slot in slots_map[pincode]:
                    age_check = self.get_age_check(result, slot)
                    vaccine_check = self.get_vaccine_check(result, slot)
                    dose_check = self.get_dose_check(result, slot)
                    if age_check and vaccine_check and dose_check:
                        slots.append(slot)
                if phone_no in notifications_map.keys():
                    notifications_map[phone_no] = notifications_map[phone_no] + slots
                else:
                    notifications_map[phone_no] = slots

        db_session.close()

        return notifications_map

    def send_notification(self, booking):

        notifications_map = self.get_notifications_map(booking)

        twilio = TwilioNotification(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
       
        delete_contacts = []
        for contact in notifications_map.keys():
            if(notifications_map[contact] == []):
                pass
            else:
                twilio.send_message(notifications_map[contact], [contact])
                delete_contacts.append(contact)
                requests.get(os.environ["NGROK_URL"] + "/ivr/outgoingcall/{booking}/trigger/{contact}".format(booking = booking, contact=contact))

        #self.delete_notification_entries(booking, delete_contacts)

def start_process(booking):
    notifications.send_notification(booking)
    time.sleep(notifications.sleep_time)

if __name__ == "__main__":

    notifications = Notifications()
    p1 = None
    p2 = None
    while True:
        try:
            if(p1 == None or p1.is_alive() == False):
                p1 = multiprocessing.Process(target=start_process, args=['slotnotification'])
                p1.start()
        except:
            pass

        try:
            if(p2 == None or p2.is_alive() == False):
                p2 = multiprocessing.Process(target=start_process, args=['slotbooking'])
                p2.start()
        except:
            pass
        break