oc-rules-validation
# Validation tool for OpenClinica rules

Summary: 
Use test scripts to automatically validate your OpenClinica rules. All validation results are documented in generated PDF files.

Installation:
- install Python (https://www.python.org/downloads/)
- install virtualenv, if you want to keep this tool isolated (https://virtualenv.pypa.io/en/latest/)
- install headless firefox (apt-get install xvfb firefox / yum install Xvfb firefox)
- clone this repository
- if installed, activate your virtualenv
- install requirements (pip install -r requirements.txt)
- copy settings.py-initial to settings.py, edit settings.py to reflect your environment

Usage:
- download OC rules in Excel format. I suggest to do this in managable chunks, for example you can download them per page. It helps if your rules start with a descriptive prefix, like 'AE' for adverse event rules, or 'DEM' for rules on the demography page.
- transform the rules Excel sheet into an Excel test script by running the utility extract_rules.py, like so: 
```python extract_rules.py path/to/rules.xls /path/to/test_script.xls```
- enter the test values in the Excel script (see below)
- copy the test script(s) to the folder "test_scripts"
- run the validation. like so:
```python validate_rules.py``` 
(see below)
- find the results in the output folder as specified in settings.py

TODO: add instructions for Excel test script
TODO: add instructions for selecting which test files to run 
