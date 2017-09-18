import os  # operating system, for file and directory manipulation
import pandas as pd  # panal data, for dealing with data frame in a convenient way
import re  # regular expression
from nltk import tokenize  # natural language toolkit, for sentence tokenization
import RetrieveMembers

states = ['Alaska', 'Alabama', 'Arkansas', 'American Samoa', 'Arizona', 'California', 'Colorado', 'Connecticut',
          'District of Columbia', 'Delaware', 'Florida',
          'Georgia', 'Guam', 'Hawaii', 'Iowa', 'Idaho', 'Illinois', 'Indiana', 'Kansas', 'Kentucky', 'Louisiana',
          'Massachusetts', 'Maryland', 'Maine', 'Michigan', 'Minnesota',
          'Missouri', 'Northern Mariana Islands', 'Mississippi', 'Montana', 'National', 'North Carolina',
          'North Dakota', 'Nebraska', 'New Hampshire', 'New Jersey',
          'New Mexico', 'Nevada', 'New York', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico',
          'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee',
          'Texas', 'Utah', 'Virginia', 'Virgin Islands', 'Vermont', 'Washington', 'Wisconsin', 'West Virginia',
          'Wyoming', 'UT', 'TX']  # all states in US

Title = ["Mr.", "Ms.", "Mrs.", "Dr.", "Chairman", "Vice Chair", "Senator", "Mayor", "Commissioner", "Representative",
         "Lieutenant", "Reverend",
         "Secretary", "Sheriff", "Chief", "Admiral", "Judge", "Rev.", "Cardinal",
         "Bishop"]  # titles I've found by going through all files

specialFiles = ["CHRG-109hhrg31460.txt", "CHRG-109hhrg31575.txt",
                "CHRG-113hhrg80823.txt"]  # In these files, speaker names are in upper cases in Speeches.

politicianWords = ["Representative", "Senator"]  # Words that would indicate a witness as a politician

multiple = ["CHRG-108hhrg92120.txt", "CHRG-108hhrg94287.txt", "CHRG-109hhrg31575.txt", "CHRG-110hhrg35275.txt"]


def convertName(s):  # A function for converting names of different formats into the properly captalized format.
    result = []  # Most names in the list of committee members are all in upper case like "SMITH" or "DelBENE". While some are already captalized.
    for word in s.split():
        if word.istitle():
            result.append(word)
        elif word.isupper():
            result.append(word.title())
        else:
            converted = word[0]
            for i in range(1, len(word)):
                if word[i].islower():
                    converted += word[i]
                else:
                    if word[i - 1].islower():
                        converted += word[i]
                    else:
                        converted += word[i].lower()
            result.append(converted)
    return " ".join(result)


def parseInfo(
        s):  # Split typical committee member information in the format of "Full Name, State, (Optional: Ranking Member)"
    if s == "":
        return
    if "," not in s:
        return
    name = convertName(s.split(",")[0].strip())
    for item in s.split(","):
        if item.strip() in states:
            state = item.strip()
    if s.split(",")[-1].strip() not in states:
        level = s.split(",")[-1].strip()
    else:
        level = "Member"
    if "state" in locals():
        return name, state, level


def isNewParagraph(
        s):  # Determine whether a line indicates new paragraph by checking whether there are exactly 4 spaces at the beginning of the line.
    if len(s.strip()) > 0:
        if len(s) > 4:
            if s[:4] == "    " and s[4].isupper():
                return True
    return False


def startsWithTitle(
        s):  # Determine whether a line starts with a title. Only lines starting with a title may indicate a switch of speaker.
    for item in Title:
        if item in s:
            if s.strip().startswith(item):
                return True
    return False


def removeTitle(s):  # Remove title from a string so that only the last name of the speaker is left.
    for item in Title:
        if item in s:
            return s.replace(item, "").replace("[continuing]", "").replace("[presiding]", "").replace(".", "").strip()
    return s.replace(item, "").replace("[continuing]", "").replace("[presiding]", "").replace(".", "").strip()


def isName(
        s):  # Determine whether a string looks like a name by checking if the first letter is in upper case and second letter is in lower case.
    if "," in s:
        return False
    if "of" in s:  # Sometimes there is expressions like Mr. Smith of Texas or Mrs. Davis of California.
        s.replace("of", "")
    for item in s.split():
        if item.isupper():
            return True
        if item[0].islower() or item[1].isupper():
            return False
    return True


