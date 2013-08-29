#!/usr/bin/env python

import sys
import json

from bottle import route, run, debug, template
from optparse import OptionParser

from search import Query
from loader import load

SPATIAL_INDEX = None
TEXT_INDEX = None
OBJECT_STORE = None

TEXT_DISTANCE_FUNC = None

@route('/api/v1/search\.json')
def api_search():
    return {'data': []}

@route('/api/v1/explore\.json')
def api_explore():
    return {'data': []}

@route('/')
def index():
    return template('index')


parser = OptionParser(usage="%prog [options] datafile)")
parser.add_option("-d", "--dev", dest="dev",
                  help="run in dev mode")
parser.add_option("-h", "--host", dest="host",
                  default="127.0.0.1")
parser.add_option("-p", "--port", dest="port",
                  type="int", default=8080)


if __name__ == '__main__':
    params = {}
    (options, args) = parser.parse_args()

    if options.dev:
        debug(True)
        params['reloader'] = True
    else:
        params['server'] = 'gevent'

    params['host'] = options.host
    params['port'] = options.port

    if len(args) != 2:
        parser.print_help()
        raise SystemExit()

    print "Loading data from file...."
    SPATIAL_INDEX, TEXT_INDEX, OBJECT_STORE = load(args[1])
    print "%d locations indexed" % len(OBJECT_STORE)

    TEXT_DISTANCE_FUNC = mk_tfidf_dot(TEXT_INDEX)

    print "Starting app on %(host)s:%(port)d..." % params
    run(**params)
