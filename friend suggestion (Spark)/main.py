from pyspark import SparkContext
from operator import add

threshold = 10

# Pre-Existing Friend Pairs + All Possible Suggestions
def k(x):
    string = x.split()
    if len(string) == 1:
        output = [((string[0], string[0]), 1)] # so that it will be recognizable
        return output

    head = string[0]
    tale = string[1]
    tale = tale.split(",")
    output = []

    for firstItem in tale:
        output.append(((head, firstItem), -30000)) # already friends
        for secondItem in tale:
            if firstItem != secondItem:
                output.append(((firstItem, secondItem), 1)) # potential friends
    return output

# Sorting based on repetition
def j(x):
    if int(x[0]) != int(x[1][0][0]):
        xx = (x[0], sorted(x[1], key=lambda x: x[1], reverse=True) )
        output = "ID:" + xx[0] + "_" + "  "
        counter = 0
        for item in xx[1]:
            if counter < threshold:
                if counter == 0:
                    output = output + item[0]
                else:
                    output = output + "," + item[0]
            counter = counter + 1
    else:
        output = x[0] + "_"
    return output

# ------------ Input
sc = SparkContext("local", "FriendSuggestion")
raw = sc.textFile("q1_data.txt")

# ------------ Make Every possible Pair
suggestionsRaw = raw.flatMap(k)

# ------------ Remove existing pairs from suggestion + calculate repetition
suggestionsFiltered = suggestionsRaw.reduceByKey(add).filter(lambda x: x[1] > 0)

# ------------ Aggregate
suggestionsFilteredAgg = suggestionsFiltered.map(lambda x: (x[0][0], (x[0][1], x[1])) ).groupByKey().map(lambda x:(x[0],list(x[1])))

# ------------ Sort + policy
suggestionsRule = suggestionsFilteredAgg.map(j)

# ------------ Output
suggestionsRule.saveAsTextFile('output.txt')
