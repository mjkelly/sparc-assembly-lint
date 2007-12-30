#!/usr/bin/python
# -----------------------------------------------------------------
# testrunner.py -- Run all unit tests.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sun Aug 12 03:24:12 PDT 2007
# -----------------------------------------------------------------

import sys
from optparse import OptionParser, OptionGroup
import unittest

import tests.testregexes
import tests.testcode

def main():
	opt_parser = OptionParser(usage="%prog [OPTIONS]")

        opt_parser.add_option('-v', '--verbose', action="count", dest="verbosity", 
	                help="Increase verbosity of output.  Use multiple times to increase verbosity further.")
	opt_parser.add_option("-t", "--test", action="append", dest="run_tests",
		type="string", help="Name of specific test to run. May be given multiple times to run more than one test.")
	opt_parser.add_option("-l", "--list", action="store_true", dest="list",
		default=False, help="List names of possible tests to run with --test.")
	opt_parser.add_option("-u", "--unstable", action="store_true", dest="run_unstable",
		default=False, help="Run unstable tests.")

	opt_parser.set_defaults(verbosity=-1)
	opt_parser.set_defaults(run_tests=[])

	(opts, args) = opt_parser.parse_args()

	test_runner = TestRunner(opts)
	was_successful = True

	test_methods = get_methods(test_runner)
	avail_methods = test_methods.copy()
	
	if opts.list:
		print "Registered tests:"
		for test in avail_methods.keys():
			print "\t" + strip_prefix('runtest_', test)
		return 0
	
	if len(opts.run_tests) != 0:
		run_tests = map(lambda s: 'runtest_' + s, opts.run_tests)
	else:
		run_tests = test_methods.keys()
	
	for test in run_tests:
		method_name = test
		if not(method_name in avail_methods):
			print '*** No test "%s" exists! ***' % test
			continue
		method = avail_methods[method_name]
		print method_name
		ret = method()
		if not ret.wasSuccessful():
			was_successful = False
	
	if was_successful:
		return 0
	else:
		print "----------------------------------------------------------------"
		print "SOME TESTS FAILED!"
		return 1

def strip_prefix(prefix, str):
	'''If str begins with prefix, return str with first instance of prefix removed.'''
	if str.startswith(prefix):
		return str[len(prefix):]
	else:
		return str
	
def get_methods(testobj, prefix='runtest_'):
	'''Return a dictionary of all methods in testobj beginning with prefix.
	   Keys are method names (including prefix), values are the methods
	   themselves.'''
	test_methods = {}
	for method_name in dir(testobj):
		method = getattr(testobj, method_name)
		if method_name.startswith(prefix) and callable(method):
			test_methods[method_name] = method

	return test_methods

class TestRunner:
	'''Methods to kick off test suites.'''

	def __init__(self, opts):
		self.opts = opts
	
	def runTest(self, testClass):
		testClass.verbosity = self.opts.verbosity
		testClass.run_unstable = self.opts.run_unstable
		suite = unittest.TestLoader().loadTestsFromTestCase(testClass)
		return unittest.TextTestRunner(verbosity=2).run(suite)
		
	def runtest_regexes(self):
		return self.runTest(tests.testregexes.TestRegexes)

	def runtest_lines(self):
		return self.runTest(tests.testcode.TestLines)
	
	def runtest_files(self):
		return self.runTest(tests.testcode.TestFiles)

if __name__ == '__main__':
	sys.exit(main())

