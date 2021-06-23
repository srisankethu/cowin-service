from flask import Flask, request, redirect, url_for, session
from sqlalchemy.engine import create_engine
from flask_session import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update
from utils import get_slot_dates
from twilio_notification import TwilioNotification
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse, Hangup
from cowin_booking import CowinBooking
from slot_notification_registration import SlotNotification
from slot_booking_registration import SlotBooking
from selenium import webdriver
from threading import Timer
import os
import time
import requests
import phonenumbers


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
active_users_map = {}

def make_registration(otp, number):
    try:
        
        booking = active_users_map[str(number)]
        booking.submit_otp(otp)
        time.sleep(5)
        
        details = get_details(number)[0]
        booking.schedule_for(int(details.dose))
        time.sleep(5)
        
        booking.search_for_pincode(details.pincodes.split("*")[0])
        time.sleep(5)

        #booking.apply_age_filter(int(details.age))
        #time.sleep(5)
        return True
    except:
        return False
    finally:
        booking.driver.close()
        active_users_map.pop(str(number))

def get_details(phone_no):


    engine = create_engine('sqlite:///slotbooking.db', echo=True)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    results = db_session.query(SlotBooking).filter(SlotBooking.phone_no == phone_no).all()

    db_session.close()

    return results


def update_slot_notification_db(booking):

    if str(booking) == "slotnotification":
        model = SlotNotification
    elif str(booking) == "slotbooking":
        model = SlotBooking

    engine = create_engine('sqlite:///'+ str(booking) + '.db', echo=True)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    results = db_session.query(model).filter(model.phone_no == session['phone_no']).all()
    if(results != []):
        stmt = update(model).where(model.phone_no == session['phone_no']).values(age = int(session['age']), vaccine = str(session['vaccine']), dose = int(session['dose']), pincodes = str(session['pincodes']))
        db_session.execute(stmt)
    else:
        entry = model(str(session['phone_no']), int(session['age']), str(session['vaccine']), int(session['dose']), str(session['pincodes']))
        db_session.add(entry)
    db_session.commit()
    db_session.close()

@app.route('/ivr/outgoingcall/gather', methods=['POST'])
def gather():

    response = VoiceResponse()

    if 'Digits' in request.values:
        choice = request.values['Digits']
        success = make_registration(choice, str(request.values['To']))
        if(success):
            response.redirect(url_for("success", booking="slotbooking", kind = "booking"))
        else:
            response.redirect(url_for("failure", booking="slotbooking", kind = "booking"))
        return str(response)

    resp.redirect(url_for("outgoing_call"))

    return str(response)

@app.route("/ivr/outgoingcall", methods=['POST'])
def outgoing_call():
    response = VoiceResponse()
    gather = Gather(action = url_for("gather"), numDigits=6, timeout=10)
    gather.say("To book slot ASAP, enter the 6-digit COWIN OTP you just received")
    response.say("Book your vaccine slot. Check your messages for the vaccination slots that are open.")
    response.append(gather)

    response.redirect(url_for("outgoing_call"))
    return str(response)

@app.route("/ivr/<booking>/<kind>/success", methods=['POST'])
def success(booking, kind):

    response = VoiceResponse()
    if(kind == "registration"):
        response.say("Thank you for registering for {booking}".format(booking = booking))
        response.say("You will be notified via call and SMS once the slots are available in your areas")
    elif(kind == "booking"):
        response.say("Your booking was successfull")
        response.say("Details of your booking will be sent to you")
    response.hangup()

    return str(response)

@app.route("/ivr/<booking>/<kind>/failure", methods=['POST'])
def failure(booking, kind):

    response = VoiceResponse()
    if(kind == "registration"):
        response.say("Registration has failed")
        response.say("You might have entered the wrong details or there must be an issue with the service")
    else:
        response.say("We have failed to book your slot")
    response.say("Please try again later")
    response.hangup()

    return str(response)

@app.route("/ivr/incomingcall/<booking>/registration/details/age", methods=['POST'])
def registration_details_age(booking):
    
    response = VoiceResponse()
    gather = Gather(numDigits=2)
    gather.say("Enter your age")
    response.append(gather)

    if 'Digits' in request.values:
        session['age'] = request.values['Digits']

        response = VoiceResponse()
        response.redirect(url_for("registration_details_vaccine", booking=booking))
        str(response)

    response.redirect(url_for('registration_details_age', booking=booking))
    return str(response)

@app.route("/ivr/incomingcall/<booking>/registration/details/vaccine", methods=['POST'])
def registration_details_vaccine(booking):
    
    response = VoiceResponse()
    response.say("Select the vaccines you prefer")
    gather = Gather()
    gather.say("Press 1 for Covishield")
    gather.say("Press 2 for Covaxin")
    gather.say("Press 3 for SPUTNIK 5")
    gather.say("You can select multiple options separated by asterix")
    gather.say("Press # to end")
    response.append(gather)

    if 'Digits' in request.values:
        session['vaccine'] = request.values['Digits']

        response = VoiceResponse()
        response.redirect(url_for("registration_details_dose", booking=booking))
        str(response)

    response.redirect(url_for('registration_details_vaccine', booking=booking))
    return str(response)

