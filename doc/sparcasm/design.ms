\" $Header: /home/ediger/src/csrc/sparc_assembler10/RCS/design.ms,v 1.4 1997/03/25 07:42:38 bediger Exp bediger $
\" $Log: design.ms,v $
\" Revision 1.4  1997/03/25 07:42:38  bediger
\" several days of work
\"
\" Revision 1.2  1997/02/14 06:35:57  bediger
\" additions
\"
\" Revision 1.1  1997/01/15 01:15:31  bediger
\" Initial revision
\"
.DA
.TL
Design of a SPARC assembler
.AU
Bruce Ediger
.SH
Goal
.LP
The goal of this project was to improve my knowledge of compiling and
linking.
Writing an assembler seemed like a good way to do this, since
an assembler is at an interesting juncture in compilation.
Assemblers must read and  decipher text input.
Assemblers also generate object code that should be 
link-editable into a larger program entity.
Writing an assembler therefore requires some of the lexical analysis
and parsing of a compiler proper, but it also requires the ability
to generate binary instructions, and linking information.
.LP
An assembler is also a project that has a definable ending:
it's done when it can replace the stock, system-provided assembler.
.LP
I should justify writing something that will
never replace the current utility (the GNU \fIas\fR assembler), except temporarily on my machine.
About the only thing I can say is that my assembler is a bit easier
to understand than the GNU assembler.
It should be more obvious to make it cross-assemble, or to add
new assembler directives or opcode mnemonics.
This obviousness is directly related to the fact that
it assembles only a single instruction set.
.LP
This assembler is supposed to assemble SPARC Version 8 assembly language
into object modules of the NetBSD 
.ft CW
a.out
.ft R
format.
I tried to retain all features of Sun Microsystems SunOS assembler,
and include as much as I could decipher of the GNU SPARC assembler.
.LP
I used \fIThe SPARC Architecture Manual\fR, version 8, Prentice Hall,
1992, ISBN 0-13-825001-4 for the definition of the SPARC instruction
set, and for the suggested assembly language syntax.
.SH
Description
.LP
My assembler is a two-pass assembler written in a language as close to ANSI C
as I can manage.  A complete parse of the input is done for each pass.
It uses a program-generated lexical analyzer and a program-generated
parser to recognize and structure its textual input.
Assembler directives are considered part of the grammar, because that 
allows the parser to recognize and evaluate algebraic expressions in directive arguments.
Comments are recognized and removed by the lexical analyzer.
.LP
The assembler's first pass over the input file determines the size
of the assembled machine code and initialized data.  It fills in
a symbol table with all labels that refer to data or instructions in the input.
Between passes over the input, it
pre-allocates a file of the size required for instructions and
initialized data.  It does not pre-allocate space in the file for
symbol table and relocation information.
.LP
The second pass creates and writes instructions and initialized data
into the pre-allocated file.  It also adds special purpose debugging symbols
to the symbol table. The assembler ignores debugging symbols (``stabs'') during the first pass,
since they can reference other symbols.
The second pass creates relocation information
that will allow link-editing an object module with other object modules
and library code.
After the second pass, the assembler appends symbol table and relocation
information to the file containing the object code.
.SH
Development Platform
.LP
I chose NetBSD/sparc version 1.1 as my development platform.   I currently own a
functional NetBSD/sparc 1.1 computer, but there are a few other reasons.
.IP 1.
Source code for the entire compiler is freely available.
This gives me examples and extra information when the documentation
is inadequate or incomprehensible.
It also gives me a framework in which to test my assembler.
.IP 2.
The SPARC instruction set architecture is a well documented and stable
RISC architecture.
A consequence of this is that the assembly language itself is simpler
than for some other ISAs.
.IP 3.
SPARC instructions are all of a single width, and have relatively few
formats. This decreases the amount of effort I had to expend on
the trivialities of generating bits for the instructions.
Single-width instructions also avoid the complicated instruction selection
that some other ISA's assembly language conventions seem to mandate (e.g.
assemblers for Motorola's M68K have to decide whether to use a ``branch''
or ``branch quick'' instruction for the same mnemonic: the preference is for ``branch quick'',
which saves at least two bytes).
.LP
There are some drawbacks to choosing this platform.
NetBSD/sparc is considered an experimental operating system.
Developing or running software may expose bugs in the OS or
system-provided software.
NetBSD/sparc is essentially a SPARC V8 system, which is
becoming obsolescent as Sun Microsystems introduces SPARC V9
CPUs and systems.
.SH
Completion Criteria
.LP
I wanted to put a limit on this project. I wanted to scope it so that it would not drag on
for a long time, and I would have some way to decide whether
to include or exclude design or implementation changes.
.LP
I decided that my assembler would be complete if it could act as the
assembler for building the 
.ft CW
lcc 
.ft R
3.5 ANSI C compiler, and if it could assemble
the SPARC assembly language portion of the NetBSD/sparc 1.1 operating
system kernel. I later added two more tests: acting as assembler when recompiling itself,
and assembling the SPARC assembly code for the SML/NJ 0.93 interpreter.
.LP
I chose the OS kernel assembly portions because they are hand coded by an expert,
using all the odd features of SPARC assembly. They also include many privileged
mode instructions that compilers won't generate.
The assembly code from the SML/NJ interpreter has much the same properties, but it's written by
another expert, further exercising my assembler.
.LP
I chose building 
.ft CW
lcc
.ft R
as a completion test because that would check
the assembler's compatibility with compiler output.  The complete build of 
.ft CW
lcc
.ft R
compiles
three versions,  two of which are compiled by the previous version.
Each version potentially generates different assembly code.
.ft CW
lcc
.ft R
also uses floating-point arithmetic to choose among alternatives
during the code generation phase of compilation.
.SH
Recognizing and deciphering input text
.LP
Since my goal was to learn more about compiling and linking,
I wrote this assembler as if it were a compiler.
It has a lexical analyzer that breaks the input text stream
into tokens and marks each token with a type.
It has a parser that gets tokens and their type markers
from the lexical analyzer and organizes them into small parse
trees.
It builds one parse tree (a true tree, not a DAG) per assembly language statement.
.LP
I used the freely-available lexical-analyzer-generator 
.ft CW
flex,
.ft R
version 2.5.2, to implement the lexical analyzer.
I used the similarly freely-available LALR(1) parser generator
.ft CW
byacc,
.ft R
version 1.9, to implement the parser.
.LP
.ft CW
flex
.ft R
seemed like a wise choice because of word-of-mouth
recommendations, and because I wasn't interested in learning
how to do lexical analysis.
I can't complain about the results of this choice.
.LP
I chose 
.ft CW
byacc
.ft R
because I was quite taken with the suggested
assembly language syntax given in \fIThe SPARC Architecture Manual\fR.
The suggested syntax seemed to be a natural fit with 
.ft CW
byacc's
.ft R
input.  
.LP
The suggested syntax did lead to a relatively small grammar.
Many of the productions of the grammar exist to perform the elaborate C-language-style
operator precedence rules for algebraic expressions, not for dealing with the
assembly language proper.
The grammar also made for small, manageable semantic actions associated with each production.
.LP
This elaborate method of recognizing input may be overkill for a simple
language like SPARC assembly.
It's possible that using a full-blown 
.ft CW
byacc
.ft R
style parser is both
slower and harder to do than manually writing a simple recursive-descent
parser.
The parse trees generated are very simple, amounting to little more than
a direct transliteration of a line of assembly into a C struct.
This suggests that a simpler parser may be in order.
.SH
Symbol table
.LP
The symbol table is a linear dynamic hash table.
I wrote the hash table based on ``Dynamic Hash Tables''
by Per-Ake Larson, \fICommunications of the ACM\fR,
April 1988, volume 31, number 4.
I suspect this is overkill, but it should yield decent
performance for both small and large symbol tables.
The symbol names (ASCII strings) are used as the single
key to retrieve 
.ft CW
struct nlist
.ft R
symbol table entries.
I used the venerable ``PJW'' hash function on the symbol
name strings to generate hash values.
.LP
One complication of the symbol table is the old SunOS 4.x assembler's
``local labels''.
In the assembly language input, local labels consist of a single digit
(0 through 9) followed by a colon.  There can be an arbitrary number
of locations labeled with any particular digit.
As a branch destination or symbolic name, a local label is 
a digit and a letter `f' or `b'.
The letters indicate forward or backward reference.
That is, the address of the symbol referred to depends on where the reference
is made.
What's worse is that the ``nearest digit-labeled symbol'' is done on a
textual basis, not on an address basis.  In a code sequence like:
.na
.nf
.ft CW
	.data
	1: .asciiz "some stuff"
	.text
	[...input without local labels...]
	set 1b,%o1
