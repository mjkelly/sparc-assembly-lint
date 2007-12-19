/*
$Log: directives.c,v $
Revision 1.9  1997/03/14 05:41:00  bediger
make code reflect changes to struct expr_node (minimize size of that struct)
add code to handle .double, .single, .int, .long directives, not all
of them correctly.

Revision 1.8  1997/03/10 01:15:34  bediger
add stubs for .single and .double assembler directives.

Revision 1.7  1997/02/14 06:27:58  bediger
remove dead code - stab_directive() function not used
add '.comm' directive handling.

Revision 1.6  1997/02/04 03:59:48  bediger
support for changed assembly statement representation

Revision 1.5  1997/01/15 01:28:55  bediger
massive changes to have these functions do a list of arguments
instead of a set number

Revision 1.4  1997/01/05 08:54:26  bediger
fix bugs relating to .reserve, .common and BSS segment

Revision 1.3  1996/12/29 01:19:43  bediger
support for cmd-line specification of symbol table debugging

Revision 1.2  1996/12/14 20:01:22  bediger
removed some commented-out dead code

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/directives.c,v 1.9 1997/03/14 05:41:00 bediger Exp bediger $";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <assert.h>
#include <ctype.h>
#include <a.out.h>

#include <assy.h>
#include <io.h>
#include <symtable.h>
#include <expr.h>
#include <shortcut_alloc.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

extern int pass;

int align_directive(char *directive, struct expr_list_node *);
int skip_directive(char *directive, struct expr_list_node *);
int text_directive(char *directive, struct expr_list_node *);
int data_directive(char *directive, struct expr_list_node *);
int word_directive(char *directive, struct expr_list_node *);
int half_directive(char *directive, struct expr_list_node *);
int byte_directive(char *directive, struct expr_list_node *);
int ascii_directive(char *directive, struct expr_list_node *);
int stabd_directive(char *directive, struct expr_list_node *);
int stabn_directive(char *directive, struct expr_list_node *);
int stabs_directive(char *directive, struct expr_list_node *);
int common_directive(char *directive, struct expr_list_node *);
int seg_directive(char *directive, struct expr_list_node *);
int global_directive(char *directive, struct expr_list_node *);
int fp_const_directive(char *directive, struct expr_list_node *);

int unimp_directive(char *directive, struct expr_list_node *);
extern struct mem_stack int_alloc;

struct bzx assembler_directives[] = {
{".align", align_directive, -1, align_directive},
{".ascii", ascii_directive, -1, ascii_directive},
{".asciz", ascii_directive, -1, ascii_directive},
{".byte", byte_directive, -1, byte_directive},
{".comm", common_directive, -1, common_directive},
{".common", common_directive, -1, common_directive},
{".data", data_directive, -1, data_directive},
{".double", fp_const_directive, -1, fp_const_directive},
{".global", global_directive, 0, NULL},
{".globl", global_directive, 0, NULL},
{".half", half_directive, -1, half_directive},
{".int", word_directive, -1, word_directive},
{".long", word_directive, -1, word_directive},
{".proc", NULL, 0, NULL}, /* This directive is ignored. */
{".reserve", common_directive, -1, common_directive},
{".seg", seg_directive, -1, seg_directive},
{".short", half_directive, -1, half_directive},
{".single", fp_const_directive, -1, fp_const_directive},
{".size", NULL, 0, NULL},  /* `.size' is only meaningful when generating COFF format output */
{".skip", skip_directive, -1, skip_directive},
{".space", skip_directive, -1, skip_directive},
{".stabd", stabd_directive, 0, NULL},
{".stabn", stabn_directive, 0, NULL},
{".stabs", stabs_directive, 0, NULL},
{".text", text_directive, -1, text_directive},
{".type", NULL, 0, NULL},
{".word", word_directive, -1, word_directive},
};

int
bzx_cmp(const void *key, const void *array_element)
{
	const struct bzx *p = array_element;
    return strcmp(key, p->directive);
}

struct bzx *
assembler_directive(char *s)
{
	struct bzx *p;

	assert(NULL != s);

	p = bsearch(
		(void *)s,
		(void *)assembler_directives,
		sizeof(assembler_directives)/sizeof(*assembler_directives),
		sizeof(*assembler_directives),
		bzx_cmp
	);

	return p;
}

