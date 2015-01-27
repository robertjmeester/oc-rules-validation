import os
import sys
import time
import xlrd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from pyvirtualdisplay import Display

from reportlab.lib.units import inch
from reports import Report

from settings import OC

class Rule(object):
    """ Simple definition of a rule.
        It has a name, a description and a list of tests.
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.tests = []

    def add_test(self, test):
        """ Add a new test to the list of test for this rule """
        self.tests.append(test)

    def validate(self, browser):
        """ Run all the tests for this rule """
        print str(self.name)
        for test in self.tests:
            test.run_test(browser)

    def is_valid(self):
        """ If all tests pass, the rule is valid """
        valid = True
        for test in self.tests:
            if not test.passed():
                valid = False
                break
        return valid

    def nr_failed_tests(self):
        """ Get the number of failed tests """
        fails = 0
        for test in self.tests:
            if not test.passed():
                fails += 1
        return fails

    def get_failed_tests(self):
        """ Return a list of test id's that have not passed """
        failed = []
        for test in self.tests:
            if not test.passed():
                failed.append(str(test))
        return failed

    def create_report(self, report_path):
        """ Create a pdf with the validation result for this rule """
        if self.is_valid():
            report_name = self.name
        else:
            report_name = "INVALID_%s" % self.name
        report = Report("%s/%s.pdf" % (report_path, report_name))
        report.add_text("Validation Report - %s" % self.name, 18, 'Center')
        report.add_spacer()
        report.add_line()
        report.add_spacer(0.2*inch)
        nr_tests = len(self.tests)
        report.add_text("Description:")
        report.add_text(self.description)
        report.add_text("&nbsp;")
        report.add_text("Validation date: %s" % time.strftime("%Y-%m-%d"))
        if self.is_valid():
            report.add_text("This rule is valid, all %d checks passed." % nr_tests)
        else:
            nr_fails = self.nr_failed_tests()
            report.add_text("Number of tests: %d" % nr_tests)
            report.add_text("Number of failed tests: %d" % nr_fails)
            report.add_text("Success rate: %d %%" % (((nr_tests-nr_fails)/float(nr_tests))*100.0))
            report.add_spacer(0.1*inch)
            report.add_text("This rule is NOT valid", 14)
        for test in self.tests:
            if test.passed():
                result = "Passed"
            else:
                result = "FAILED"
            report.add_new_page()
            report.header("Rule: %s - Test: %s - %s" % (self.name, test.test_id, result))
            report.add_text("Test values used:")

            for k, v in test.test_values.items():
                if v == "":
                    v = "< empty >"
                report.add_text("%sItem: %s" % ("&nbsp;"*5, k))
                report.add_text("%sValue: %s" % ("&nbsp;"*10, v))

            if test.expected_outcome == "Fires":
                exp_out = "Fires"
            elif test.expected_outcome == "FiresNot":
                exp_out = "Does NOT fire"
            else:
                exp_out = test.expected_outcome

            if test.outcome == "Fires":
                outcome = "Fires"
            elif test.outcome == "FiresNot":
                outcome = "Does NOT fire"
            else:
                outcome = "Undefinied"

            report.add_text("Expected result: %s" % exp_out)
            report.add_text("Actual result: %s" % outcome)
            report.add_spacer()
            if test.screenshot:
                report.add_image(test.screenshot)
            else:
                report.add_text("No screenshot yet")
        report.save()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Test(object):
    """ Test holds the test values for a rule as defined in the Excel scripts """
    def __init__(self, test_id, rule, expected_outcome, test_values=[]):
        self.test_id = test_id
        self.rule = rule
        self.expected_outcome = expected_outcome
        self.test_values = test_values
        self.outcome = ""
        self.screenshot = ""

    def passed(self):
        """ Determine of test passes. """
        return self.expected_outcome == self.outcome

    def run_test(self, browser):
        """ Run this test in an established browser session.

            It updates the test with the result, and a path to the screenshot
            of the result.
        """
        self.outcome, self.screenshot = browser.run_test(self)

    def __unicode__(self):
        return unicode(self.test_id)

    def __str__(self):
        return self.test_id


