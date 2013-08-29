import unittest

def suite():
    from test_document import TestDocumentFrequencies, TestIndex
    from test_spatial import TestSpatialIndex

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDocumentFrequencies))
    suite.addTest(unittest.makeSuite(TestIndex))
    suite.addTest(unittest.makeSuite(TestSpatialIndex))

    return suite
    
