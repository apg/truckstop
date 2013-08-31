"""Collection of utils for truckstop
"""
from functools import wraps
from bottle import request


def param_validator(**specs):
    def dec(func):
        @wraps(func)
        def orator():
            print "query is: ", request.query

            kwargs = {}
            for n, s in specs.iteritems():
                try:
                    print "param_validator", n, getattr(request.query, n)
                    v = s[0](getattr(request.query, n))
                except:
                    if s[1]:
                        return {'error': s[1]}
                else:
                    kwargs[n] = v
                    print kwargs
            try:
                return func(**kwargs)
            except ValueError, e:
                return {'error': str(e)}
        return orator
    return dec
    