def isNewSpeaker(s):  # Determine whether this line switches speaker.
    if isNewParagraph(s):
        if "Rev." in s:  # The period in the title affects sentence tokenization. So get rid of the period.
            s.replace("Rev.", "Reverend")
        tokenized = tokenize.sent_tokenize(s)
        if len(tokenized) > 1:
            if startsWithTitle(tokenized[0]):
                if tokenized[0][-1] == ".":
                    if thisFile in specialFiles:
                        if removeTitle(tokenized[0]).isupper():
                            return True
                    if isName(removeTitle(tokenized[0])):
                        return True
            elif tokenized[0] == "The Chairman.":
                return True
    return False


def addSpeechToSpeaker(speakerName, speech,
                       initialCount=1):  # When a new speaker or new speech is identified, add the speaker and speech to our record.
    if speakerName not in df[thisFile]["last_name"]:  # A new speaker never recorded in this hearing is detected.
        df[thisFile]["last_name"].append(speakerName)
        df[thisFile]["speeches"].append(speech)
        df[thisFile]["num_speeches"].append(initialCount)

        df[thisFile]["document"].append(thisFile)
        df[thisFile]["num_congress"].append(thisNumber)
        df[thisFile]["chamber"].append(thisChamber)
        df[thisFile]["date"].append(thisDate)
        df[thisFile]["title"].append(thisTitle)
        df[thisFile]["committee"].append(thisCommittee)

        if len(presentInfo) < 1:
            df[thisFile]["presentInfo"].append(0)
        else:
            df[thisFile]["presentInfo"].append(1)

        if thisFile in multiple:
            df[thisFile]["multiple"].append(1)
        else:
            df[thisFile]["multiple"].append(0)

        if speakerName in witnessInfo:  # This speaker is a witness.
            df[thisFile]["name"].append("")
            df[thisFile]["identity"].append("Witness")
            df[thisFile]["description"].append("")
            df[thisFile]["state"].append("")
        else:
            for i in range(len(committee["last"])):
                if speakerName in committee["last"][i]:  # This speaker is a committee member.
                    df[thisFile]["name"].append(committee["last"][i])
                    df[thisFile]["identity"].append("Committee" + committee["level"][i])
                    df[thisFile]["description"].append("")
                    df[thisFile]["state"].append(committee["state"][i])
                    return
            df[thisFile]["name"].append("")  # Neither a witness nor committee member.
            df[thisFile]["identity"].append("")
            df[thisFile]["description"].append("")
            df[thisFile]["state"].append("")
    else:  # Add speeches to existing speakers.
        thisIndex = df[thisFile]["last_name"].index(speakerName)
        df[thisFile]["speeches"][thisIndex] += speech
        df[thisFile]["num_speeches"][thisIndex] += 1

def findSpeakerFromCommittee(speaker):
    for index, person in enumerate(committee['last']):
        if speaker.upper() in person.upper():
            return committee['first'][index], person, committee['govtrack'][index], committee['level'][index]
    return "", speaker, "N/A", ""


