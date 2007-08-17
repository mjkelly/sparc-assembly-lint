#!/usr/bin/python
# -----------------------------------------------------------------
# testrunner.py -- Run all unit tests.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sun Aug 12 03:24:12 PDT 2007
# -----------------------------------------------------------------

from optparse import OptionParser, OptionGroup
import unittest

from tests.testregexes import TestRegexes
from tests.testlines import TestSingleLines


if __name__ == '__main__':
	opt_parser = OptionParser(usage="%prog [OPTIONS]")

	opt_parser.add_option("--verbosity", action="store", dest="verbosity",
		type="int", help="Output verbosity: -1 = completely silent, 0 = quiet, 1 = some debug, 2 = copious debug.")

	opt_parser.set_defaults(verbosity=-1)

	(opts, args) = opt_parser.parse_args()

	suite = unittest.TestLoader().loadTestsFromTestCase(TestRegexes)
	unittest.TextTestRunner(verbosity=2).run(suite)

	TestSingleLines.verbosity = opts.verbosity
	suite = unittest.TestLoader().loadTestsFromTestCase(TestSingleLines)
	unittest.TextTestRunner(verbosity=2).run(suite)
