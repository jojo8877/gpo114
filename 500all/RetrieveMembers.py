import re
from lxml import etree
import json
import glob

class RetrieveMembers:
    def __init__(self):
        with open('legislators-current.json') as current,\
             open('legislators-historical.json') as historical:
            legiCurrent = json.load(current)
            legiHistorical = json.load(historical)
            self.legi = legiCurrent + legiHistorical
            self.pattern = re.compile(r".*COMMITTEE ON(.*)\n(.*\n){1,7}.*Chair.*\n", re.MULTILINE)
            self.root = etree.parse('CommitteeMembership114.xml').getroot()
            self.errorCount = 0

    def findMembers(self, pfileName):
        with open(pfileName) as fileName:
            text = fileName.read()
            searchResult = self.pattern.findall(text)
            if (len(searchResult) <= 0):
                print('Error: ', pfileName)
                self.errorCount += 1
                return
            lastOccurredCommittee = self.pattern.findall(text)[-1][0]
            xpathString = '//*[re:test(@displayname, ".*' + lastOccurredCommittee.strip() + '.*", "i")]/member'
            findMembers = etree.XPath(xpathString, namespaces={"re": "http://exslt.org/regular-expressions"})
            for member in findMembers(self.root):
                memberId = member.get('id')
                for rep in self.legi:
                    if (rep['id']['govtrack'] == int(memberId)):
                        print(rep['name']['last'])



retrieveMembers = RetrieveMembers()

for file in glob.glob("CHRG-114hhrg*.txt"):
    print(file)
    retrieveMembers.findMembers(file)
    print('-----------------------------')
print('total errors: ', retrieveMembers.errorCount)