if __name__ == "__main__":

    directory = "."  # A default directory if no directory is given in previous step.

    hearingInfo = pd.DataFrame.from_csv(directory + "/300part_list.csv")  # Previously worked out.

    info = pd.DataFrame()  # An empty data frame. Will contain information for all hearings.

    allSpeeches = pd.DataFrame() # data frame that contains all speeches

    files = []  # A list of txt files in the directory.

    filesProcessed = 0

    for file in os.listdir(directory):  # Get a list of names for all text files in this directory
        if file.endswith(".txt"):
            files.append(file)

    df = {}  # A Python dictionary of all hearings' information. Can be retrieved later for debugging.

    for thisFile in files:
        f = open(directory + "/" + thisFile)

        # Construct a dictionary for current hearing. Will be made into data frame later.
        df[thisFile] = {"document": [],
                        "num_congress": [],
                        "chamber": [],
                        "date": [],
                        "multiple": [],
                        "presentInfo": [],
                        "title": [],
                        "committee": [],
                        "name": [],
                        "last_name": [],
                        "identity": [],
                        "description": [],
                        "state": [],
                        "num_speeches": [],
                        "speeches": []}

        thisNumber = int(thisFile.split("-")[1][:3])  # Number of this congress hearing
        thisChamber = hearingInfo.loc[hearingInfo["FileName"] == thisFile]["Chamber"][0]  # Chamber of this hearing
        thisDate = hearingInfo.loc[hearingInfo["FileName"] == thisFile]["Date"][0]  # Date of this hearing
        thisTitle = hearingInfo.loc[hearingInfo["FileName"] == thisFile]["Title"][0].split("-")[-1].strip()
        thisCommittee = hearingInfo.loc[hearingInfo["FileName"] == thisFile]["Committee"][0]  # Title of this hearing

        committee = {"name": [], "state": [],
                     "level": []}  # save the committee members' information of this hearing tempoparily.
        length = 0
        COMMITTEE = 0

        speeches = {"committee_name": [],
                    "committee_code": [],
                    "file_name": [],
                    "title": [],
                    "govtrack": [],
                    "ranking": [],
                    "speaker_last": [],
                    "speaker_first": [],
                    "speech": []}  # Save the speeches and speakers temporarily. Will be saved as the hearing segmented by speakers.
        isSpeech = False
        skip = True

        isWitness = False

        isPresent = False
        presentInfo = ""
        retrieveMembers = RetrieveMembers.RetrieveMembers()
        committee, committee_name, committee_code = retrieveMembers.findMembers(thisFile)
        if committee is None:
            print("Error processing ", thisFile)
            continue
        if len(committee["govtrack"]) == 0:
            print("Empty committee list ", thisFile)
            continue

        for line in f:  # Read the current file line by line.

            if "WITNESS" in line or "PRESENTER" in line or "Witness" in line:  # Indicate the witnesses are listed in the next block
                isWitness = True
                witnessInfo = ""
                witnessSpace = 0
            if isWitness and "WITNESS" not in line:  # There is a blank line between WITNESS and main body of witness information.
                if line in ['\n', '\r\n']:
                    witnessSpace += 1
                if witnessSpace == 2:  # Another blank line indicates the end of witness information.
                    isWitness = False
                # Parse witnessInfo here. Too different to parse.
                if len(line.split()) > 0 and witnessSpace == 1:
                    witnessInfo += line

            if "met, pursuant to" in line or "convened, pursuant to" in line or "Washington, DC." in line or "met, Pursuant to" in line:
                isSpeech = True
                speech = ""
                thisSpeaker = ""

            if "Whereupon" in line and "adjourned" in line:  # At the end of hearing, there is "Whereupon, the committee was adjourned."
                isSpeech = False
                thisSpeakerFirst, thisSpeakerLast, thisSpeakerGovtrack, thisRanking = findSpeakerFromCommittee(thisSpeaker)
                speeches['committee_name'].append(committee_name)
                speeches['committee_code'].append(committee_code)
                speeches['file_name'].append(thisFile)
                speeches['title'].append(thisTitle)
                speeches['govtrack'].append(thisSpeakerGovtrack)
                speeches['ranking'].append(thisRanking)
                speeches["speaker_last"].append(thisSpeakerLast)
                speeches["speaker_first"].append(thisSpeakerFirst)
                speeches["speech"].append(speech)
                addSpeechToSpeaker(thisSpeaker, speech)
                print "Finished analyzing %s" % thisFile
                filesProcessed += 1

            if isNewParagraph(line) and line.split()[
                0] == "Present:":  # The paragraph indicating the committee members present.
                isPresent = True
            if isPresent:
                if len(presentInfo) > 0 and (isNewParagraph(line) or line in ["\n", "\r\n"]):
                    isPresent = False
                    splitedInfo = presentInfo.replace("Present: ", "").replace("Representatives", "").replace(
                        "Representative", "").replace("Senators", "").replace("Senator", "").replace("and",
                                                                                                     ",").replace(".",
                                                                                                                  "").split(
                        ",")
                    # The list of name starts with "Senators", "Representatives", "Representatives", "Senator"
                    committeePresent = [item.strip() for item in splitedInfo]
                    if "" in committeePresent:
                        committeePresent.remove("")
                    for present in committeePresent:
                        addSpeechToSpeaker(present, "", 0)
                else:
                    presentInfo += line.strip()

            if isSpeech and "[" in line and "follows:]" in line:  # Skip the prepared statements, graph, etc.
                skip = True
            if isSpeech and skip and isNewSpeaker(line):  # Stop skipping when a new speaker starts speaking.
                skip = False

            if isSpeech:
                if not skip:
                    if isNewSpeaker(
                            line):  # If a new speaker is detected, save the latest speech to the previous speaker
                        if thisSpeaker != "":
                            thisSpeakerFirst, thisSpeakerLast, thisSpeakerGovtrack, thisRanking = findSpeakerFromCommittee(thisSpeaker)
                            speeches['committee_name'].append(committee_name)
                            speeches['committee_code'].append(committee_code)
                            speeches['file_name'].append(thisFile)
                            speeches['title'].append(thisTitle)
                            speeches['govtrack'].append(thisSpeakerGovtrack)
                            speeches['ranking'].append(thisRanking)
                            speeches["speaker_last"].append(thisSpeakerLast)
                            speeches["speaker_first"].append(thisSpeakerFirst)
                            speeches["speech"].append(speech)
                            addSpeechToSpeaker(thisSpeaker, speech)

                            speech = line.replace("\r\n", "").replace("\n", "")
                            if tokenize.sent_tokenize(line)[0] == "The Chairman.":
                                thisSpeaker = committee["name"][committee["level"].index("Chairman")].split()[-1]
                            elif line.strip().startswith("Rev."):
                                thisSpeaker = removeTitle(tokenize.sent_tokenize(line)[1])
                            else:
                                thisSpeaker = removeTitle(tokenize.sent_tokenize(line)[0])
                        else:
                            speech += line.replace("\r\n", "").replace("\n", "")
                            if tokenize.sent_tokenize(line)[0] == "The Chairman.":
                                thisSpeaker = committee["name"][committee["level"].index("Chairman")].split()[-1]
                            elif line.strip().startswith("Rev."):
                                thisSpeaker = removeTitle(tokenize.sent_tokenize(line)[1])
                            else:
                                thisSpeaker = removeTitle(tokenize.sent_tokenize(line)[0])
                    else:
                        if not line.isupper():
                            speech += line.replace("\r\n", "").replace("\n", "")
                        # If new speaker is not detected, add the current line to the ongoing speech, if the line is not in all upper case letters.

        # Iteration through all lines in a file ends.
        # write out segmented speeches for each speaker in this document
        if not os.path.isdir(directory + "/speeches"):
            os.makedirs(directory + "/speeches")
        for i in range(len(df[thisFile]["last_name"])):
            FileName = thisFile.replace(".txt", "_") + df[thisFile]["last_name"][i] + ".txt"
            with open(directory + "/speeches/" + FileName, "w") as text_file:
                text_file.write(re.sub(r'\[.+?\]\s*', '', df[thisFile]["speeches"][i]))

        # write out segmented speeches for this document
        if not os.path.isdir(directory + "/speech_level"):
            os.makedirs(directory + "/speech_level")

        thisDf = pd.DataFrame(speeches, columns=["committee_name", "committee_code", "file_name", "title", "govtrack", "ranking", "speaker_last", "speaker_first", "speech"])
        thisDf = thisDf.applymap(lambda x: x.encode('unicode_escape').decode('utf-8') if isinstance(x, str) else x)
        allSpeeches = pd.concat([allSpeeches, thisDf])
        thisDf.to_excel(directory + "/speech_level/speeches_" + thisFile.replace("txt", "xlsx"))

        df[thisFile]["order"] = range(1, len(df[thisFile]["document"]) + 1)
        info = pd.concat([info, pd.DataFrame(df[thisFile],
                                             columns=["order", "document", "num_congress", "chamber", "date",
                                                      "multiple",
                                                      "presentInfo", "title", "committee", "name", "last_name",
                                                      "identity", "description", "state", "num_speeches"])])

        f.close()

    # Iteration through all files ends.
    # write out the overall information for all documents
    info.to_excel(directory + "/info.xlsx", index=False)

    # export allSpeeches to excel
    allSpeeches.to_excel(directory + "/allspeeches.xlsx")
    allSpeeches.to_csv(directory + "/allspeeches.csv", encoding='utf-8')
    print("total files processed:", filesProcessed)

    for file in os.listdir(directory + "/speeches/"):
        if file.endswith(".txt"):
            if file.split("_")[1] == ".txt":
                print "Removing file %s" % file
                os.remove(directory + "/speeches/" + file)
