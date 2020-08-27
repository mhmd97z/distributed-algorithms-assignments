from pyspark import SparkContext
from operator import add

iterations = 4

def f(x):
    data2 = x[0].split(",")
    out_neighbor = []
    for i, item in enumerate(data2):
        if item == "1":
            out_neighbor.append(i)
    output = (str(x[1]), out_neighbor)
    return output

def g(x):
    if len(x[1][1]) == 0:
        return
    additional = x[1][0] / len(x[1][1])
    output = []
    for item2 in x[1][1]:
        output.append((str(item2), additional))
    return output

# ------------ Input
sc = SparkContext("local", "test")
data = sc.textFile("sample.csv").zipWithIndex()

# ------------ Calculate neighbors
vertexOutNbr = data.map(f)

# ----------- Rank initial
n = vertexOutNbr.count()
initial = n * [1 / n]
for i,item in enumerate(initial):
    initial[i] = [str(i), item]
rank = sc.parallelize(initial)

# -------------- Calculations
for i in range(iterations):
    augmentedData = rank.join(vertexOutNbr) # bring out neighbor and rank together
    rank = augmentedData.flatMap(g).reduceByKey(add).map(lambda x: (x[0], 0.85 * x[1] + 0.15 / n)) # rule

# -------------- Output
rank.saveAsTextFile('output.txt')
