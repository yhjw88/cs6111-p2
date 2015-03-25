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

def getOneInfoMult(container, multKeys):
    """
    Extension of getOneInfo()
    The multKeys is an array of arrays [[k11, k12, k13 ...], [k21, k22 ...] ...]
    This will return an array [element[k11][k12][k13]..., element[k21][k22]..., ...]
    None is added to each array for each missing element
    @param theList
    @param keys
    @return None if the array is only has None, or the array if it has atleast one not None element
    """
    elementArray = []
    for keys in multKeys:
        value = getOneInfo(container, keys)
        elementArray.append(value)
    empty = True
    for element in elementArray:
        if element:
            empty = False
            break
    if empty:
        return None
    else:
        return elementArray

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

def getListInfoMult(theList, multKeys):
    """
    Extension of getListInfo()
    The multKeys is an array of arrays [[k11, k12, k13 ...], [k21, k22 ...] ...]
    This iterates through the given list, and for each element
    It adds an array [element[k11][k12][k13]..., element[k21][k22]..., ...] to the returned list
    None is added to each array for each missing element
    Nothing is added to the returned list for every array that only contains None
    @param theList
    @param keys
    @return A list of arrays, each containing the specified member elements, or None if none
    """
    toReturn = []
    for container in theList:
        elementArray = getOneInfoMult(container, multKeys)
        if elementArray:
            toReturn.append(elementArray)
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
        name = "| " + name + ":"
        print name.ljust(20), value
        print " ----------------------------------------------------------------------------------"
    
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
    name = "| " + name + ":"
    for value in values: 
        print name.ljust(20), value
        name = ""
    print " ----------------------------------------------------------------------------------"

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
    print " ----------------------------------------------------------------------------------"
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

def printBusinessPersonInfo(properties):
    """
    Prints infobox info for entity type "BusinessPerson"
    @param properties
    """
    print "-----------"
    print "businessperson"
    print "-----------"

    # Board Leader (From, To, Organization, Role, Title)
    leadershipList = getOneInfo(properties, ["/business/board_member/leader_of", "values"])
    leadershipInfoLists = getListInfoMult(leadershipList,
        [["property", "/organization/leadership/from", "values", 0, "text"],
         ["property", "/organization/leadership/to", "values", 0, "text"],
         ["property", "/organization/leadership/organization", "values", 0, "text"],
         ["property", "/organization/leadership/role", "values", 0, "text"],
         ["property", "/organization/leadership/title", "values", 0, "text"]])
    for leadershipInfo in leadershipInfoLists:
        if leadershipInfo[2]:
            print "Leader of " + leadershipInfo[2]
        if leadershipInfo[0]:
            print "from: " + leadershipInfo[0]
        if leadershipInfo[1]:
            print "to: " + leadershipInfo[1]
        if leadershipInfo[3]:
            print "in role: " + leadershipInfo[3]
        if leadershipInfo[4]:
            print "with title: " + leadershipInfo[4]
        print "--------"

    # Board Member (From, To, Organization, Role, Title)
    boardMembershipList = getOneInfo(properties, ["/business/board_member/organization_board_memberships", "values"])
    boardMembershipInfoLists = getListInfoMult(boardMembershipList,
        [["property", "/organization/organization_board_membership/from", "values", 0, "text"],
         ["property", "/organization/organization_board_membership/to", "values", 0, "text"],
         ["property", "/organization/organization_board_membership/organization", "values", 0, "text"],
         ["property", "/organization/organization_board_membership/role", "values", 0, "text"],
         ["property", "/organization/organization_board_membership/title", "values", 0, "text"]])
    for membershipInfo in boardMembershipInfoLists:
        if membershipInfo[2]:
            print "Member of " + membershipInfo[2]
        if membershipInfo[0]:
            print "from: " + membershipInfo[0]
        if membershipInfo[1]:
            print "to: " + membershipInfo[1]
        if membershipInfo[3]:
            print "in role: " + membershipInfo[3]
        if membershipInfo[4]:
            print "with title: " + membershipInfo[4]
        print "--------"

    # Founded (OrganizationName)
    orgsFoundedList = getOneInfo(properties, ["/organization/organization_founder/organizations_founded", "values"])
    printListInfo(orgsFoundedList, ["text"], "Organizations Founded")


def printAuthorInfo(properties):
    """
    Prints infobox info for entity type "author"
    @param properties
    """
    print "-----------"
    print "author"
    print "-----------"

    # Books
    booksList = getOneInfo(properties, ["/book/author/works_written", "values"])
    printListInfo(booksList, ["text"], "Books Written")

    # Books about the Author
    booksAboutList = getOneInfo(properties, ["/book/book_subject/works", "values"])
    printListInfo(booksAboutList, ["text"], "Books about the Author")

    # Influenced
    influencedList = getOneInfo(properties, ["/influence/influence_node/influenced", "values"])
    printListInfo(influencedList, ["text"], "Influenced")

    # Influenced By
    influencedByList = getOneInfo(properties, ["/influence/influence_node/influenced_by", "values"])
    printListInfo(influencedByList, ["text"], "Influenced By")


def printActorInfo(properties):
    """
    Prints infobox info for entity type "actor"
    @param properties
    """

    print "-----------"
    print "actor"
    print "-----------"

    # Films Participated (Film Name, Character)
    filmList = getOneInfo(properties, ["/film/actor/film", "values"])
    if filmList:
        filmInfoLists = getListInfoMult(filmList,
            [["property", "/film/performance/film", "values", 0, "text"],
             ["property", "/film/performance/character", "values", 0, "text"]])
        for filmInfo in filmInfoLists:
            if filmInfo[0]:
                print "Acted in " + filmInfo[0]
            if filmInfo[1]:
                print "as character: " + filmInfo[1]
            print "--------"