void
print_directive_list(char *fmt, char *directive, struct expr_list_node *list)
{
	input_problem(fmt, directive);
	while (list)
	{
		print_expr(stderr, list->expression);
		list = list->next;
	}
	fputc('\n', stderr);
}

int
align_directive(char *directive, struct expr_list_node *list)
{
	int *alignment, off, r = 0;
	struct nlist *ntmp;
	struct relocation_info *rtmp;
	struct register_address ra;

	assert(NULL != directive);
	assert(NULL != list);

	switch (expr_to_imm(list->expression, &ntmp, &rtmp, &alignment, &ra))
	{
	case SYMBOL:
		print_directive_list("%s directive has bad stuff: ", directive, list);
		break;

	case VALUE:

		off = *alignment - (CURROFFSET % *alignment);

		if (off != *alignment)
		{
			if (1 == pass)
			{
				r = off;
			} else {
				while (off--)
				{
					fputc('\0', a_out);
					++CURROFFSET;
				}
			}
		}
		break;
	case REGISTER:
		internal_problem(__FILE__, __LINE__, "%s directive a bad place for register: ", directive);
		print_expr(stderr, list->expression);
		break;
	}

	if (rtmp) free(rtmp);
	if (alignment) ASM_DEALLOC(alignment, int_alloc);

	if (list->next)
		print_directive_list("%s directive: too many parameters", directive, list);

	return r;
}

int
seg_directive(char *directive, struct expr_list_node *list)
{
	int r;
	char *line, *p;
	
	if (ExprStr == list->expression->kind)
		line = list->expression->u.id;
	else {
		print_directive_list("seg_directive(), directive %s, wrong expression: ", directive, list);
		return 0;
	}

	if (NULL != (p = strstr(line, "text")))
		r = text_directive(".text", NULL);
	else if (NULL != (p = strstr(line, "data")))
		r = data_directive(".data", NULL);
	else
		r = 0;

	return r;
}

int
global_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *sym;
	char *line;
	
	while (list)
	{
		if (ExprSym != list->expression->kind)
		{

			input_problem("%s directive, problem with symbol: ", directive);
			print_expr(stderr, list->expression);
			fputc('\n', stderr);

			list = list->next;

			continue;
		}

		line = list->expression->u.id;

		if (sym_debug)
			fprintf(stderr, ".global directive, marking symbol named \"%s\" as N_EXT\n", line);

		if (NULL == (sym = symbol_named(line)))
		{
			/* add a (blank) new symbol */
			sym = add_symbol_named(line);
			sym->n_type  = N_UNDF;
			sym->n_value = 0;
		}

		sym->n_type |= N_EXT;

		list = list->next;
	}

	return 0;
}

int
skip_directive(char *directive, struct expr_list_node *list)
{
	int *skip, r = 0;
	struct nlist *ntmp; struct relocation_info *rtmp;
	struct register_address ra;

	expr_to_imm(list->expression, &ntmp, &rtmp, &skip, &ra);

	if (1 == pass)
		r += *skip;
	else
		while ((*skip)--)
		{
			fputc('\0', a_out);
			++CURROFFSET;
		}

	if (rtmp) free(rtmp);
	ASM_DEALLOC(skip, int_alloc);

	if (list->next)
		print_directive_list("%s directive, more than one argument:",
			directive, list);

	return r;
}

void
seg_seek(long offset)
{
	if (fseek(a_out, offset, SEEK_SET) < 0)
		internal_problem(
			__FILE__, __LINE__,
			"2nd pass, %s directive, couldn't seek to 0x%x: %s\n",
			CURSEGNAME, offset,
			strerror(errno)
		);
}

int
text_directive(char *directive, struct expr_list_node *list)
{
	current_segment = TEXT_SEG;

	/* output FILE pointer has to be kept correct only on 2nd pass */
	if (2 == pass)
		seg_seek(outs_offset[current_segment] + sizeof(struct exec));

	return 0;
}

/* also referenced and used in assembler.c - CURRADDR macro */
int text_size = 0;

int
data_directive(char *directive, struct expr_list_node *list)
{
	current_segment = DATA_SEG;

	if (2 == pass)
		seg_seek(outs_offset[current_segment] + sizeof(struct exec) + text_size);

	return 0;
}

