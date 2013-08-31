import unittest
from truckstop.search import Document, DocumentIndex, Query, mk_tfidf_dot

from bane_lyrics import holding_this_moment


class TestDocumentFrequencies(unittest.TestCase):

    def setUp(self):
        self.sample = "The quick brown fox jumped over the lazy dog"
        self.sampleDocument = Document('sample', self.sample)
        self.buffalo = "Buffalo buffalo buffalo buffalo buffalo buffalo"
        self.buffaloDocument = Document('buffalo', self.buffalo)

    def test_frequencies(self):
        self.assertEquals(self.sampleDocument.freq('the'), 0, 
                          "The should be removed via stop words")

        self.assertEquals(self.sampleDocument.freq('lazy'), 1,
                          "lazy appears only once")

        self.assertEquals(self.sampleDocument.freq('lazy dog'), 0,
                          "bigrams are not considered")

        self.assertEquals(self.buffaloDocument.freq('buffalo'), 6,
                          "buffalo appears 6 times")

        self.assertEquals(self.buffaloDocument.freq('Buffalo'), 6,
                          "Buffalo appears 6 times when downcased")

        self.assertEquals(self.buffaloDocument.max_freq, 6,
                          "Buffalo appears the most, 6 times")

        self.assertEquals(self.buffaloDocument.total_words, 6,
                          "The buffalo document has 6 words in total")

        self.assertEquals(self.sampleDocument.total_words, 7,
                          "The sample document has 9 words in total")


        
class TestIndex(unittest.TestCase):
    
    def setUp(self):
        self.index = DocumentIndex(holding_this_moment)
        self.hardcoreQuery = Query("hardcore effort")
        self.lifeQuery = Query("life")
        self.rubberbandQuery = Query("Rubberband stretched")
        self.nullQuery = Query("")
        self.noResultsQuery = Query("Pink Floyd")

    def test_frequencies(self):
        self.assertEquals(self.index.doc_freq("life"), 3,
                          "Life appears in 3 separate songs")
        self.assertEquals(self.index.doc_freq("the", 1), 1,
                          "the is a stop word and thus shouldn't "
                          "appear, but we do some smoothing")
        
    def test_search(self):
        noResults = self.index.query(self.noResultsQuery)
        self.assertEquals(len(noResults), 0,
                          "Pink Floyd should return no results")

        nullResults = self.index.query(self.nullQuery)
        self.assertEquals(len(noResults), 0,
                          "empty query should return no results")

        rubberBandResults = self.index.query(self.rubberbandQuery)
        self.assertEquals(len(rubberBandResults), 1,
                          "Rubberband stretched appears 1 time in "
                          "Holding this Moment")
        self.assertEquals(rubberBandResults[0][1], 'In Pieces')


    def test_idf_search(self):
        idf_distance = mk_tfidf_dot(self.index)
        lifeResults = self.index.query(self.lifeQuery, max_results=2,
                                       distance=idf_distance)
        
        self.assertEquals(len(lifeResults), 2, 
                          "'life' has 3 matching documents, but "
                          "we asked for 2 only")

        hardcoreResults = self.index.query(self.hardcoreQuery,
                                           max_results=1,
                                           distance=idf_distance)
        
        self.assertEquals(len(hardcoreResults), 1,
                          "'hardcore scene' should match 2 documents, "
                          "but we asked for the best one")
        self.assertEquals(hardcoreResults[0][1], 'Every Effort Made',
                          "Every Effort Made is the best result")
        
