/*
$Log: asm.c,v $
Revision 1.9  1997/03/21 07:45:02  bediger
lcc-3.5 is stricter about struct initialization than gcc is.
Change an initialized struct so lcc-3.5 doesn't complain.

Revision 1.8  1997/03/14 05:44:16  bediger
changes to formatting of a constant used in setting file offset

Revision 1.7  1997/02/27 07:44:03  bediger
support for SunOS-style local labels

Revision 1.6  1997/02/14 06:18:05  bediger
remove hints of abilit to assemble from stdin

Revision 1.5  1997/01/15 01:22:01  bediger
changes to reflect directives as part of grammar

Revision 1.4  1997/01/05 08:57:47  bediger
fix bug relating to BSS segment, add command line option "help".

Revision 1.3  1996/12/29 01:20:58  bediger
support for several command-line options dealing with debugging output

Revision 1.2  1996/12/14 20:01:36  bediger
removed some unused cmd-line options

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/asm.c,v 1.9 1997/03/21 07:45:02 bediger Exp bediger $";

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <assert.h>
#include <a.out.h>

#include <assy.h>
#include <io.h>
#include <expr.h>
#include <symtable.h>
#include <digit_label.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif


extern char *optarg;
extern int   optind;

extern int yyparse(void);
extern int text_directive(char *directive, struct expr_list_node *);
extern int align_directive(char *directive, struct expr_list_node *);
extern int data_directive(char *directive, struct expr_list_node *);

void compose_hdr(struct exec *preallocated_hdr);
FILE *open_output(char *output_filename, int text_size, int data_size);

int pass2(void);

/* globals used all over the place */

int   pass;      /* 1 or 2 */
int   outs_offset[2] = {0, 0};
int   bss_offset = 0;
enum CurrentSegment current_segment;
int   lineno = 1;
char *working_input_file = NULL;
int   keep_locals = 0;
int   sym_debug = 0;
int   offset_debug = 0;
char *output_filename = "a.out";
FILE *a_out = NULL;

/* debug code: free all the stuff on the struct-specific allocation
 * stacks.  That way, just about any unfreed memory is a bug
void destroy_all_monsters()
{
#include <shortcut_alloc.h>

	extern struct mem_stack expr_alloc;
	extern struct mem_stack stmnt_alloc;
	extern struct mem_stack addr_alloc;
	extern struct mem_stack register_alloc;
	extern struct mem_stack int_alloc;
	int free_cnt = 0;

	while (expr_alloc.cnt)
	{
		free(expr_alloc.stack[--expr_alloc.cnt]);
		++free_cnt;
	}
	if (free_cnt != expr_alloc.allocations)
		fprintf(stderr, "expr trees: freed %d, allocated %d\n",
			free_cnt, expr_alloc.allocations);

	free_cnt = 0;
	while (stmnt_alloc.cnt)
	{
		free(stmnt_alloc.stack[--stmnt_alloc.cnt]);
		++free_cnt;
	}
	if (free_cnt != stmnt_alloc.allocations)
		fprintf(stderr, "stmnts: freed %d, allocated %d\n",
			free_cnt, stmnt_alloc.allocations);

	free_cnt = 0;
	while (addr_alloc.cnt)
	{
		free(addr_alloc.stack[--addr_alloc.cnt]);
		++free_cnt;
	}
	if (free_cnt != addr_alloc.allocations)
		fprintf(stderr, "addresses: freed %d, allocated %d\n",
			free_cnt, addr_alloc.allocations);

	free_cnt = 0;
	while (register_alloc.cnt)
	{
		free(register_alloc.stack[--register_alloc.cnt]);
		++free_cnt;
	}
	if (free_cnt != register_alloc.allocations)
		fprintf(stderr, "registers: freed %d, allocated %d\n",
			free_cnt, register_alloc.allocations);


	free_cnt = 0;
	while (int_alloc.cnt)
	{
		free(int_alloc.stack[--int_alloc.cnt]);
		++free_cnt;
	}
	if (free_cnt != int_alloc.allocations)
		fprintf(stderr, "ints: freed %d, allocated %d\n",
			free_cnt, int_alloc.allocations);

}
*/

