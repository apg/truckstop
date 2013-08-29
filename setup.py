from setuptools import setup

def run_tests():
    import os, sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
    from truckstop_tests import suite
    return suite()


setup(
    name = 'truckstop',
    version = '0.1',
    packages = [],
    author = 'Andrew Gwozdziewycz',
    author_email = 'web@apgwoz.com',
    description = 'San Francisco food trucks on a map.',
    url = 'https://github.com/apgwoz/truckstop',
#    scripts = ['truckstop']
    test_suite = '__main__.run_tests'
)
