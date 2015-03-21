import urllib
import urllib2
import json
import sys
import argparse

INFOBOX = "INFOBOX"
QUESTION = "QUESTION"

#def makeQuery(key, query):
#    """
#    Sends the query to Bing
#    @param key The Bing key
#    @param query The query, as a string
#    @return The results list returned in JSON format, ie ['d']['results']
#    """
#    getQuery = {'Query': ('\'' + query + '\'')}
#    bingUrl = 'https://api.datamarket.azure.com/Bing/Search/Web?' \
#              + urllib.urlencode(getQuery) + '&$top=' \
#              + str(NUMRESULTS) + '&$format=json'
#    accountKeyEnc = base64.b64encode(key + ':' + key)
#    headers = {'Authorization': 'Basic ' + accountKeyEnc}
#    req = urllib2.Request(bingUrl, headers = headers)
#    response = urllib2.urlopen(req)
#    content = response.read()
#    json_content = json.loads(content)
#    return json_content['d']['results']
#
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

def usage():
    print "Usage: python query.py -key <Freebase API Key> -q <query> -t <infobox|question>"
    print "Usage: python query.py -key <Freebase API Key> -f <file of queries> -t <infobox|question>"
    print "Usage: python query.py -key <Freebase API Key>"

if __name__ == "__main__":
    """
    Entry point, processes parameters
    """

    parser = argparse.ArgumentParser(description="Does Freebase queries.")
    parser.add_argument("-key", required=True, dest="key")
    parser.add_argument("-q", dest="query")
    parser.add_argument("-f", dest="fileName")
    parser.add_argument("-t", dest="type")
    