int
main(int ac, char **av)
{
	int r;
	int opt;

	while (-1 != (opt = getopt(ac, av, "Lo:lO")))
	{
		switch (opt)
		{
		case 'O':
			offset_debug = 1;
			break;
		case 'l':
			sym_debug = 1;
			break;
		case 'o':
			output_filename = optarg;
			break;
		case 'L':
			keep_locals = 1;
			break;
		default:
			fprintf(stderr, "%s: SPARC assembler\n", *av);
			fprintf(stderr, "usage: %s [-o output_file] [-L] [-x] [-a] [input_file]\n", *av);
			fprintf(stderr,
				"-o <output_file>  specify name of assembled output, default \"a.out\"\n"
				"-L                retain compiler-generated \"local\" symbols\n"
				"-O                output segment offset writing information\n"
				"-l                output symbol table information\n"
				"last name on command line taken to be input file name\n"
				"There must be an input file specification\n");
			return 1;
			break;
		}
	}

	if (optind != ac)
	{
		FILE *f;
		extern FILE *yyin;

		if (NULL == (f = fopen(av[optind], "r")))
		{
			fprintf(stderr, "Failed to open assembler input file \"%s\": %s\n",
				av[optind], strerror(errno));
			return 1;
		}

		working_input_file = av[optind];
		yyin = f;
	} else {
		fprintf(stderr, "There must be an input file name: cannot work from stdin\n");
		return 1;
	}

	outs_offset[TEXT_SEG] = 0;
	outs_offset[DATA_SEG] = 0;
	current_segment = TEXT_SEG;

	/* prepare a.out header, relocation data table, symbol table, string
	 * table, temp file for text and data segments */

	init_symtable();
	init_relocation();

	pass = 1;

	r = yyparse();

	if (r)
		fprintf(stderr, "Bad input - shame on you\n");
	else
		r = pass2();

/*
	destroy_all_monsters();
*/

	return r;
}

struct expr_node      expr_8 = {ExprCon, NULL, NULL};
struct expr_list_node node_8 = {&expr_8, NULL};

