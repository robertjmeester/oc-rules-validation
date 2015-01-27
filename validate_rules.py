#!path/to/python
import sys
from settings import OC, PATHS, TESTSXLS
from models import Browser, TestBattery

if __name__ == "__main__":
    """ Validation of OpenClinica rules """

    # Manual testscript input on command line
    # trumps the list in settings.py
    if len(sys.argv[1:]) != 0:
        TESTSXLS = []
        for script in sys.argv[1:]:
            TESTSXLS.append(script)

    # Create a browser session and login
    browser = Browser(OC['URL'], PATHS['SCREENSHOTS'] )
    browser.login(OC['USER'], OC['PWD'])
    browser.set_study(OC['STUDY'])
    
    # Load validation tests into test battery
    test_battery = TestBattery(PATHS['TEST_SCRIPTS'], TESTSXLS)

    # Run the validation tests in the browser
    test_battery.validate(browser)
    
    # End the browser session    
    browser.close()
        
    # Create PDF reports
    test_battery.create_reports(PATHS['REPORTS'])

