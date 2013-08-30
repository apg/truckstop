"""search.py: Indexes for searching for food trucks!

This module defines two types of indexes, and then combines them into
a single index that can be queried with lots of different options.

First, we have a text index, DocumentIndex. This is done quite simply
by utilizing dot products of term frequencies across the set of
documents.  It's more or less a "poor man's text index" and requires
that we iterate over all documents per query. As such, we'll
prioritize the Spatial index first when possible.

There are a number of improvements to be made here. First, a search
for "tea" won't bring up "teas" or "iced-tea." The first example could
be solved by stemming all the words, making "teas" be stored as "tea",
and therefore counting towards an additional occurance of "tea." An
example algorithm for doing this is Porter. I haven't included this 
here (though this documentation may be out of date if I can find an
implementation -- it's rather complicated to implement just for this
exercise).


The second index type is for spatial searches. Since Food Trucks in SF
(I assume given the data) are permitted to operate at set locations,
we have an address and lat / lon of there permitted location. Thus, we
can easily build a KD-Tree (though other types of trees, such as an
Octree or Quad-tree would work) to eliminate trucks from our search
that are out of range.

In reality, searching for food trucks essentially comes down to this:

  - If given a max travel distance, find trucks within that range.
  - Of that set, keep the ones that the text query keeps
  - Order by some combined score (maybe prioritize distance over 
    relevance)

One can expand upon this by expanding the travel distance and offering
places that match the search terms, specifying to the user "We didn't
find anything in your range, but these things are just a bit
further...".

"""

from collections import defaultdict

import re
import math
import heapq


# At 40 deg north or south the distance between a degree of 
# longitude is 53 miles. Latitude varies ~68 - 69 miles

# XXX: I should have just done it for real.
SAN_FRANCISCO_LONGITUDE_MILEAGE = 53
SAN_FRANCISCO_LATITUDE_MILEAGE = 69
ESTIMATE_PER_UNIT_DISTANCE_MILES = (69 + 53) / 2.0


STOP_WORDS = set([
    'a', 'able', 'about', 'across', 'after', 'all', 'almost', 'also', 'am', 
    'among', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 
    'but', 'by', 'can', 'cannot', 'could', 'dear', 'did', 'do', 'does', 
    'either', 'else', 'ever', 'every', 'for', 'from', 'get', 'got', 'had', 
    'has', 'have', 'he', 'her', 'hers', 'him', 'his', 'how', 'however', 'i', 
    'if', 'in', 'into', 'is', 'it', 'its', 'just', 'least', 'let', 'like', 
    'likely', 'may', 'me', 'might', 'most', 'must', 'my', 'neither', 'no', 
    'nor', 'not', 'of', 'off', 'often', 'on', 'only', 'or', 'other', 'our',
    'own', 'rather', 'said', 'say', 'says', 'she', 'should', 'since', 'so', 
    'some', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these', 
    'they', 'this', 'tis', 'to', 'too', 'twas', 'us', 'wants', 'was', 'we', 
    'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 
    'will', 'with', 'would', 'yet', 'you', 'your'
])


def word_splitter(s):
    if isinstance(s, list):
        return s
    return filter(None, map(lambda x: x.strip().lower(), 
                            re.split("[^a-zA-Z0-9-]+", s)))


def fdot_product(d1, d2):
    """Computes the dot product of d1 and d2 using word frequencies
    as the vector components"""
    n = 0
    for w, f1 in d1._frequencies.iteritems():
        f2 = d2.freq(w)
        n += f2 * f1

    return n

def mk_tfidf_dot(docindex):
    """Creates a closure which computes the dot product of two documents
    where the vector components are the TF-IDF, rather than raw frequency.

    TF-IDF is a better metric than raw frequency for the simple fact that 
    it severely discounts popular terms across the document corpus. Thus,
    while dot product of frequencies would over emphasize non-important
    words like `the` and `a`, TF-IDF essentially makes them worth nothing.

    A simpler way to get similar results would be to remove the most common
    words, or to use a "stop list" which is a predetermined list of common
    words. We opt for a stop list, and TF-IDF for our computation.
    """
    def tf(w, d):
        return .5 + (.5 * d.freq(w)) / (d.max_freq or 1)

    def idf(w):
        dfreq = docindex.doc_freq(w) or 1
        ndocs = len(docindex)
        return math.log(ndocs / dfreq)

    def fdot_product(d1, d2):
        n = 0
        for w, _ in d1._frequencies.iteritems():
            tf1 = tf(w, d1)
            tf2 = tf(w, d2)
            idfw = idf(w)

            n += tf2 * tf1 * idfw 
        return n

    return fdot_product


class Document(object):
    """Represents a single document as a "bag of words."

    The "bag of words" isn't quite a bag of words, since it's stored
    in a rolled up fashion...

    Each document gets a `key` which is some external identifier used
    to retrieve the real data associated with the this representation.
    """

    def __init__(self, key, words):
        self._key = key
        words = word_splitter(words)
        self._frequencies = self._compute_frequencies(
            filter(lambda x: x not in STOP_WORDS, words))
        self._total_word_count = len(words)
        
        fv = self._frequencies.values()
        self._max_freq = max(fv) if fv else 0

    @property
    def key(self):
        return self._key

    def freq(self, w, default=0):
        return self._frequencies.get(w.lower(), default)

    @property
    def max_freq(self):
        return self._max_freq

    @property
    def total_words(self):
        return self._total_word_count

    def _compute_frequencies(self, words):
        f = defaultdict(lambda: 0)
        for w in words:
            f[w] += 1
        return f