/*
`.half N'
     Define a two-byte integer constant N; synonym for the portable
     `as' directive `.short'.
*/
int
half_directive(char *directive, struct expr_list_node *list)
{
	int r = 0;

	assert(NULL != directive);
	assert(NULL != list);

	while (list)
	{
		if (1 == pass)
			r += 2;
		else {
			unsigned short contents;
			int *value;
			struct nlist *sym;
			struct relocation_info *reloc;
			struct register_address ra;

			expr_to_imm(list->expression, &sym, &reloc, &value, &ra);

			if (reloc) free(reloc);

			contents = (unsigned short)*value;
		
			if (fwrite(&contents, sizeof(contents), 1, a_out) != 1)
			{
				internal_problem(__FILE__, __LINE__, "Failed to write .byte %d to current segment %d: %s\n",
					contents, current_segment, strerror(errno));
			} else {
				/* didn't write it, can't increment offset */
				CURROFFSET += sizeof(contents);
			}
			if (value) ASM_DEALLOC(value, int_alloc);
		}

		list = list->next;
	}

	return r;
}

int
byte_directive(char *directive, struct expr_list_node *list)
{
	int r = 0;

	assert(NULL != directive);
	assert(NULL != list);

	while (list)
	{
		if (1 == pass)
			r += 1;
		else {
			unsigned char contents;
			int *value;
			struct nlist *sym;
			struct relocation_info *reloc;
			struct register_address ra;

			expr_to_imm(list->expression, &sym, &reloc, &value, &ra);

			if (reloc) free(reloc);

			contents = (unsigned char)*value;
		
			if (fwrite(&contents, sizeof(contents), 1, a_out) != 1)
			{
				internal_problem(__FILE__, __LINE__, "Failed to write .byte %d to current segment %d: %s\n",
					contents, current_segment, strerror(errno));
			} else {
				/* didn't write it, can't increment offset */
				CURROFFSET += sizeof(contents);
			}

			if (value) ASM_DEALLOC(value, int_alloc);
		}

		list = list->next;
	}

	return r;
}

int
ascii_directive(char *directive, struct expr_list_node *list)
{
	int r = 0;

	assert(NULL != directive);
	assert(NULL != list);

	while (list)
	{
		int  used = 0, cc;
		char *buf, *f = list->expression->u.id;
		int sz = strlen(list->expression->u.id);

		/* the logic here is that if the string following the .ascii or .asciz
	 	* directive has any backslash-escaped characters, it will be shorter
	 	* than sz in its final form.  It will be no longer than sz+1 if we
	 	* have to add the final ASCII nul at the end (.asciz) */

		buf = malloc(sz+1);
		assert(NULL != buf);

		for(; *f; ++f)
		{
			if ('\\' != *f)
				buf[used++] = *f;
			else {

				++f;  /* character after the backslash */

				switch (*f)
				{
				case 'n': buf[used++] = '\n'; break;
				case 'r': buf[used++] = '\r'; break;
				case 't': buf[used++] = '\t'; break;
				case 'b': buf[used++] = '\b'; break;
				case 'f': buf[used++] = '\f'; break;
				default:

					/* have to handle the \0dd and \dd cases - how about hex? */
					/* apparently, GAS interprets \dd as an octal escape sequence */

					if (isdigit(*f))
					{
/* the part that's commented out - both \0dd and \dd are _octal_.  There's
 * no distinction between octal and decimal based on leading '0' character */
/*
						int multiplier;
						if ('0' == *f)
							multiplier = 010;
						else
							multiplier = 10;
*/
						int multiplier = 010;

						buf[used] = 0; /* NOT nul-terminated, it's now a number */
						while (isdigit(*f))
						{
							buf[used] = buf[used] * multiplier + (*f - '0');
							++f;
						}
						--f;
						++used;
					} else {
						/* I guess this means it's an escaped single char */
						buf[used++] = *f;
					}
				}
			}
		}

		if (!strcmp(directive, ".asciz"))
			buf[used++] = '\0';

		/* it may be too late, but if we haven't core-dumped, it'll
	 	* be worth double-checking */
		assert(used <= sz+1);

		if (1 == pass)
			r += used;
		else {
			if ((cc = fwrite(buf, 1, used, a_out)) != used)
			{
				internal_problem(
					__FILE__, __LINE__,
					"directive %s failed to write \"%s\" to %s segment: %s\n",
					directive,
					list->expression->u.id,
					((current_segment == TEXT_SEG)?".text":".data"),
					strerror(errno)
				);
				used = cc;
			}

			CURROFFSET += used;
		}

		free(buf);   /* buf can't possibly be NULL at this point */

		list = list->next;
	}

	return r;
}

