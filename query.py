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
                  "name~=": "Google"
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


#def search(key, precision, query):
#    """
#    Performs the actual loop of querying, asking user, query expansion
#    Assumes that the params passed in are valid
#    @param key The Bing key
#    @param precision The requested precision, as a float
#    @param query The initial user query
#    """
#    numRelevant = 0
#    while True:
#        print ""
#        print "======================"
#        print "Query: " + query
#        results = makeQuery(key, query)
#        numItems = 0
#        numRelevant = 0
#
#        print "======================"
#        print "y = relevant"
#        print "n = not relevant"
#        print "Anything else = quit"
#        print "======================"
#        for item in results:
#            numItems += 1
#            print "Result " + str(numItems)
#            print "["
#            print " URL: " + item['Url']
#            print " Title: " + item['Title']
#            print " Summary: " + item['Description']
#            print "]\n"
#            relevant = raw_input("Relevant (y/n)?")
#            if relevant == 'Y' or relevant == 'y':
#                item['relevant'] = 1
#                numRelevant += 1
#            elif relevant == 'N' or relevant == 'n':
#                item['relevant'] = 0
#            else:
#                print "Bye!"
#                return
#
#        if (numItems < NUMRESULTS):
#            print "Error: Not enough results, only %d found" % numItems
#            return
#        if (numRelevant <= 0):
#            print "Error: Nothing was marked relevant, exiting"
#            return
#        print "Query: %s" % query
#        print "Precision: %.1f" % (numRelevant / float(NUMRESULTS))
#        if numRelevant < precision * NUMRESULTS:
#            docs = strip_docs(results)
#            termScores = getScores(query, docs)
#            if numRelevant < 2:
#                query = expandQueryRocchio(query, termScores)
#            else:
#                query = expandQueryClique(query, termScores, docs)
#            query = orderQuery(query, docs)
#        else:
#            print "Precision reached, exiting"
#            return

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

    # Get Entity Types
    entityTypes = getEntityTypes(properties)
    success = False
    for value in entityTypes:
        if value:
            success = True
            break
    if not success:
        return False

    # TODO: Formatting
    # TODO: Get infobox properties
    if entityTypes[PERSON]:
        print "Person"
    if entityTypes[AUTHOR]:
        print "Author"
    if entityTypes[ACTOR]:
        print "Actor"
    if entityTypes[BUSINESSPERSON]:
        print "Business Person"
    if entityTypes[LEAGUE]:
        print "League"
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

