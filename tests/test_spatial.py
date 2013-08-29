import unittest

from truckstop.search import SpatialIndex

"""

Scenario 1:

            N (0, 10)



W (-10, 0)  X            E (10, 0)

 
       
            S (0, -10)

This is a simple set of points. We'll never find anything if we search
within 10 units.


Scenario 2: (lifted from the WikiPedia example)

               D (4, 7)   

                                          C (9, 6)
              
                 B (5, 4)
      A (2, 3)
                                  F (7, 2)
                                      E (8, 1)      
X     
"""




SCENARIO_1 = {
    'N': (0, 10),
    'S': (0, -10),
    'E': (10, 0),
    'W': (-10, 0),
}

# from WikiPedia
SCENARIO_2 = {
    'A': (2, 3), 
    'B': (5, 4), 
    'C': (9, 6), 
    'D': (4, 7), 
    'E': (8, 1), 
    'F': (7, 2)
}


class TestSpatialIndex(unittest.TestCase):

    def setUp(self):
        self.scenario_1 = SpatialIndex(SCENARIO_1, magnitude=1)
        self.scenario_2 = SpatialIndex(SCENARIO_2, magnitude=1)

    def test_search(self):
        wideOpenSearch = self.scenario_1.search((0, 0), 100000,
                                                max_results=1000)
        self.assertEquals(len(wideOpenSearch), 4, "A wide open search "
                          "should return all points")

        narrowSearch = self.scenario_1.search((0, 0), 1,
                                              max_results=1000)

        self.assertEquals(len(narrowSearch), 0, "A narrow search "
                          "should return no points")
        
        within7oforigin = self.scenario_2.search((0, 0), 7)

        self.assertEquals(len(within7oforigin), 2, 
                          "Only 2 points within 7")
        self.assertEquals('AB', 
                          ''.join(map(lambda x: x[1], within7oforigin)),
                          'Order should be AB')
        
                                                 