def printLeagueInfo(properties):
    """
    Prints infobox info for entity type "league"
    @param properties
    """
    # Name, Sport 
    print "-----------------------------------------------------------------------------------"
    printOneInfo(properties, ["/type/object/name", "values", 0, "text"], "Name")
    printOneInfo(properties, ["/sports/sports_league/sport", "values", 0, "text"], "Sport")
    # Slogans
    slogansList = getOneInfo(properties, ["/organization/organization/slogan", "values"])
    printListInfo(slogansList, ["text"], "Slogans")
    # Official Websites
    websitesList = getOneInfo(properties, ["/common/topic/official_website", "values"])
    printListInfo(websitesList, ["text"], "Websites")
    # Championship
    printOneInfo(properties, ["/sports/sports_league/championship", "values", 0, "text"], "Championship")
    # Teams
    teamsList = getOneInfo(properties, ["/sports/sports_league/teams", "values"])
    printListInfo(teamsList, ["property", "/sports/sports_league_participation/team", "values", 0, "text"], "Teams")
    # Description
    printOneInfo(properties, ["/common/topic/description", "values", 0, "value"], "Description")

def printSportsTeamInfo(properties):
    """
    Prints infobox infor for entity type "sports team"
    @param properties
    """
    # Name, Sport, Founded
    print "-----------------------------------------------------------------------------------"
    printOneInfo(properties, ["/type/object/name", "values", 0, "text"], "Name")
    printOneInfo(properties, ["/sports/sports_team/sport", "values", 0, "text"], "Sport")
    printOneInfo(properties, ["/sports/sports_team/founded", "values", 0, "text"], "Founded")
    # Locations
    locationsList = getOneInfo(properties, ["/sports/sports_team/location", "values"])
    printListInfo(locationsList, ["text"], "Locations")
    # Arenas (Venues)
    arenasList = getOneInfo(properties, ["/sports/sports_team/venue", "values"])
    if arenasList:
        arenasInfo = getListInfoMult(arenasList, [["property", "/sports/team_venue_relationship/venue", "values", 0, "text"],
                                                  ["property", "/sports/team_venue_relationship/from", "values", 0, "text"],
                                                  ["property", "/sports/team_venue_relationship/to", "values", 0, "text"]])
        if arenasInfo:
            print "Arenas:"
            for arenaInfo in arenasInfo:
                if not arenaInfo[1]:
                    arenaInfo[1] = ""
                if not arenaInfo[2]:
                    arenaInfo[2] = ""
                if arenaInfo[0]:
                    print "%s (%s-%s)" % (arenaInfo[0], arenaInfo[1], arenaInfo[2])
            print "-----------"
    # Leagues
    leaguesList = getOneInfo(properties, ["/sports/sports_team/league", "values"])
    printListInfo(leaguesList, ["property", "/sports/sports_league_participation/league", "values", 0, "text"], "Leagues")
    # Championships
    championshipsList = getOneInfo(properties, ["/sports/sports_team/championships", "values"])
    printListInfo(championshipsList, ["text"], "Championships")
    # Coaches (Name, Position, From, To)
    coachesList = getOneInfo(properties, ["/sports/sports_team/coaches", "values"])
    if coachesList:
        coachesInfo = getListInfoMult(coachesList, [["property", "/sports/sports_team_coach_tenure/coach", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_coach_tenure/position", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_coach_tenure/from", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_coach_tenure/to", "values", 0, "text"]])
        if coachesInfo:
            print "Coaches:"
            for coachInfo in coachesInfo:
                if not coachInfo[0]:
                    continue
                toPrint = coachInfo[0]
                if coachInfo[1]:
                    toPrint += ", " + coachInfo[1]
                if not coachInfo[2]:
                    coachInfo[2] = ""
                if not coachInfo[3]:
                    coachInfo[3] = ""
                print "%s (%s-%s)" % (toPrint, coachInfo[2], coachInfo[3])
            print "-----------"
    # PlayersRoster (Name, Position, Number, From, To)
    playersList = getOneInfo(properties, ["/sports/sports_team/roster", "values"])
    if playersList:
        playersInfo = getListInfoMult(playersList, [["property", "/sports/sports_team_roster/player", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_roster/position", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_roster/number", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_roster/from", "values", 0, "text"],
                                                  ["property", "/sports/sports_team_roster/to", "values", 0, "text"]])
        if playersInfo:
            print "Players:"
            for playerInfo in playersInfo:
                if not playerInfo[0]:
                    continue
                toPrint = playerInfo[0]
                if playerInfo[1]:
                    toPrint += ", " + playerInfo[1]
                if playerInfo[2]:
                    toPrint += ", " + playerInfo[2]
                if not playerInfo[3]:
                    playerInfo[3] = ""
                if not playerInfo[4]:
                    playerInfo[4] = ""
                print "%s (%s-%s)" % (toPrint, playerInfo[3], playerInfo[4])
            print "-----------"
    # Description
    printOneInfo(properties, ["/common/topic/description", "values", 0, "value"], "Description")

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
        printAuthorInfo(properties)
    if entityTypes[ACTOR]:
        printActorInfo(properties)
    if entityTypes[BUSINESSPERSON]:
        printBusinessPersonInfo(properties)
    if entityTypes[LEAGUE]:
        printLeagueInfo(properties)
    if entityTypes[SPORTSTEAM]:
        printSportsTeamInfo(properties)

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
        print "unable to fetch results from freebase"
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
