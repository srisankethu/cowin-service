import requests
from utils import get_slot_dates

class Cowin:

    def __init__(self):
        pass

    def find_available_slots(self, dates, pincodes, age_limit, search_for_dose1, search_for_dose2, preferred_vaccines = ['COVISHIELD', 'COVAXIN', 'SPUTNIK V']):


        available_slots = []
        for date in dates:
            for pincode in pincodes:

                url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date}".format(date=date, pincode = pincode)
                slots = requests.get(url).json()['sessions']
                for slot in slots:
                    if slot['vaccine'] in preferred_vaccines:
                        if slot['min_age_limit'] == age_limit:
                            if(search_for_dose1 == True and search_for_dose2 == True):
                                if slot['available_capacity_dose1'] > 0 or slot['available_capacity_dose2'] > 0:
                                    available_slots.append(slot)
                            elif(search_for_dose1 == True):
                                if slot['available_capacity_dose1'] > 0:
                                    available_slots.append(slot)
                            elif(search_for_dose2 == True):
                                if slot['available_capacity_dose2'] > 0:
                                    available_slots.append(slot)
                            else:
                                pass

        return available_slots

if __name__ == "__main__":

    cowin = Cowin()

    dates = get_slot_dates(2)
    pincodes = [500017, 500033, 500034]
    preferred_vaccines = ['COVISHIELD', 'COVAXIN', 'SPUTNIK V']

    slots = cowin.find_available_slots(dates, pincodes, 18, True, False, preferred_vaccines)
    print(slots)