class Browser(object):
    """ Holds a selenium Firefox browser session for testing """
    def __init__(self, url, path):
        """ Starts a browser session with the
            OpenClinica instance defined in 'url'
        """
        if os.uname()[0] == 'Linux':
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()
        self.session = webdriver.Firefox()
        self.session.implicitly_wait(15)
        self.url = url
        self.screenshot_path = path

    def login(self, user, password):
        """ Login to the OpenClinica instance """
        try:
            self.session.get(self.url)
            self.session.find_element_by_name("j_username").send_keys(user)
            self.session.find_element_by_name("j_password").send_keys(password)
            self.session.find_element_by_name("submit").click()
        except:
            print "Unable to log in"
            sys.exit(1)

    def set_study(self, study):
        """ Change (if needed) to the study we want to use """
        # first see if we are already at the right study
        xpath_expr = "//div[@id='StudyInfo']/b/a"
        elem = self.session.find_element_by_xpath(xpath_expr)
        # if not, change the study
        if elem.text != study:
            self.session.find_element_by_link_text('Change Study/Site').click()
            try:
                xpath_expr = "//td/b[contains(text(),'%s')]/../input[@name='studyId']" % study
                self.session.find_element_by_xpath(xpath_expr).click()
                self.session.find_element_by_xpath(xpath_expr).click()
                self.session.find_element_by_name("Submit").click()
                self.session.find_element_by_name("Submit").click()
            except NoSuchElementException:
                print "Study not found!"
                sys.exit(1)

    def close(self):
        """ Close browser and display """
        self.session.close()
        if os.uname() == 'Linux':
            self.display.stop()

    def run_test(self, test):
        """ Runs one test for a rule in OpenClinica
            Input:  Test object and browser session
            Output: Result of running the test, and a path to
                    the screenshot of the result
        """

        scope = "?module=admin&maxRows=15&showMoreLink=true&\
                ruleAssignments_tr_=true&ruleAssignments_p_=1&\
                ruleAssignments_mr_=15&ruleAssignments_f_ruleName="
        rule_page = "%s%s%s%s" % (self.url, "ViewRuleAssignment", scope, test.rule)
        self.session.get(rule_page)
        screenshot = '%s/screenshot_%s.png' % (self.screenshot_path, test.test_id)
        # test if rule is found
        try:
            test_button = self.session.find_elements_by_xpath(
                    "//a[contains(@href, 'TestRule')]")
            test_button[1].click()
            self.session.find_elements_by_xpath(
                    "//input[@value='Validate & Test']")[0].click()
        except:
            self.session.save_screenshot(screenshot)
            return 'Undef', screenshot
        # Write values to test items
        for k, v in test.test_values.items():
            try:
                self.session.find_element_by_id(k).clear()
            except:
                self.session.save_screenshot(screenshot)
                return 'Undef', screenshot
            # Excel stores numbers as floats. Convert to integer if needed
            parts = str(v).split('.')
            try:
                if parts[1] == '0':
                    v = parts[0]
            except IndexError:
                pass
            try:
                self.session.find_element_by_id(k).send_keys(v)
            except:
                self.session.save_screenshot(screenshot)
                return 'Undef', screenshot
        try:
            self.session.find_elements_by_xpath(
                    "//input[@value='Validate & Test']")[0].click()
            self.session.save_screenshot(screenshot)
            action = self.session.find_elements_by_xpath(
                    "//*[contains(text(), 'Actions Fired')]/following-sibling::td")

            if action[0].text == 'N':
                result = "FiresNot"
            elif action[0].text == 'Y':
                result = "Fires"    
            else:
                result = "Undef"
        except:
            self.session.save_screenshot(screenshot)
            return 'Undef', screenshot
        return (result, screenshot)


