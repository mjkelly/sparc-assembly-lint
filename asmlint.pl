#!/usr/bin/perl
# -----------------------------------------------------------------
# asmlint.pl -- Try to catch common errors in SPARC assembly.
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Fri Jun  1 11:55:40 PDT 2007
# -----------------------------------------------------------------

use strict;
use warnings;

my $file = shift(@ARGV) or die "Usage: $0 FILENAME[...]\n";

if( !defined(open(INPUT, '<', $file))  ){
	die "Error opening input file $file: $!\n";
}

while(<INPUT>){
	print;
	print "\n";
}

close(INPUT);