/* what the hell does a .common directive do? */
int
common_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *symbol;
	char *name;
	int   size;

	name = list->expression->u.id;
	size = list->next->expression->u.val;

	if (NULL == (symbol = symbol_named(name)))
	{
		if (2 == pass)
			input_problem("pass %d, %s directive, defining symbol named \"%s\"\n",
				pass, directive, name);
		symbol = add_symbol_named(name);
	}

	if (!strcmp(directive, ".reserve"))
	{
		if (sym_debug)
			fprintf(stderr, "Marking symbol named \"%s\" as N_BSS\n", name);
		symbol->n_type |= N_BSS;
	}

	symbol->n_value = bss_offset;

	bss_offset += size;

	return 0;
}

/* fill_in_stab() probably assumes too much that it's list of directives args
 * is correct.  Could leak memory or make silly mistakes. */
void
fill_in_stab(struct nlist *stab, struct expr_list_node *list)
{
	struct nlist *ntmp;
	struct relocation_info *rtmp;
	int *value;
	struct register_address ra;

	expr_to_imm(list->expression, &ntmp, &rtmp, &value, &ra);
	stab->n_type = *value;
	if (rtmp) free(rtmp);
	if (value) ASM_DEALLOC(value, int_alloc);

	expr_to_imm(list->next->expression, &ntmp, &rtmp, &value, &ra);
	stab->n_other = *value;
	if (rtmp) free(rtmp);
	if (value) ASM_DEALLOC(value, int_alloc);

	expr_to_imm(list->next->next->expression, &ntmp, &rtmp, &value, &ra);
	stab->n_desc = *value;
	if (rtmp) free(rtmp);
	if (value) ASM_DEALLOC(value, int_alloc);
}

int stabd_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *stabd;

	/* .stabd          type, other, desc
	 *  value is the address of the location counter when .stadb assembled
	 *  name is a "null pointer"
	 */

	STRUCT_ALLOC(stabd, struct nlist);

	stabd->n_un.n_name = strcpy(malloc(1), "");  /* this is NOT a "null pointer" */

	fill_in_stab(stabd, list);

	stabd->n_value = CURROFFSET;

	add_stab(stabd);

	return 0;
}

int
stabn_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *stabn;
	struct nlist *ntmp;
	struct relocation_info *rtmp;
	int *value;
	struct register_address ra;

	/* .stabn          type, other, desc, value
	 * name set to empty string ("")
	 */

	STRUCT_ALLOC(stabn, struct nlist);

	stabn->n_un.n_name = strcpy(malloc(1), "");  /* this is NOT a "null pointer" */

	fill_in_stab(stabn, list);

	/* this is the .stabn's "value".  Is this always a string? */

	switch (expr_to_imm(list->next->next->next->expression, &ntmp, &rtmp, &value, &ra))
	{
	case VALUE:
		stabn->n_value = *value;
		break;
	case SYMBOL:
		/* should be a symbol already in symbol table complete with value? */
		if (NULL == ntmp)
		{
			internal_problem(__FILE__, __LINE__,
				".stabn value is a string \"%s\", no corresponding symbol\n",
				list->next->next->next->expression->u.id);
			stabn->n_value = 0;
		} else
			stabn->n_value = ntmp->n_value;
		break;
	case REGISTER:
		internal_problem(__FILE__, __LINE__, "%s directive a bad place for register: ", directive);
		print_expr(stderr, list->next->next->next->expression); putc('\n', stderr);
		break;
	}

	if (rtmp) free(rtmp);
	if (value) ASM_DEALLOC(value, int_alloc);

	add_stab(stabn);

	return 0;
}

