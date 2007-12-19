/*
$Log: digit_label.c,v $
Revision 1.4  1997/02/27 07:42:55  bediger
complete re-write, one that finally works.

Revision 1.3  1997/02/22 23:49:07  bediger
another wrongish way to do it, but a stab at "textual" nearness

Revision 1.2  1997/01/15 01:28:08  bediger
this is wrong: it needs to do the "nearest" based on textual nearness,
not address nearness

Revision 1.1  1996/12/19 06:49:31  bediger
Initial revision

*/

static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/digit_label.c,v 1.4 1997/02/27 07:42:55 bediger Exp bediger $";

#include <stdlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <a.out.h>
#include <nlist.h>

#include <assy.h>
#include <io.h>
#include <symtable.h>
#include <digit_label.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

extern int pass;

int digit_label_cnt[10] = {0,0,0,0,0,0,0,0,0,0};

void
reset_local_labels(void)
{
	int i;

	for (i = 0; i < sizeof(digit_label_cnt); ++i)
		digit_label_cnt[i] = 0;
}

struct nlist *
lookup_digit(char *sym_name)
{
	struct nlist *p;
	int digit;
	char dir, name_buf[16];

	digit = atoi(sym_name);  /* relies on atoi() stopping at 1st non-digit */
	dir   = sym_name[1];

	assert(-1 < digit && 10 > digit);
	assert('f' == dir || 'b' == dir);

	sprintf(name_buf, "L.%d.%d", digit,
		'b' == dir ? digit_label_cnt[digit] - 1 : digit_label_cnt[digit]);

	p = symbol_named(name_buf);

	if ('b' == dir && NULL == p)
		internal_problem(__FILE__, __LINE__,
			"local label \"%d%c\" (%s): backward ref had no symbol\n",
			digit, dir, name_buf);

	/* this is slightly redundant - some or all of the routines calling
	 * symbol_named() (which calls this) also do an add_symbol_named(),
	 * but it has to be done to conceal the fact that local (digit)
	 * labels get turned into local (L) symbols */

	if (NULL == p)
		p = add_symbol_named(name_buf);

	return p;
}

struct nlist *
assemble_digit_label(int digit)
{
	struct nlist *p;
	char name_buf[16];  /* allows 11 digits worth of symbols for any given label */

	assert(-1 < digit && 10 > digit);

	sprintf(name_buf, "L.%d.%d", digit, digit_label_cnt[digit]);

	if (NULL != (p = symbol_named(name_buf)))
		internal_problem(__FILE__, __LINE__,
			"assembling local label \"%d\" (pseudo-symbol %s): already had a symbol\n",
			digit, name_buf);

	p = add_symbol_named(name_buf);
	p->n_value = N_UNDF;
	p->n_type = N_UNDF;

	passed_local(digit);

	return p;
}

void
passed_local(int digit)
{
	assert(-1 < digit && 10 > digit);
	++digit_label_cnt[digit];
}

struct nlist *
local_symbol_named(int digit)
{
	struct nlist *p;
	char name_buf[16];  /* allows 11 digits worth of symbols for any given label */

	assert(-1 < digit && 10 > digit);

	sprintf(name_buf, "L.%d.%d", digit, digit_label_cnt[digit]);

	p  = symbol_named(name_buf);

	if (2 == pass && NULL == p)
		internal_problem(__FILE__, __LINE__,
			"local label \"%d\" (%s): didn't have a symbol\n",
			digit, name_buf);

	return p;
}
