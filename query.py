import urllib
import urllib2
import json
import sys
import argparse

INFOBOX = "infobox"
QUESTION = "question"
INTERACTIVE = "interactive"
USAGE = ("python query.py -key <Freebase API Key> -q <query> -t <infobox|question>\n" 
        "       python query.py -key <Freebase API Key> -f <file of queries> -t <infobox|question>\n" 
        "       python query.py -key <Freebase API Key>")

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
    
    response = json.loads(html)
    results = response["result"]
    if len(results) == 0:
        print "No results for query \"%s\"" % query
        return None
    
    return results

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

    print json.dumps(results, indent=4)

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
