import urllib
import urllib2
import json
import sys
import argparse

# Usage constants
INFOBOX = "infobox"
QUESTION = "question"
INTERACTIVE = "interactive"
USAGE = ("python query.py -key <Freebase API Key> -q <query> -t <infobox|question>\n"
        "       python query.py -key <Freebase API Key> -f <file of queries> -t <infobox|question>\n"
        "       python query.py -key <Freebase API Key>")
# Freebase Entity Types
PERSON = 0
AUTHOR = 1
ACTOR = 2
BUSINESSPERSON = 3
LEAGUE = 4
SPORTSTEAM = 5
FETTOINDEX = {
            "/people/person":PERSON,
            "/book/author":AUTHOR,
            "/film/actor":ACTOR,
            "/tv/tv_actor":ACTOR,
            "/organization/organization_founder":BUSINESSPERSON,
            "/business/board_member":BUSINESSPERSON,
            "/sports/sports_league":LEAGUE,
            "/sports/sports_team":SPORTSTEAM,
            "/sports/professional_sports_team":SPORTSTEAM
            }

def getOneInfo(container, keys):
    """
    Given a dictionary or list c and the array of keys [k1, k2, k3 ...]
    This will return the member of the container c[k1][k2][k3]... if it exists
    If not, it just returns None
    @param container
    @param keys
    @return None if none, or the member of the dictionary if it exists
    """
    current = container
    for key in keys:
        if isinstance(current, dict): 
            if key in current:
                current = current[key]
            else:
                return None
        elif (key < len(current)):
            current = current[key]
        else:
            return None

    return current

def getListInfo(theList, keys):
    """
    Given the containing list l, and array of keys [k1, k2, k3 ...]
    This iterates through that list, and for each element
    It adds element[k1][k2][k3] ... to the returned list
    @param theList
    @param keys
    @return A list of the member elements, or None if none
    """
    toReturn = []
    for container in theList:
        value = getOneInfo(container, keys)
        if value:
            toReturn.append(value)
    if len(toReturn) == 0:
        return None
    return toReturn

def printOneInfo(properties, keys, name):
    """
    Given the list of properties and the array of keys [k1, k2, k3 ...]
    This will print the infobox entry located at properties[k1][k2][k3]... if it exists
    It prints nothing if the entry doesn't exist
    @param properties
    @param keys
    @param name The name given to the infobox entry to be printed out
    """
    # TODO: Needs to print in prettier fashion
    value = getOneInfo(properties, keys)
    if value:
        print "%s: \n%s" % (name, value)
        print "-----------"

def printListInfo(theList, keys, name):
    """
    Given the containing list l, and array of keys [k1, k2, k3 ...]
    This iterates through that list, and for each element
    It prints element[k1][k2][k3] ... if it exists
    If theList is None, or there is no info to print, nothing is printed
    @param theList
    @param keys
    @param name The name given to the infobox entry to be printed out
    """
    # TODO: Needs to print in prettier fashion
    if not theList:
        return
    values = getListInfo(theList, keys)
    if not values:
        return
    print "%s:" % name
    for value in values: 
        print value
    print "-----------"

def getAnswer(query, key):
    # extract entity from question query
    entity = query[12:]
    entity = entity[:-1]

    # search for authors with written works whose name contains the entity
    service_url = 'https://www.googleapis.com/freebase/v1/mqlread'
    query1 = [{
                "/book/author/works_written": [{
                  "a:name": None,
                  "name~=": entity
                }],
                "name": None,
                "type": "/book/author"
              }]
    params1 = {
                'query': json.dumps(query1),
                'key': key
              }
    url1 = service_url + '?' + urllib.urlencode(params1)
    response1 = json.loads(urllib.urlopen(url1).read())

    # search for organization founders with organizations whose name contains the entity
    query2 = [{
                "/organization/organization_founder/organizations_founded": [{
                  "a:name": None,
                  "name~=": entity
                }],
                "name": None,
                "type": "/organization/organization_founder"
              }]
    params2 = {
                'query': json.dumps(query2),
                'key': key
              }
    url2 = service_url + '?' + urllib.urlencode(params2)
    response2 = json.loads(urllib.urlopen(url2).read())

    # merge the two responses and sort by creator name
    response = response1["result"] + response2["result"]
    response.sort(key=lambda x: x["name"])

    # output the results
    # TODO: format output as "first, second, ..., and last"
    i = 1
    for creator in response:
        out = str(i) + ". " + creator['name']
        if creator['type'] == "/book/author":
            out = out + " (as Author) created "
            for work in creator["/book/author/works_written"]:
                out = out + "<" + work["a:name"] + ">, "
        elif creator['type'] == "/organization/organization_founder":
            out = out + " (as BusinessPerson) created "
            for org in creator["/organization/organization_founder/organizations_founded"]:
                out = out + "<" + org["a:name"] + ">, "
        print out
        i = i + 1

def freebaseSearch(query, key):
    """
    Queries the Freebase Search API
    @param query
    @param key
    @return The result array of results, or None if none
    """
    freebaseUrl = "https://www.googleapis.com/freebase/v1/search"
    params = {"query": query, "key": key}
    url = freebaseUrl + '?' + urllib.urlencode(params)
    html = ""
    try:
        response = urllib2.urlopen(url)
        html = response.read()
    except urllib2.URLError as e:
        print "Error with Freebase Search URL request: %s" % e.reason
        return None

    jsonResults = json.loads(html)
    results = jsonResults["result"]
    if len(results) == 0:
        print "No results for query: %s" % query
        return None

    return results

