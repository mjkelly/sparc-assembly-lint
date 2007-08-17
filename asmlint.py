#!/usr/bin/python
# -----------------------------------------------------------------
# asmlint.py -- Find common errors in SPARC assembly files.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Thu Aug 16 01:20:52 PDT 2007
# -----------------------------------------------------------------

from optparse import OptionParser, OptionGroup
import sys
import pprint

from asm_parser import yacc, debug, warn, info, get_num_errors, init_parser

parse_tree = []

# Run the linter on a file handle.
# @return the number of errors that occurred in the parse
def run(handle, check_line_length, max_line_length, verbosity):
	init_parser(verbosity)
	lineno = 0
	while True:
		lineno += 1
		s = handle.readline()
		debug(">>> " + s.rstrip())

		if check_line_length and len(s.rstrip('\n')) > max_line_length:
			warn("%s:%d exceeds %d chars." % (handle.name, lineno, max_line_length))

		if s == "":
			break
		try:
			parse_tree.append(str(yacc.parse(s)))
		except Exception, e:
			print 'Exception caught while parsing line %d!\n' % lineno
			raise e

	return get_num_errors()

def main(argv):

	opt_parser = OptionParser(usage="%prog [OPTIONS] [FILENAME]")

	opt_parser.add_option("--check-line-length", action="store_true", dest="check_line_length",
		help="Check line length.")
	opt_parser.add_option("--max-line-length", action="store", dest="max_line_length",
		type="int", help="Maximum acceptable line length when --check-line-length is on.")
	opt_parser.add_option("--verbosity", action="store", dest="verbosity",
		type="int", help="Output verbosity: -1 = completely silent, 0 = quiet, 1 = some debug, 2 = copious debug.")

	opt_parser.set_defaults(max_line_length=80)
	opt_parser.set_defaults(check_line_length=False)
	opt_parser.set_defaults(verbosity=2)

	input_file = sys.stdin

	(opts, args) = opt_parser.parse_args()

	if len(args) > 1:
		opt_parser.print_help()
		sys.exit(2)
	elif len(args) > 0:
		input_filename = args[0]
		input_file = open(input_filename, 'r')
	
	num_errors = run(input_file, opts.check_line_length, opts.max_line_length, opts.verbosity)

	if input_file != sys.stdin:
		input_file.close()

	info("-----------------------------------------------------------------------------")
	info("%d errors." % num_errors)

	if num_errors == 0:
		return 0
	else:
		return 1

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == '__main__':
	sys.exit(main(sys.argv))