.ft R
.fi
.ad
The reference to 
.ft CW
1b
.ft R
in the 
.ft CW
\ .text
.ft R
segment is to the label 
.ft CW
1:
.ft R
in the 
.ft CW
\ .data
.ft R
segment.
The label referred to in the 
.ft CW
set
.ft R
instruction is the immediately previous ``1'' in the input, not in
the assembled object code.  This strikes me as a poor misfeature,
but to be able to pass my self-imposed acceptance tests, I needed
this assembler to correctly handle ``local labels''.
.LP
I ended up having to generate temporary labels when a local label
appeared in the input, using a counter to keep the ``nearest''
label accessible.
.SH
Development software
.LP
I used the following software and systems of software to write this
assembler.
I extend thanks to everyone who wrote the following things.
.nf
.na
.ft CW
NetBSD/sparc 1.1
X11R6
vim 3.21 and 4.5
gcc 2.4.5 - NetBSD's version
GNU assembler version 1.92.3, NetBSD $Revision: 1.4 $
The ld link editor that comes with NetBSD 1.1
GDB 4.11 (sparc-netbsd), Copyright 1993 Free Software Foundation, Inc.
lcc 3.5
xxgdb 1.12
flex 2.5.2
byacc 1.9
Electric Fence 2.0.1 Copyright (C) 1987-1993 Bruce Perens.
dmalloc-3.1.3, Copyright (C) 1992 - 1995 by Gray Watson.
``LEAK - Quick and dirty code to find memory leaks'',
	Copyright (C) 1993, Christopher G. Phillips
