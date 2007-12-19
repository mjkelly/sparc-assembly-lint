/*
 * Need to include nlist.h, machine/exec.h before including this file
 */
/* $Id: symtable.h,v 1.3 1997/01/05 08:50:05 bediger Exp bediger $
$Log: symtable.h,v $
Revision 1.3  1997/01/05 08:50:05  bediger
added SYMBOL_TYPE, IS_SYMBOL_TYPE, CURR_SEG_TYPE macros

Revision 1.2  1996/12/29 01:17:03  bediger
changed prototype to have filename and line number as args so
that extra debugging info could be generated if desired

Revision 1.1  1996/12/13 14:36:37  bediger
Initial revision

*/

#define SYMBOL_TYPE(sym) (((sym)->n_type&N_TYPE)&(~N_EXT))
#define IS_SYMBOL_TYPE(sym, ty) ((ty)==SYMBOL_TYPE(sym))
#define CURR_SEG_TYPE ((current_segment == TEXT_SEG)?N_TEXT:N_DATA)


void run_symtable(void);
void init_symtable(void);
void free_symtable(void);
void init_relocation(void);


struct nlist *assemble_label(struct expr_node *expr);

void insert_relocation(char *file, int linenum, struct relocation_info *reloc, struct nlist *symbol);

struct stringtable *create_stringtable(int weedout_locals);

unsigned long write_symtable(FILE *a_out, struct stringtable *stbl);

struct nlist *symbol_named(char *symbol_name);

struct nlist *add_symbol_named(char *sym_name);

void add_stab(struct nlist *stab);

void enumerate_symbols(int weedout_locals);
void adjust_segment(int segment, int offset);
unsigned long write_text_relocations(FILE *a_out);
unsigned long write_data_relocations(FILE *a_out);

void resolve_text_references(FILE *text_seg);
void resolve_data_references(FILE *text_seg);

char *print_reloc_type(enum reloc_type rt);
char *print_n_type(char ntype);   /* readable rep of nlist's n_type field */


struct stringtable {
	unsigned long length;
	char         *data;
};

struct rlc {
	struct relocation_info *reloc;
	struct nlist           *sym;
};

struct relocations {
	int used;
	int size;

	struct rlc *data;
};
