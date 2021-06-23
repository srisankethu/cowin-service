from datetime import datetime, timedelta

def get_slot_dates(no_of_days = 1):

    if(no_of_days < 1):
        return

    dates = []

    for i in range(no_of_days):
        today = datetime.now() + timedelta(i)
        today_string = today.strftime("%d/%m/%Y")

        dates.append(today_string)

    return dates