@app.route("/ivr/incomingcall/<booking>/registration/details/dose", methods=['POST'])
def registration_details_dose(booking):
    
    response = VoiceResponse()
    response.say("Select for which dose you want to register")
    gather = Gather(numDigits=1)
    gather.say("Press 1 for Dose 1")
    gather.say("Press 2 for Dose 2")
    response.append(gather)

    if 'Digits' in request.values:
        session['dose'] = request.values['Digits']

        response = VoiceResponse()
        response.redirect(url_for("registration_details_pincodes", booking=booking))
        str(response)

    response.redirect(url_for('registration_details_dose', booking=booking))
    return str(response)

@app.route("/ivr/incomingcall/<booking>/registration/details/pincodes", methods=['POST'])
def registration_details_pincodes(booking):
    
    response = VoiceResponse()
    gather = Gather()
    gather.say("Enter pincodes of the areas that you can reach to separated by asterix")
    gather.say("Press # to end")
    response.append(gather)

    if 'Digits' in request.values:
        session['pincodes'] = request.values['Digits']
        
        response = VoiceResponse()
        response.redirect(url_for('registration_validation', booking=booking))
        str(response)
    
    response.redirect(url_for("registration_details_pincodes", booking=booking))
    return str(response)

@app.route("/ivr/incomingcall/<booking>/registration/validation", methods=['POST'])
def registration_validation(booking):

    response = VoiceResponse()
    count = 0
    for key in session.keys():
        key = str(key)
        if key == 'phone_no':
            phone_no = phonenumbers.parse(session['phone_no'])
            if(phonenumbers.is_valid_number(phone_no)):
                count = count + 1
        elif key == 'age':
            if(session['age']>=18 and session['age'] < 150):
                count = count + 1
        elif key == 'vaccine':
            vaccines = session['vaccine'].split("*")
            vc = 0
            for vaccine in vaccines:
                if(int(vaccine) == 1 or int(vaccine) == 2 or int(vaccine) == 3):
                    vc = vc + 1
            if(vc == len(vaccines)):
                count = count + 1
        elif key == 'dose':
            if(int(session['dose']) == 1 or int(session['dose']) == 1)
            count = count + 1
        elif key == 'pincodes':
            pincodes = session['pincodes'].split("*")
            pc = 0
            for pincode in pincodes:
                if(len(pincode) == 6):
                    pc = pc + 1
            if(pc == len(pincodes)):
                count = count + 1
        else:
            pass

    if count == 5:
        update_slot_notification_db(booking)
        response.redirect(url_for("success", booking=booking, kind = "registration"))
    else:
        response.redirect(url_for("failure", booking=booking, kind = "registration"))
    
    return str(response)


@app.route("/ivr/incomingcall/<booking>/registration", methods=['POST'])
def register_for_slot_notification(booking):

    session['phone_no'] = request.values['Caller']

    response = VoiceResponse()
    response.redirect(url_for("registration_details_age", booking=booking))

    return str(response)

@app.route("/ivr/incomingcall", methods = ['POST'])
def incoming_call():

    response = VoiceResponse()
    gather = Gather(numDigits=1, timeout=10)
    gather.say("Press 1 for slot notification")
    gather.say("Press 2 for slot booking")
    response.say("Hello, welcome to the CoWIN slot booking service")
    response.append(gather)

    if 'Digits' in request.values:

        choice = int(request.values['Digits'])
        response = VoiceResponse()
        if(choice == 1):
            response.redirect(url_for("register_for_slot_notification", booking="slotnotification"))
            return str(response)
        elif(choice == 2):
            response.redirect(url_for("register_for_slot_notification", booking="slotbooking"))
            return str(response)
        else:
            response.say("Enter a valid choice")
            response.hangup()
        return str(response)

    response.redirect(url_for("incoming_call"))
    return str(response)

@app.route("/ivr/outgoingcall/slotnotification/trigger/<number>", methods = ['GET', 'POST'])
def slot_notification_call(number):
    contacts = [number]
    message='<Response> \
             <Say> Book your vaccine slot. Check your messages for the vaccination slots that are open.</Say> \
             </Response>'
    for contact in contacts:     
        call = twilio_notification.client.calls.create(
                twiml=message,
                from_='+12109878250',
                to=contact
                )
    return ""

@app.route("/ivr/outgoingcall/slotbooking/trigger/<number>", methods = ['GET', 'POST'])
def slot_booking_call(number):
    
    contacts = [number]
    
    driver = webdriver.Chrome('./chromedriver')
    ngrok_url = os.environ["NGROK_URL"]
    url = "https://selfregistration.cowin.gov.in/"
    booking = CowinBooking(driver, url)
    time.sleep(5)
    booking.request_otp(number[3:])
    active_users_map[str(number)] = booking
    
    for contact in contacts:  
        call = twilio_notification.client.calls.create(
                url=ngrok_url + url_for("outgoing_call"),
                from_=os.environ['TWILIO_PHONE_NUMBER'],
                to=contact
                )
    return ""

if __name__ == "__main__":

    twilio_notification = TwilioNotification(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    app.run(debug = True, use_reloader = False)