#!path/to/python
import sys
import xlrd
import xlwt

class Rule(object):
    def __init__(self, name, message, expression, items):
        self.name = name
        self.message = message
        self.expression = expression
        self.items = items

def uniqify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x):
            return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result

def read_rules(rules):
    rule_list = []
    for rownum in range(rules.nrows)[1:]:
        if (rules.row_values(rownum)[13] != 'ShowAction' and
           rules.row_values(rownum)[8] == 'available'):
                name = rules.row_values(rownum)[6]
                message = " ".join(rules.row_values(rownum)[14].split())
                expression = rules.row_values(rownum)[10]
                items = uniqify([r for r in rules.row_values(rownum)[10]
                                 .replace('(', '')
                                 .replace(')', '')
                                 .split() if len(r) > 5])
                rule_list.append(Rule(name, message, expression, items))
    return rule_list

def create_tests(rule_list, xls_out):
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Tests")
    
    col = 0
    row = 1
    
    sheet.write(0, 0, "Test ID")
    sheet.write(0, 1, "Rule Name")
    sheet.write(0, 2, "Rule Message")
    sheet.write(0, 3, "Rule Expression")
    sheet.write(0, 4, "Expected Result")
    sheet.write(0, 5, "Rule Item")
    sheet.write(0, 6, "Rule Item Value")
    
    max_width = 0
    
    for r in rule_list:
        for x in range(len(r.items)):
            sheet.write(row, col, "%s_%02d" % (r.name, x + 1))
            sheet.write(row, col+1, r.name)
            sheet.write(row, col+2, r.message)
            sheet.write(row, col+3, r.expression)
            offset = 5
            for item in r.items:
                # sheet.write(0,col+offset,"Rule Item")
                sheet.write(row, col + offset, item)
                if max_width < len(item):
                    sheet.col(col+offset).width = (len(item) + 6) * 256
                    max_width = len(item)
    
                # sheet.write(0, col+offset+1, "Rule Item Value")
                sheet.col(col+offset+1).width = 20 * 256
    
                offset += 2  # skip a cell so that value can be entered
            row += 1
    workbook.save(xls_out)


if __name__ == '__main__':
    
    rule_list = []
    if len(sys.argv[1:]) != 2:
        print("Exactly two arguments expected")
        sys.exit(2)
    
    xls_in = sys.argv[1]
    xls_out = sys.argv[2]
    
    try:
        rules = xlrd.open_workbook(xls_in).sheet_by_index(0)
    except:
        print("input file not found")
        sys.exit(2)
        
    rule_list = read_rules(rules)
    create_tests(rule_list, xls_out)