.ft R
.fi
.ad
.LP
I believe that all of this software is either unencumbered, or is free for
non-commercial use.
Since I don't have any illusions about getting money for my assembler,
I believe I fall under the non-commercial use clauses.
.LP
lcc 3.5 is described in
\fIA Retargetable C Compiler: Design and Implementation\fR,
Addison-Wesley, 1995, ISBN 0-8053-1670-1.
.SH
Problems during development
.LP
I initially thought that only a single pass over the input would be required.
Using and maintaining several symbol and relocation information tables during assembly would allow an ultimate
reconciliation of forward references.
After the reconciliation, rewriting of
instructions that make forward references would be possible.
.LP
A single-pass assembler may be possible in theory, but the intricacies
of the 
.ft CW
a.out
.ft R
object file format make it very difficult.
The worst difficulties I encountered involved
source level debugging information.  Source level debugging information for
high-level languages is represented by special symbol table entries.
This means
debugging information symbols potentially do the same
kind of forward references that ``branch'' instructions make.
I believe this can lead to a problem of symbols that refer to other
symbols, potentially circularly.  I didn't want to deal with
detecting and resolving problems like that.
.LP
Relocation information that relates to unresolved symbols presents
another problem for a single-pass assembler.  The association between
relocation information and symbol information is an index into an array
(
.ft CW
r_index
.ft R
field of
.ft CW
struct relocation_info
.ft R
).  This indexing forces formatting the symbol table as an array
before completing the relocation information.
.LP
The 
.ft CW
byacc
.ft R
grammar did lead to some difficulty in writing the code that actually
generates the instruction bit patterns.
Given the small number of SPARC instruction formats, I'd hoped to
have only a few routines that actually formatted instructions.
The parser would call the appropriate routine when it had built
up the parse tree for an assembly language statement.
.LP
It just wasn't possible to write 5 or 6 routines, one for each
instruction format, and reuse those few functions to assemble many
different instructions.  The suggested assembly language has situations like this:
.LP
.nf
.na
.ft CW
ld [rs1+rs2],rd
st rd,[rs1+rs2]
.ft R
.ad
.fi
.LP
Both
.ft CW
ld
.ft R
and
.ft CW
st
.ft R
mnemonics have identical machine code instruction formats.  Only the human-readable
assembly language is somewhat different.  The parser can distinguish
these based on grammatical considerations and rearrange the tokens to
a conventional order (source 1, source 2, destination).
This isn't the case for ``synthetic'' instructions.
.LP
.nf
.na
.ft CW
tst %o5  ! orcc %g0, %o5, %g0
dec %o5  ! sub  %o5, 0x1, %o5
clr %o5  ! or   %g0, %g0, %o5
.ft R
.ad
.fi
.LP
There's not enough information for the parser to figure out if the
operand register is one or both of the source registers, or the
destination register.
.LP
In some cases, the same human-readable mnemonic is used for several distinct
instructions.  The selection of instruction depends on the
register named in the assembly language statement.  For instance, for the
following instructions, the actual bit-pattern for
the instruction must be selected by examining the operand registers.
.LP
.nf
.na
.ft CW
rd %y,%r15         ! RDY   instruction
rd %psr,%r15       ! RDPSR instruction
st %f1,[%r1+%r2]   ! STF   instruction
st %r3,[%r1+%r2]   ! ST    instruction
.ft R
.fi
.ad
.LP
I ended up writing 5 or 6 routines that handled the bulk of
the instruction mnemonics, and about 10 more routines that handled the
irregular synthetic instructions.
.LP
There are actually more instruction formats than \fIThe SPARC Architecture Manual\fR
indicates.
For example, the various trap-on-condition-code instructions, nominally format 3,
end up using the destination register field (
.ft CW
rd
.ft R
) as the distinguishing code for the trap condition
(e.g. not equal, positive, less than, etc, relating to the integer condition codes
bits of the Processor Status Register).
.LP
Both the SunOS assembler and the NetBSD version of the GNU assembler
accept opcode mnemonics that are undocumented.
For example, the SunOS assembler accepts 
.ft CW
ld2
.ft R
and
.ft CW
st2
.ft R
mnemonics.  I can't find documentation for these anywhere.
.LP
The ancient BSD 
.ft CW
a.out
.ft R
object file format is very peculiar, as noted previously.
Despite its age, sometimes the documentation on it is very weak.
I found the relocation information to be particularly tricky to
get right.
.LP
The symbol table (an array of
.ft CW
struct nlist
.ft R
) and relocation information (two arrays of
.ft CW
struct relocation_info_sparc
.ft R
) seem designed to minimize the
amount of disk space they consume, yet there are some odd redundancies.
The 
.ft CW
r_extern
.ft R
field of 
.ft CW
struct relocation_info_sparc
.ft R
duplicates
the information in the 
.ft CW
N_EXT
.ft R
bit of the 
.ft CW
n_type
.ft R
field of
.ft CW
struct nlist.
.ft R
.SH
Testing, Validation and Verification
.IP "Regression tests"
While developing this assembler, I collected a series of files of assembly language.
I used this series of files to ensure that further development
didn't cause previously correct assembly to fail.
I did this by comparing the disassembled outputs of the GNU assembler and
my assembler for the same input.
Some of these files are written to exercise particular blocks
of code in the assembler, some are exhaustive checks of categories
of instructions (e.g. Bicc - branch on integer condition code) and some are
compiler outputs that triggered bugs.
.IP "Integration tests"
Regression tests have their place, but they don't check that symbol
table and relocation information  get generated correctly.
I wrote a series of C programs that cause compilers to
generate specific assembly language or specific types of relocation
information and symbol table entries.
Compiling these programs verifies that link-editing information is correct.
Running the compiled programs exercises the assembled machine code.
.IP "Memory usage"
I used several malloc debuggers in a continual attempt to detect memory leaks.
I used dmalloc version 3.1.3 by Gray Watson, and Electric Fence 2.0.1 by Bruce Perens.
This nearly convinced me that garbage collection is necessary.
.IP "Compiler dependencies"
I tried to reduce compiler dependencies in coding the assembler itself. 
During development I alternated between compiling the assembler with
the GNU C compiler provided with NetBSD/sparc 1.1 (GCC 2.4.5) and compiling
with Hansen and Fraser's 
.ft CW
lcc
.ft R
ANSI C compiler. I ran all my regression and integration tests against
assemblers compiled with both compilers.
.IP "ANSI C compliance"
I used compiler warnings to determine ANSI C compliance.
GNU C and 
.ft CW
lcc
.ft R
report different problems. For example, 
.ft CW
lcc
.ft R
reports on ``compiler dependent''
behaviors, while the GNU C compiler reports when all members of an enum aren't 
case labels in a switch.  I tried to eliminate all compiler warnings.
.IP "Branch coverage"
I used the 
.ft CW
lcc
.ft R
compiler to measure branch coverage.  Compiling with the proper options
causes 
.ft CW
lcc
.ft R
to produce instrumented code that counts actual executions
of basic blocks of code.
Assembling a large amount of compiler-generated code that has no assembler syntactic or semantic
errors causes this assembler to execute about 50% of its basic blocks
of code.
Assembling assembly language specifically written to contain semantic errors
raises this to about 75% of its basic blocks.
The remainder of the unexecuted blocks of code can be observed to
be error outputs for failure of system library calls like 
.ft CW
malloc(3)
.ft R
or
.ft CW
fwrite(3).
.ft R
.SH
Portability
.LP
Porting this software (in the sense of getting it to run on another platform or
under another OS) should be fairly easy, given a set of NetBSD/sparc
header files.  I tried to be ANSI-C compliant, using compilers and compiler options
to enforce this.  The program uses only stock ``stdio'' for input and output,
although it does do a lot of 
.ft CW
fseek()s
.ft R
to write instructions and data in the same file.
.LP
There are two issues that should be discussed further.
.IP "1. How easy would it be to get it to generate another object file format (e.g. ELF)?"
I think this would be moderately difficult.
There are two pervasive assumptions in the code that would be difficult to
work around.  One is that all object code has two ``segments'', one
full of machine code, one full of data.  Adapting this assembler to
a format that has multiple segments or sections of machine code and/or data might
be tricky.
The second problem is that the
.ft CW
a.out
.ft R
object file format permeates the routines that put together the 
machine code instructions.  Creation and filling-in of relocation information
is particularly intrusive.
.IP "2. What pitfalls are hidden in the code."
The big pitfalls here are the assumption that a C variable of type
.ft CW
int
.ft R
is the same size as an instruction, and that addresses and constants
calculated at assembly time are the size of a 32-bit
.ft CW
int.
.ft R
There may also be ``endian'' problems hidden in it.  
It assumes that compilers pack bit-field members of structs.
.SH
Further development
.LP
There are two areas where futher development that might actually pay off:
working to speed it up, and adding support for SPARC V9 instructions.
.LP
I never profiled execution of this assembler, nor made any determination of speed.
I estimate it's less than half as fast as NetBSD's system assembler.
Probably a small amount of further work could greatly speed up my assembler.
Two areas come to mind as potential improvements.
Opcode mnemonics and assembler directives are found by binary search of an array.
A pre-hashed table, or an Aho-Corasick type finite automata might be much faster.
Each pass over the input lexes and parses the input.  It wouldn't be
too hard to make the first pass save the parse trees,
and have the second pass just work from these trees instead of re-parsing the input.
.LP
Adding SPARC V9 instruction mnemonics shouldn't be very difficult at all.
I did not do this since my computer is SPARC V7: I felt I was stretching
to write a V8 assembler.
