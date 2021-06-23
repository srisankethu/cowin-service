from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


class CowinBooking:

    def __init__(self, driver, url):
        self.driver = driver
        self.url = url
        driver.maximize_window()
        driver.get(url)

    def perform_login(self, mobile_number):

        self.request_otp(mobile_number)
        time.sleep(10)
        self.submit_otp("123456")

    def request_otp(self, mobile_number):

        mobile_input = self.driver.find_element_by_xpath("//input[@formcontrolname='mobile_number']")
        mobile_input.send_keys(mobile_number)

        get_otp_button = self.driver.find_element_by_xpath("//ion-button")
        get_otp_button.click()

    def submit_otp(self, otp):

        mobile_input = self.driver.find_element_by_xpath("//input[@formcontrolname='otp']")
        mobile_input.send_keys(otp)

        submit_otp_button = self.driver.find_element_by_xpath("//ion-button")
        submit_otp_button.click()

    def schedule_for(self, dose):

        schedule_buttons = self.driver.find_elements_by_xpath("//a[@href='/dashboard']")
        if(dose == 1):
            schedule_buttons[0].click()
        elif(dose == 2):
            schedule_buttons[1].click()

    def search_for_pincode(self, pincode):
        pincode_input = self.driver.find_element_by_xpath("//input[@formcontrolname='pincode']")
        pincode_input.send_keys(pincode)
        pincode_input.send_keys(Keys.RETURN)

    def apply_age_filter(self, age):

        if(age >= 18 and age < 45):
            age = 18
        elif(age >= 45):
            age = 45
        
        if(age == 18):
            age_button = self.driver.find_element_by_xpath("//input[@id='c1']")
        elif(age == 45):
            age_button = self.driver.find_element_by_xpath("//input[@id='c2']")

        age_button.click()

    def find_slot(self):

        vcs_panel = self.driver.find_element_by_xpath("//div[@class='center-box']")
        vcs = vcs_panel.find_elements_by_xpath("//div[@class='row ng-star-inserted']")
        for vc in vcs:
            vc_details = vc.find_element_by_class_name("row-disp")

            vc_name = vc_details.find_element_by_tag_name("h5")

            vc_slots_panel = vc.find_element_by_xpath("//ul[@class='slot-available-wrap']")
            vc_slots = vc_slots_panel.find_elements_by_tag_name("li")
            for vc_slot in vc_slots[:2]:
                try:
                    available_slot = vc_slot.find_element_by_xpath("//a[@href='/appointment']")
                    available_slot.click()
                    print("Vaccination center : " + str(vc_name.text))
                    print("No of doses : " + str(available_slot.text))
                    return
                except:
                    pass


if __name__=="__main__":

    url = "https://selfregistration.cowin.gov.in/"
    driver = webdriver.Chrome('./chromedriver')
    
    booking = CowinBooking(driver, url)

    booking.perform_login("9701137942")