int
stabs_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *stabs;
	struct nlist *ntmp;
	struct relocation_info *rtmp;
	int *value;
	struct register_address ra;

	/* .stabs string,  type, other, desc, value */

	STRUCT_ALLOC(stabs, struct nlist);

	stabs->n_un.n_name = list->expression->u.id;
	list->expression->u.id = NULL;

	fill_in_stab(stabs, list->next);

	/* this is the .stabs's "value".  Is this always a string? */

	switch (expr_to_imm(list->next->next->next->next->expression, &ntmp, &rtmp, &value, &ra))
	{
	case VALUE:
		stabs->n_value = *value;
		break;
	case SYMBOL:
		/* should be a symbol already in symbol table complete with value? */
		if (NULL == ntmp)
		{
			internal_problem(__FILE__, __LINE__,
				".stabs value is a string \"%s\", no corresponding symbol\n",
				list->next->next->next->next->expression->u.id);
			stabs->n_value = 0;
		} else
			stabs->n_value = ntmp->n_value;
		break;
	case REGISTER:
		internal_problem(__FILE__, __LINE__, "%s directive a bad place for register: ", directive);
		print_expr(stderr, list->expression);
		break;
	}

	if (rtmp) free(rtmp);
	if (value) ASM_DEALLOC(value, int_alloc);

	add_stab(stabs);

	return 0;
}

int unimp_directive(char *directive, struct expr_list_node *list)
{
	input_problem("unimplemented directive \"%s\"\n", directive);
	return 0;
}

/*
`.word'
     On the Sparc, the .word directive produces 32 bit values, instead
     of the 16 bit values it produces on many other machines.

 *  Has to handle this: ".word _alist+48" and this: ".word 5"
 * and even ".word _alist+48+4"
 */
int
word_directive(char *directive, struct expr_list_node *list)
{
	struct nlist *nl = NULL;
	struct relocation_info *reloc = NULL;
	int r = 0, *value;
	struct register_address ra;

	assert(NULL != list);

	while (list)
	{
		switch (expr_to_imm(list->expression, &nl, &reloc, &value, &ra))
		{
		case VALUE:
			break;
		case SYMBOL:
			*value = 0;  /* address the symbol's at is immaterial */
			break;
		case REGISTER:
			internal_problem(__FILE__, __LINE__, ".word directive a bad place for register: ");
			print_expr(stderr, list->expression); putc('\n', stderr);
			goto problem;
			break;
		}

		if (1 == pass)
		{
			r += 4;
			if (reloc)
				free(reloc);
		} else {
			/* may be a relocation record even for values */

			if (reloc)
			{
				reloc->r_type = RELOC_32;
				insert_relocation(__FILE__, __LINE__, reloc, nl);
			}

			if (!value || (fwrite(value, sizeof(value), 1, a_out) != 1))
			{
				internal_problem(__FILE__, __LINE__,
				"Failed to write .word to current segment %d: %s\n",
				current_segment, strerror(errno));
				return 0;
			} else
				CURROFFSET += sizeof(*value);
		}

		problem:

		if (value)
			ASM_DEALLOC(value, int_alloc);

		list = list->next;
	}
 
	return r;
}

int
fp_const_directive(char *directive, struct expr_list_node *list)
{
	int r = 0;
	int offset = 4;
	void *value;
	float f;

	assert(NULL != list);

	if (!strcmp(directive, ".double"))
		offset = 8;

	while (list)
	{
		if (1 == pass)
			r += offset;
		else {

			if (ExprFlt != list->expression->kind)
			{
				input_problem("%s directive, but value is a", directive);
				print_expr(stderr, list->expression);
				fputc('\n', stderr);
				list = list->next;
				continue;
			}

			if (4 == offset)
			{	/* these seems klunky */
				f = (float)list->expression->u.fltval;
				value = &f;
			} else if (8 == offset) {
				value = &list->expression->u.fltval;
			} else {
				input_problem("%s directive, bad offset: %d", directive, offset);
				list = list->next;
				continue;
			}

			if (fwrite(value, 1, offset, a_out) != offset)
			{
				internal_problem(__FILE__, __LINE__,
				"Failed to write %s (size %d) to current segment %d: %s\n",
				directive, offset,
				current_segment, strerror(errno));
			} else
				CURROFFSET += offset;
		}

		list = list->next;
	}

	return r;
}
