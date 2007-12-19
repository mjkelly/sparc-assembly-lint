# $Header: /home/ediger/src/csrc/sparc_assembler10/RCS/makefile,v 1.5 1997/03/21 07:42:26 bediger Exp bediger $
YACC = byacc
# YACCOPTS appropriate for byacc 1.8 and up?
YACCOPTS = -v -d
LEX = flex

GRAMMAR = assy
LEXER   = assy

# Princeton/Bell Labs lcc C compiler - Fraser and Hanson
CC = lcc -A
#CC = lcc.asm -A
#CC = gcc
OPTIMFLAG =
#PROFILFLAG = -DUSE_DMALLOC -DDMALLOC_FUNC_CHECK
#PROFILFLAG = -b   # basic block coverage w/ lcc 3.5
#PROFILFLAG =
#CFLAGS = $(OPTIMFLAG) -g -I. -I/usr/local/include -Wreturn-type -Wunused $(PROFILFLAG)
#CFLAGS2 = -Wall
CFLAGS = $(OPTIMFLAG) $(PROFILFLAG) -g -I. -I/usr/local/include

# compile y.tab.c with -DYYDEBUG, and setting env var YYDEBUG=[0-9]
# for a running account of the parse.

#Y_TAB_CFLAGS = -DYYDEBUG

#LIBS = -L/home/ediger/src/csrc/efence -lefence

# note that the cpp that comes with lcc doesn't allow redefining macro args
# lcc's cpp hates the way leak.h and dmalloc.h redefine malloc() and free()
#LIBS = /usr/local/lib/leak.o
#LIBS = -L/usr/local/lib -ldmalloc

SRCS = asm.c assembler.c digit_label.c directives.c expr.c \
	hashtable.c io.c misc.c mnemonic.c symtable.c
PARSER = assy.l assy.y
HDRS = assembler.h formats.h symtable.h assy.h hashtable.h \
	digit_label.h io.h expr.h shortcut_alloc.h
OTHERS = makefile design.ms asm.1

OBJFILES = y.tab.o lex.yy.o asm.o assembler.o digit_label.o \
	directives.o expr.o hashtable.o io.o misc.o mnemonic.o symtable.o

asm: $(OBJFILES)
	$(CC) $(OPTIMFLAG) $(PROFILFLAG) -g -o asm  $(OBJFILES) $(LIBS)

y.tab.o: y.tab.c y.tab.h assy.h symtable.h digit_label.h expr.h assembler.h io.h
	$(CC) $(CFLAGS) $(Y_TAB_CFLAGS) -c y.tab.c

lex.yy.o: lex.yy.c y.tab.h assy.h shortcut_alloc.h
	$(CC) $(CFLAGS) -c lex.yy.c

y.tab.c y.tab.h: $(GRAMMAR).y
	${YACC} ${YACCOPTS} $(GRAMMAR).y

lex.yy.c: $(LEXER).l
	${LEX} $(LEXER).l
mnemonic.o: mnemonic.c assy.h assembler.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c mnemonic.c
misc.o: misc.c assy.h io.h expr.h shortcut_alloc.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c misc.c
asm.o: asm.c assy.h io.h symtable.h shortcut_alloc.h digit_label.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c asm.c
directives.o: directives.c assy.h io.h symtable.h expr.h shortcut_alloc.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c directives.c
assembler.o: assembler.c assy.h io.h assembler.h formats.h symtable.h expr.h shortcut_alloc.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c assembler.c
symtable.o: symtable.c assy.h io.h expr.h symtable.h hashtable.h digit_label.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c symtable.c
hashtable.o: hashtable.c hashtable.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c hashtable.c
expr.o: expr.c assy.h io.h expr.h symtable.h shortcut_alloc.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c expr.c
io.o: io.c io.h assy.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c io.c
digit_label.o: digit_label.c assy.h digit_label.h io.h symtable.h
	$(CC) $(CFLAGS) $(CFLAGS2) -c digit_label.c

clean:
	-rm y.tab.c y.tab.h y.output lex.yy.c *.o
	-rm *.core *.bak *.BAK *.dir *.pag *.i *.db a.out
	-rm -rf scratch design.ps

coverage:
	rm -f prof.out
	sh check_coverage
	bprint > coverage

clobber:
	make clean
	rm tags asm

ctags:
	ctags $(SRCS) assy.[yl]

lines:
	@date
	wc -l $(SRCS) assy.[yl]


design.ps: design.ms
	groff -Tps -t -mgs design.ms > design.ps

asm.ps: asm.1
	groff -Tps -t -man asm.1 > asm.ps

tar:
	tar cvf asm.tar README $(SRCS) $(PARSER) $(HDRS) $(OTHERS)

shar:
	shar README asm.1  > asm.0.shar
	shar $(HDRS)       > asm.1.shar
	shar $(OTHERS)     > asm.2.shar
	shar $(PARSER)     > asm.3.shar
	shar assembler.c   > asm.4.shar
	shar directives.c  > asm.5.shar
	shar expr.c        > asm.6.shar
	shar asm.c hashtable.c > asm.7.shar
	shar digit_label.c io.c misc.c mnemonic.c > asm.8.shar
	shar symtable.c > asm.9.shar