def getEntityTypes(properties):
    """
    Given the property portion from the Freebase Topic query
    This will return an array
    True is stored at the index of each corresponding entity type found
    @param properties
    @return The boolean array entityTypes
    """
    entityTypes = [False] * 6
    values = properties["/type/object/type"]["values"]

    for value in values:
        if value["id"] in FETTOINDEX:
            entityTypes[FETTOINDEX[value["id"]]] = True

    return entityTypes

def printPersonInfo(properties):
    """
    Prints infobox info for entity type "person"
    @param properties
    """
    # Name, Birthday, Place of Birth
    print "-----------"
    printOneInfo(properties, ["/type/object/name", "values", 0, "text"], "Name")
    printOneInfo(properties, ["/people/person/date_of_birth", "values", 0, "text"], "Birthday")
    printOneInfo(properties, ["/people/person/place_of_birth", "values", 0, "text"], "Place of Birth")
    # Death
    printOneInfo(properties, ["/people/deceased_person/date_of_death", "values", 0, "text"], "Death Date")
    printOneInfo(properties, ["/people/deceased_person/place_of_death", "values", 0, "text"], "Place of Death")
    deathCauseList = getOneInfo(properties, ["/people/deceased_person/cause_of_death", "values"])
    printListInfo(deathCauseList, ["text"], "Causes of Death")
    # Siblings
    siblingsList = getOneInfo(properties, ["/people/person/sibling_s", "values"])
    printListInfo(siblingsList, ["property", "/people/sibling_relationship/sibling", "values", 0, "text"], "Siblings")
    # Spouses
    spousesList = getOneInfo(properties, ["/people/person/spouse_s", "values"]) 
    printListInfo(spousesList, ["property", "/people/marriage/spouse", "values", 0, "text"], "Spouses")
    # Description
    printOneInfo(properties, ["/common/topic/description", "values", 0, "value"], "Description")

def printLeagueInfo(properties):
    """
    Prints infobox info for entity type "league"
    @param properties
    """
    # Name, Sport 
    printOneInfo(properties, ["/type/object/name", "values", 0, "text"], "Name")
    printOneInfo(properties, ["/sports/sports_league/sport", "values", 0, "text"], "Sport")
    # Slogans
    slogansList = getOneInfo(properties, ["/organization/organization/slogan", "values"])
    printListInfo(slogansList, ["text"], "Slogans")
    # Official Websites
    # Championship

def freebaseTopic(mid, key):
    """
    Queries the Freebase Topic API for infobox
    Will return True iff successfully finds entity and prints out infobox
    @param mid
    @return True if successful, False if failed
    """
    # Query Freebase Topic
    freebaseUrl = "https://www.googleapis.com/freebase/v1/topic" + mid
    params = {"key": key}
    url = freebaseUrl + '?' + urllib.urlencode(params)
    html = ""
    try:
        response = urllib2.urlopen(url)
        html = response.read()
    except urllib2.URLError as e:
        print "Error with Freebase Topic URL request: %s" % e.reason
        return False
    results = json.loads(html)
    if "property" not in results:
        return False
    properties = results["property"]

    # Get entity types
    entityTypes = getEntityTypes(properties)
    success = False
    for value in entityTypes:
        if value:
            success = True
            break
    if not success:
        return False

    # Print the properties given the entity type
    if entityTypes[PERSON]:
        printPersonInfo(properties)
    if entityTypes[AUTHOR]:
        print "Author"
    if entityTypes[ACTOR]:
        print "Actor"
    if entityTypes[BUSINESSPERSON]:
        print "Business Person"
    if entityTypes[LEAGUE]:
        printLeagueInfo(properties)
    if entityTypes[SPORTSTEAM]:
        print "Sports Team"

    return True

def getInfobox(query, key):
    """
    Makes the query and displays the infobox before returning
    @param query
    @param key
    @return True if successful, False if failed
    """
    results = freebaseSearch(query, key)
    if not results:
        return False

    success = False
    for result in results:
        success = freebaseTopic(result["mid"], key)
        if success:
            break
    if not success:
        print "No entities of interest matching the given query: %s" % query
        return False

    return True

if __name__ == "__main__":
    """
    Entry point, processes parameters
    """

    # Argument parsing
    parser = argparse.ArgumentParser(description="Does Freebase queries.", usage=USAGE)
    parser.add_argument("-key", required=True, dest="key")
    parser.add_argument("-q", dest="query")
    parser.add_argument("-f", dest="fileName")
    parser.add_argument("-t", dest="queryType", choices=[INFOBOX, QUESTION])
    args = parser.parse_args()
    if (args.query or args.fileName) and not args.queryType:
        parser.error("-t must be set in order to use -q or -f")
    if not (args.query or args.fileName) and args.queryType:
        parser.error("-q or -f must be set in order to use -t")
    if args.query and args.fileName:
        parser.error("-q and -f cannot both be set")

    # Do actual work
    # TODO: Do file and question mode
    # TODO: Apparently interactive mode not required so...
    if args.query and args.queryType == INFOBOX:
        getInfobox(args.query, args.key)
    elif args.query and args.queryType == QUESTION:
        getAnswer(args.query, args.key)

