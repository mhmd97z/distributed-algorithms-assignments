`These assignments were part of my undergrad coursework at Sharif UT.`

# Distributed Algorithms Simulations

 Implementation LCR leader election, Bellman-Ford shortest path, Paxos consensus algorithm, and GHS minimum spanning tree algorithms using socket programming as well as distributed computation of a page rank and a friend suggestion method using Spark. 

### LCR Leader Election Algorithm
 IDs and link delays are passed to the nodes in a circular topology in clockwise order, then they start to exchange required messages until a leader is founded with the help of LCR algorithm explained in Distributed Algorithms by Nancy A. Lynch[^1].

### Bellman-Ford Shortest Path Algorithm
 Desired topology is fed into the code with a predefined format, then message passing starts so that finally a specified node, that does not have a central view of the network, knows the shortest path to evey other nodes. [^1]

### Paxos Consensus Protocol
 Nodes in a a given topology exchange messages in an asynchronous manner until they come to a consensus on their valuse. This protocol is known as Paxos. [^2]

### Gallager-Humblet-Spira (GHS) Minimum Spanning Tree Algorithm
 In this algorithm, nodes talk to each other to find a minimum spanning tree between themeselves. At the end, evey node should know its neighbor in the tree. This algorithm is explained in [^1] in detail.

### Friend Suggestion
 Suggesting some, for example 10, new friends to a person using Spark. These new friends have the most common friends with that person but are not his/her friends. The dataset consists of rows that show friends of an individual.

### Page Rank
 Ranking a set of pages that have links to each other. [This ranking method](https://en.wikipedia.org/wiki/PageRank) was used in Google in its early days of establishments. This method is implemented using Spark.


 [^1]: Lynch, N.A., 1996. Distributed algorithms. Elsevier.
 [^2]: Lamport, L., 2001. Paxos made simple. ACM Sigact News, 32(4), pp.18-25.
