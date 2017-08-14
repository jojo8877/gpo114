import re

committeePattern = re.compile(r".*COMMITTEE ON(.*)\n(.*\n){1,2}.*Chairman\n", re.MULTILINE)

with open("CHRG-114hhrg99744.txt") as f:
    text = f.read()
    for match in committeePattern.finditer(text):
        print (match.group(1))