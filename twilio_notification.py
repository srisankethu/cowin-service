from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse
import os

class TwilioNotification:

    def __init__(self, sid, auth_token):

        self.client = Client(sid, auth_token)

    def send_call(self, action_url, contacts):

        response = VoiceResponse()
        gather = Gather(action = action_url, numDigits=6, timeout=10)
        gather.say("To book slot ASAP, enter the 6-digit COWIN OTP you just received")
        response.say("Book your vaccine slot. Check your messages for the vaccination slotsthat are open.")
        response.append(gather)


        for contact in contacts:     
            call = self.client.calls.create(
                    twiml=response,
                    from_=os.environ['TWILIO_PHONE_NUMBER'],
                    to=contact
                    )

    def send_message(self, slots, contacts):

        if(slots == []):
            return
    
        message = 'Book your vaccination slot at: \n'
        for i in range(len(slots)):
            message = message + '{number}. {vaccine} vaccine in {hospital} having {dose1_slots} slots for dose 1 and {dose2_slots} slots for dose 2 at {pincode} on {date} \n\n'.format(number = i+1, vaccine=slots[i]['vaccine'], hospital=slots[i]['name'], pincode=slots[i]['pincode'], dose1_slots=slots[i]['available_capacity_dose1'], dose2_slots=slots[i]['available_capacity_dose2'], date=slots[i]['date'])
        message = message + "Visit https://selfregistration.cowin.gov.in/ to book your slot ASAP \n"
        
        for contact in contacts:
            sms = self.client.messages.create(
                    body=message,
                    from_=os.environ['TWILIO_PHONE_NUMBER']
                    to=contact
                    )