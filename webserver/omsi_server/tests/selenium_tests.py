from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re
import os

class Viewer(unittest.TestCase):
    def setUp(self):
        options = {'chrome.switches': '--args --disable-web-security'}
        self.driver = webdriver.Chrome(desired_capabilities=options)
        #self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000"
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_viewer(self):
        driver = self.driver
        driver.get(self.base_url + "/openmsi/client/viewer/?file=20120711_Brain.h5&image_name=Mouse%20Brain:%20Left%20Coronal%20Hemisphere&expIndex=0&dataIndex=0&channel1Value=868.6&channel2Value=840.6&channel3Value=824.6&rangeValue=0.2&cursorCol1=40&cursorRow1=40&cursorCol2=80&cursorRow2=80")
        self.assertEqual("OpenMSI Viewer", driver.title)
        
        try: self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "#graph1 svg g path"))
        except AssertionError: self.verificationErrors.append("no spectrum graph for Point #1")
        try: self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "#graph2 svg g path"))
        except AssertionError: self.verificationErrors.append("no spectrum graph for Point #2")

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert.text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
