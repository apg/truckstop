#!/usr/bin/env python
import gevent.monkey; gevent.monkey.patch_all()
import sys
import os
import json

from bottle import route, run, debug, template, request, \
    static_file

from optparse import OptionParser

from truckstop.search import Query, mk_tfidf_dot
from truckstop.loader import load
from truckstop.utils import param_validator

SPATIAL_INDEX = None
TEXT_INDEX = None
OBJECT_STORE = None

TEXT_DISTANCE_FUNC = None

def mk_static(route_base):
    def s(filename):
        print >>sys.stderr, filename, route_base, os.path.abspath('.' + route_base)
        return static_file(filename, root=os.path.abspath('.' + route_base))
    return route(os.path.join(route_base,'<filename>'))(s)

mk_static('/static/js')
mk_static('/static/css')
mk_static('/static/img')

@route('/api/v1/search.json')
@param_validator(lat=(float, "Invalid Latitude"),
                 lon=(float, "Invalid Longitude"),
                 radius=(float, None),
                 query=(str, None),
                 page=(int, None),
                 per_page=(int, None),)
def api_search(lat=None, lon=None, radius=10, 
               query='', page=1, per_page=10):
    """Searches a given area identified by the parameters
    `lat`, `lon` and `radius` for `query` (optional)
    """
    if radius <= 0 or radius > 15:
        raise ValueError("radius must be > 0 and < 15")
    if page <= 0:
        raise ValueError("page must be > 0")
    if per_page <= 0 or per_page > 50:
        raise ValueError("per page must be between 0 and 50")

                
    results = SPATIAL_INDEX.search((lat, lon), radius)
    distances = dict((v, k) for k, v in results)
    textscores = {}

    if query and results:
        keys = set(x[1] for x in results)
        results = TEXT_INDEX.query(Query(query), keys=keys)
        scores = dict((v, k) for k, v in results)

    # we also need to keep the correct distances from above.z
    # do paging now, then get the correct objects from the OBJECT_STORE

    objects = []
    for s, oid in results:
        o = OBJECT_STORE.get(oid)
        if o:
            o = o.copy()
            o['Address'] = o['Address'].title()
            o['distance'] = distances.get(oid, 10000)
            o['distance_desc'] = '%.2fmi' % distances.get(oid, 10000)
            objects.append(o.copy())

    return {'venues': sorted(objects, key=lambda x: x['distance'])}

@route('/api/v1/roulette.json')
def api_roulette():
    return {'venues': []}

@route('/')
def index():
    return template('index')


parser = OptionParser(usage="%prog [options] datafile)")
parser.add_option("-b", "--bind", dest="host",
                  default="127.0.0.1")
parser.add_option("-d", "--dev", dest="dev", action="store_true",
                  default=False,
                  help="run in dev mode")
parser.add_option("-p", "--port", dest="port",
                  type="int", default=8080)
parser.add_option("-s", "--static-directory", dest="static",
                  default="./static")


if __name__ == '__main__':
    import os
    params = {}
    (options, args) = parser.parse_args()

    if options.dev:
        debug(True)
        params['reloader'] = True
    else:
        params['server'] = 'gevent'

    params['host'] = options.host
    params['port'] = options.port

    if len(args) != 1:
        parser.print_help()
        raise SystemExit()

    print "Loading data from file...."
    SPATIAL_INDEX, TEXT_INDEX, OBJECT_STORE = load(args[0])
    print "%d locations indexed" % len(OBJECT_STORE)

    TEXT_DISTANCE_FUNC = mk_tfidf_dot(TEXT_INDEX)

    print "Starting app on %(host)s:%(port)d..." % params


    run(**params)