class Query(Document):
    """Represents a query, which is just a Document without a key
    """

    def __init__(self, s):
        super(Query, self).__init__(s, word_splitter(s))


class DocumentIndex(object):
    """A box of documents, which can be queried. 

    """

    def __init__(self, documents):
        self._documents = documents
        self._inverted_index = defaultdict(set)
        # how many documents is `w` in?
        self._document_frequencies = self._rollup_frequencies(documents)


    def doc_freq(self, w, default=1):
        return self._document_frequencies.get(w, default)

    def __len__(self):
        return len(self._documents)

    def _rollup_frequencies(self, documents):
        f = defaultdict(lambda: 0)
        for d in documents:
            for w in d._frequencies:
                f[w] += 1
                self._inverted_index[w].add(d)
        return f

    def _candidate_documents(self, doc, keys=None):
        """Return only the documents from the index which actually
        contain a word in `doc`

        If keys is specified, only check those specified by `keys`"""

        docs = set()
        for w in doc._frequencies:
            if keys:
                for d in self._inverted_index[w]:
                    if d.key in keys:
                        docs.add(doc)
            else:
                docs.update(self._inverted_index[w])

        return docs

    def query(self, doc, max_results=10, distance=fdot_product, keys=None):
        results = []
        for d in self._candidate_documents(doc, keys=keys):
            dist = distance(doc, d)
            if dist == 0:
                dist = inf
            else:
                dist = 1 / dist
            
            heapq.heappush(results, (dist, d.key))
            results = heapq.nsmallest(max_results, results, key=lambda x: x[0])

        return results


# HACK: We're dealing in terms of a single city, which means that
# accuracy is unlikely to be *too* affected by not using something
# more geographically sound, like great circle distance.
def euclidean_distance(p1, p2):
    """Compute the distance between p1 and p2 on a hyperplane"""
    return math.sqrt(sum(map(lambda x, y: (x-y)**2, p1, p2)))


class SpatialNode(object):
                  
    __slots__ = ('pt', 'key', 'left', 'right',)

    def __init__(self, pt=None, key=None, left=None, right=None):
        self.pt = pt
        self.key = key
        self.left = left
        self.right = right

    def distance(self, pt, func=euclidean_distance):
        return func(self.pt, pt)


class SpatialIndex(object):
    """Creates a spatial index using lat / lon coordinates.

    `locations` in the constructor should be in the form of:
       [('key', (lat, lon)), ....]
    or
       {'key': (lat, lon), ...}

    Where `key` is an external way in which to lookup the real value.
    """

    def __init__(self, locations, magnitude=ESTIMATE_PER_UNIT_DISTANCE_MILES):
        if isinstance(locations, dict):
            self._tree = self._make_tree(locations.iteritems())
        else:
            self._tree = self._make_tree(locations)
        self.magnitude = magnitude

    def _make_tree(self, locations):
        return kdtree(locations)

    def _search(self, pt, within, node, accum, depth=0, 
                max_results=None, distance=euclidean_distance):
        if not node:
            return

        d = distance(pt, node.pt) * self.magnitude
        if d <= within:
            heapq.heappush(accum, (d, node.key,))

        if max_results:
#            import pdb; pdb.set_trace()
            accum = heapq.nsmallest(max_results, accum, 
                                    key=lambda x: x[0])

        axis = depth % len(pt)

        for child in ('left', 'right'):
            child = getattr(node, child)
            if child:
                # are we within range at the axis level?
                there = [0] * len(pt)
                there[axis] = child.pt[axis]

                here = [0] * len(pt)
                here[axis] = pt[axis]

                if distance(there, here) <= within:
                    accum = self._search(pt, within, child, accum, depth+1,
                                         max_results=max_results, 
                                         distance=distance)
        return accum

    def search(self, pt, within, max_results=None):
        """Finds and orders all nodes within `within` distance of
        `pt`

        Returns [(distance, 'key')]
        """
        return self._search(pt, within, self._tree, [], 
                            max_results=max_results)



# From: http://en.wikipedia.org/wiki/Kd-tree
def kdtree(pts, depth=0):
    if not pts:
        return None

    # realize any iterator so we can index
    pts = list(pts)

    # Select axis based on depth so that axis cycles through all valid values
    k = len(pts[0][1]) # assumes all points have the same dimension
    axis = depth % k
 
    # Sort point list and choose median as pivot element
    pts.sort(key=lambda loc: loc[1][axis])
    median = len(pts) // 2 # choose median

    loc = pts[median]
    # Create node and construct subtrees
    node = SpatialNode(key=loc[0], pt=loc[1])
    node.left = kdtree(pts[:median], depth + 1)
    node.right = kdtree(pts[median + 1:], depth + 1)

    return node