int
pass2(void)
{
	int r;
	struct exec hdr;
	struct stringtable *strtbl;

	extern FILE *yyin;
	extern int text_size;

	/* fill in a.out hdr - aligns segment ends, too*/
	expr_8.u.val = 8;
	compose_hdr(&hdr);

	/* open and create correctly-sized file */
	a_out = open_output(
		output_filename,
		outs_offset[TEXT_SEG],
		outs_offset[DATA_SEG]
	);

	if (NULL == a_out)
		return 1;

	/* output a.out header */
	if (fwrite((void *)&hdr, sizeof(hdr), 1, a_out) != 1)
		internal_problem(__FILE__, __LINE__,
			"Problem with first write of exec header: %s",
			strerror(errno));

	/* update addresses (r_value) in data segment symbols */
	adjust_segment(N_DATA, outs_offset[TEXT_SEG]);
	adjust_segment(N_BSS,  outs_offset[TEXT_SEG] + outs_offset[DATA_SEG]);

	/* reset some globals */
	text_size = outs_offset[TEXT_SEG];
	bss_offset = outs_offset[TEXT_SEG] + outs_offset[DATA_SEG];
	outs_offset[TEXT_SEG] = 0;
	outs_offset[DATA_SEG] = 0;
	current_segment = TEXT_SEG;
	lineno = 1;
	rewind(yyin);
	reset_local_labels();

	/* make the 2nd pass */

	pass = 2;

	r = yyparse();

	if (r)
	{
		fprintf(stderr, "Bad input on 2nd pass\n");
		return r;
	}

	/* instructions and initialized data now in the pseudo-a.out
	 * file.  Seek to end of that stuff to write relocations,
	 * symbol table, string table. */

	text_directive(".text", NULL);
	outs_offset[TEXT_SEG] += align_directive(".align", &node_8);
	data_directive(".data", NULL);
	outs_offset[DATA_SEG] += align_directive(".align", &node_8);

	if (offset_debug)
		fprintf(stderr, "offset: real end of text and data at %d\n",
			ftell(a_out));

	if (fseek(a_out,
		sizeof(struct exec) + outs_offset[TEXT_SEG] + outs_offset[DATA_SEG],
		SEEK_SET) < 0)
	{
		internal_problem(
			__FILE__, __LINE__,
			"2nd pass, About to write relocations, couldn't seek to 0x%x + 0x%x + 0x%x: %s\n",
			sizeof(struct exec),
			outs_offset[TEXT_SEG],
			outs_offset[DATA_SEG],
			strerror(errno)
		);
	}

	if (offset_debug)
		fprintf(stderr, "offset: as per headers, end of text and data at %d\n",
			ftell(a_out));

	/* ordinalize symbols - do this after 2nd pass to get the extern refs
	 * correctly numbered, too */
	enumerate_symbols(!keep_locals);

	/* output relocation data */
	hdr.a_trsize = write_text_relocations(a_out);
	hdr.a_drsize = write_data_relocations(a_out);
	hdr.a_bss = bss_offset; /* bss_offset; */

	/* create string table, changing the pointer-to-symbol name
	 * into index into string table - needs to be done before writing
	 * out symbol table */
	strtbl = create_stringtable(!keep_locals);

	/* output symbol table */
	hdr.a_syms = write_symtable(a_out, strtbl);

	if (fseek(a_out, N_STROFF(hdr), SEEK_SET) < 0)
	{
		internal_problem(
			__FILE__, __LINE__,
			"2nd pass, About to write string table, couldn't seek to 0x%x: %s\n",
			N_STROFF(hdr),
			strerror(errno)
		);
	}

	if (offset_debug)
		fprintf(stderr, "offset: writing string table beginning at %d\n",
			ftell(a_out));
 
	/* output string table */
	if (fwrite((void *)&strtbl->length, 1, 4, a_out) != 4)
		fprintf(stderr, "Problem writing string table size: %s\n", strerror(errno));
	if (fwrite((void *)strtbl->data, 1, strtbl->length-4, a_out) != strtbl->length-4)
		fprintf(stderr, "Problem writing %d bytes of string table: %s\n",
			strtbl->length-4, strerror(errno));

	/* rewrite the now correct a.out hdr */
	rewind(a_out);
	if (fwrite((void *)&hdr, sizeof(hdr), 1, a_out) != 1)
		internal_problem(__FILE__, __LINE__,
			"Problem with second write of exec header: %s",
			strerror(errno));

	free(strtbl->data);
	free(strtbl);

	free_symtable();

	fclose(a_out);

	return 0;
}

FILE *
open_output(char *output_filename, int text_size, int data_size)
{
	char buf[BUFSIZ];
	int cnt, rem;
	FILE *r;

	assert(NULL != output_filename);

	memset(buf, '\0', BUFSIZ);

	/* is this the place to decide to use stdout? */

	if (NULL == (r = fopen(output_filename, "w+")))
	{
		fprintf(stderr, "Problem opening \"%s\" in w+ mode: %s\n",
			output_filename, strerror(errno));
		return NULL;
	}

	cnt = (text_size + data_size + sizeof(struct exec))/BUFSIZ;
	rem = (text_size + data_size + sizeof(struct exec))%BUFSIZ;

	if (offset_debug)
		fprintf(stderr, "offset: writing a file %d (header) + %d (text)  + %d (data) = %d bytes long\n",
			sizeof(struct exec), text_size, data_size,
			text_size + data_size + sizeof(struct exec));

	while (cnt--)
		fwrite(buf, BUFSIZ, 1, r);

	if (rem)
		fwrite(buf, rem, 1, r);

	rewind(r);

	return r;
}

void
compose_hdr(struct exec *r)
{
	N_SETMAGIC(*r, OMAGIC, MID_SPARC, 0);

	/* these basically get the offsets correct at the end of the segments */
	text_directive(".text", NULL);
	outs_offset[TEXT_SEG] += align_directive(".align", &node_8);
	data_directive(".data", NULL);
	outs_offset[DATA_SEG] += align_directive(".align", &node_8);

	r->a_text = outs_offset[TEXT_SEG];
	r->a_data = outs_offset[DATA_SEG];
	r->a_entry = 0x0;
	r->a_bss = r->a_trsize = r->a_drsize = r->a_syms = 0;

	return;
}
