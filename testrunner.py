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

import unittest

from tests.testregexes import TestRegexes
from tests.testlines import TestSingleLines

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(TestRegexes)
	unittest.TextTestRunner(verbosity=2).run(suite)

	suite = unittest.TestLoader().loadTestsFromTestCase(TestSingleLines)
	unittest.TextTestRunner(verbosity=2).run(suite)