class TestBattery(object):
    """ TestBattery holds all tests to be run for the study

        TestBattery is fed a path to and a list of Excel sheets that
        define the test to be run. TestBattery is a dictionary of
        page name and rule pairs. Rules have a list of tests that are
        relevant for that rule.
    """
    def __init__(self, path, scripts=[]):
        """ Initialize TestBattery by loading the test scripts
        
            Get the test scripts either from the parameter if available
            or find all the Excel sheets with tests in the specified folder (path)
        """
        self.tests = {}
        if scripts != []:
            test_scripts = sorted(scripts)
        else:
            test_scripts = sorted([file.split(".")[0] for file in os.listdir(path) if file.split(".")[1].lower()=="xls"])
        for page in test_scripts:
            self.load_script(page, "%s/%s.xls" % (path, page))    
    
    def load_script(self, page, xlfile, sheet=0):
        """ Loads tests from an Excel sheet.
        
            Rule objects are created, and tests are added to them.
            Returns a list of rules.
        """
        rule_list = []
        rules = xlrd.open_workbook(xlfile).sheet_by_index(sheet)
        rule_name = ""
        
        for rownum in range(rules.nrows)[1:]:
            test_vals = {}
            item_counter = 5
            while item_counter < len(rules.row_values(rownum)):
                key = rules.row_values(rownum)[item_counter]
                # it seems max number of filled columns is
                # used, shorter rows have therefore empty keys
                # and empty keys result in errors..
                if key != '':
                    test_vals[key] = ""
                    try:
                        val = rules.row_values(rownum)[item_counter+1]
                        test_vals[key] = val
                    except IndexError:
                        pass
                    item_counter += 2
                else:
                    break
            test_name = rules.row_values(rownum)[1]
            if rule_name != test_name:
                if rule_name != "":
                    rule_list.append(rule)
                rule_name = test_name
                rule_descr = rules.row_values(rownum)[2]
                rule = Rule(rule_name, rule_descr)
            test_id = rules.row_values(rownum)[0] 
            test_exp_outcome = rules.row_values(rownum)[4]
            rule.add_test(Test(test_id, rule_name, test_exp_outcome, test_vals))
            # testdata_ordered = sorted(testdata_list, key=lambda test_data: test_id)
        rule_list.append(rule)
        self.tests[page] = rule_list
    
    def validate(self, browser):
        """ Validate all test in the battery """
        for test in sorted(self.tests.values()):
            for rule in test:
                rule.validate(browser)
                
    def summary(self):
        """ Overview of rules per page """
        summary_per_page = {}
        totals = {}
        for page, rules in self.tests.items():
            summary_per_page[page] = {'rules': 0,
                                      'tests': 0,
                                      'valid_rules': 0,
                                      'passed_tests': 0,
                                      'failed_rules': []}
            test_fail = {}
            summary_per_page[page]['rules'] = len(rules)
            for rule in rules:
                summary_per_page[page]['tests'] += len(rule.tests)
                if rule.is_valid():
                    summary_per_page[page]['valid_rules'] += 1
                else:
                    summary_per_page[page]['failed_rules'].append(rule)
                for test in rule.tests:
                    if test.passed():
                        summary_per_page[page]['passed_tests'] += 1
        totals = {'rules': 0,
                  'tests': 0,
                  'valid_rules': 0,
                  'passed_tests': 0}               
        for page in summary_per_page:
            totals['rules'] += summary_per_page[page]['rules']
            totals['tests'] += summary_per_page[page]['tests']
            totals['valid_rules'] += summary_per_page[page]['valid_rules']
            totals['passed_tests'] += summary_per_page[page]['passed_tests']
        return summary_per_page, totals
    
    def summary_report(self, path):
        report = Report("%s/%s" % (path, "validation_overview.pdf"))
        report.add_text(OC['STUDY'], 18, 'Center')
        report.add_spacer(0.1*inch)
        report.add_text("Rules Validation Overview", 16, 'Center')
        report.add_spacer(0.1*inch)
        report.add_line()
        report.add_spacer(0.2*inch)
        summary_per_page, totals = self.summary()
        report.add_text("Test date: %s" % time.strftime("%d-%m-%Y"))
        report.add_text("&nbsp")
        try:
            report.add_text("Success rate: %3.1f%%" % (totals['valid_rules']/float(totals['rules'])*100))
        except ZeroDivisionError:
            # There are no rules yet
            report.add_text("Success rate: 0 %")
        report.add_text("&nbsp")
        report.add_text("Rules run: %d" % totals['rules'])
        report.add_text("Rules failed: %d" % (totals['rules']-totals['valid_rules']))
        report.add_text("&nbsp")
        report.add_text("Tests run: %d" % totals['tests'])
        report.add_text("Tests failed: %d" % (totals['tests']-totals['passed_tests']))
        if totals['tests']-totals['passed_tests']:
            report.add_new_page()
            report.add_text(OC['STUDY'], 14, 'Center')
            report.add_text("Overview failed tests", 12, 'Center')
            report.add_spacer(0.1*inch)
            report.add_line()
            report.add_spacer(0.1*inch)
            for page in sorted(summary_per_page):
                if summary_per_page[page]['failed_rules']:
                    report.add_text("%s:" % page)
                    for rule in summary_per_page[page]['failed_rules']:
                        report.add_text(", ".join(rule.get_failed_tests()))
                    report.add_text("&nbsp")
        report.save()
        
    def create_reports(self, report_path):
        """ Create all reports for test battery """
        
        # Create new folder 
        try:
            os.mkdir(report_path)
        except OSError:
            pass
        
        self.summary_report(report_path)
        
        for page, rules in self.tests.items():
            # Create subfolder for page
            output_path = "%s/%s" % (report_path, page)
            os.mkdir(output_path)
            for rule in rules:
                rule.create_report(output_path)
 
