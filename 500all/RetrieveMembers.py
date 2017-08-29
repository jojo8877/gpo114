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
            # self.pattern = re.compile(r".*COMMITTEE ON(.*)\n(.*\n){1,7}.*Chair.*\n", re.MULTILINE)
            self.pattern = re.compile(r"^(?: )*\n^(?: )*(?:HOUSE)?(?: )*(?:SELECT)?(?: )*((?:SUB)?COMMITTEE ON.*)\n(.*\n){0,5}.* Chair(wo)?(man)?(?:\s)*\n", re.MULTILINE | re.IGNORECASE)
            self.root = etree.parse('CommitteeMembership114.xml').getroot()
            self.errorCount = 0

    def findMembers(self, pfileName):
        with open(pfileName) as fileName:
            text = fileName.read()
            searchResult = self.pattern.findall(text)
            if (len(searchResult) <= 0):
                self.errorCount += 1
                return None, "", ""
            lastOccurredCommittee = self.pattern.findall(text)[-1][0]
            xpathString = ''
            if lastOccurredCommittee[0:3].lower() == "sub": # if subcommittee
                lastOccurredCommittee = lastOccurredCommittee[16:]
                if lastOccurredCommittee[0:15].lower() == "the departments":
                    lastOccurredCommittee = lastOccurredCommittee[19:]
                if lastOccurredCommittee == "Regulatory Reform, Commercial and Antitrust Law":
                    lastOccurredCommittee = "Regulatory Reform, Commercial, and Antitrust Law"
                xpathString = '//committee[@type="house"]/*[re:test(@displayname, "^' + lastOccurredCommittee.strip() + '.* Subcommittee", "i")]'
            else:
                if "BENGHAZI" in lastOccurredCommittee:
                    lastOccurredCommittee = "BENGHAZI"
                xpathString = '//*[re:test(@displayname, "HOUSE.*' + lastOccurredCommittee.strip() + '", "i")]'

            findCommittee = etree.XPath(xpathString, namespaces={"re": "http://exslt.org/regular-expressions"})

            for comm in findCommittee(self.root):
                committee_name = comm.get('displayname')
                committee_code = comm.get('code')
                if comm.tag == "subcommittee":
                    parent = comm.getparent()
                    committee_code = parent.get('code') + "-" + committee_code

            findMembers = etree.XPath(xpathString + "/member", namespaces={"re": "http://exslt.org/regular-expressions"})
            committee = {"name": [], "state": [], "level": [], "govtrack": []}
            for member in findMembers(self.root):
                memberId = member.get('id')
                memberRole = member.get('role')
                if memberRole is None:
                    memberRole = "Member"
                isMemberFound = False
                for rep in self.legi:
                    if rep['id']['govtrack'] == int(memberId):
                        fullName = rep['name']['official_full']
                        for term in rep['terms']:
                            if term['start'][0:4] == "2015" or term['start'][0:4] == "2016" or memberId == "412306":
                                state = term['state']
                                committee["name"].append(fullName)
                                committee["state"].append(state)
                                committee["level"].append(memberRole)
                                committee["govtrack"].append(memberId)
                                isMemberFound = True
                                break

                        break
                if not isMemberFound:
                    print("Error finding info for memberId: ", memberId)
            return committee, committee_name, committee_code



'''
retrieveMembers = RetrieveMembers()

for file in glob.glob("CHRG-114hhrg20596.txt"):
    print(file)
    com, com_name, com_code = retrieveMembers.findMembers(file)
    print(com)
    print(com_name, com_code)
    print('-----------------------------')
print('total errors: ', retrieveMembers.errorCount)
'''