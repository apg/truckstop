import csv

from search import SpatialIndex, DocumentIndex, Document

def load(fname):
    """Loads CSV into searchable indexes
    """
    skip = 0
    documents = []
    locations = []
    objects = {}
    reader = csv.DictReader(open(fname))
    for spot in reader:
        if not spot['Latitude'] or not spot['Longitude']:
            print "%d. Have to skip this one: %s" % (skip, spot['Applicant'])
            skip += 1
            continue

        lat, lon = float(spot['Latitude']), float(spot['Longitude'])
        doctext = "%(Applicant)s %(FoodItems)s" % spot
        key = spot['ObjectID']
        locations.append((key, (lat, lon,),))
        documents.append(Document(key, doctext))
        objects[key] = spot

    spatial = SpatialIndex(locations)
    text = DocumentIndex(documents)

    return spatial, text, objects
    
