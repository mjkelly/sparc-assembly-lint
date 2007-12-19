/* need to #include <nlist.h> first */
/* $Id: hashtable.h,v 1.2 1997/01/05 08:44:31 bediger Exp bediger $
$Log: hashtable.h,v $
Revision 1.2  1997/01/05 08:44:31  bediger
removed delta member of struct hashtable.  Number of buckets
is doubled up reallocation to keep MOD() macro working.

Revision 1.1  1996/12/13 14:36:37  bediger
Initial revision

*/


struct hashnode {
	struct hashnode *next, *prev;          /* hash chain */
	struct hashnode *ord_next, *ord_prev;  /* in-order list */
	unsigned int value;                    /* hash value and chain split count */
	int lines_in_chain;
	struct nlist *symbol;
	int ordinal;
};

/* array of hash chains consists of the "head" nodes in the chains.
 * I doubled up use of two of the hashnode struct elements for per-chain
 * counts of events of interests.  This may not be too smart. */

struct hashtable {
	int p; /* next bucket to split */
	int maxp; /* upper bound on p during this expansion */

	int currentsize;
	int allocated;

	int maxload;     /* ave lines per chain for a rehash */

	int node_cnt;    /* number of nodes in hashtable */

	int rehash_cnt;  /* number of rehashes - one chain at a time */
	
	struct hashnode **buckets;    /* array of hash chains */
	struct hashnode **sentinels;  /* array of hash chains */

	struct hashnode *head, *tail; /* in order of addtion list of nodes */
};

/* number of buckets has to be a power of 2 for this to work */
#define MOD(x,y)        ((x) & ((y)-1))

int  add_symbol(struct hashtable *h, struct nlist *sym);
void init_hashtable(struct hashtable *h, int initial_buckets, int maxload);
struct nlist *symbol_lookup(struct hashtable *h, char *string_to_lookup);
struct hashnode *node_lookup(struct hashtable *h, char *string_to_lookup);
void free_hashtable(struct hashtable *h);
unsigned int hash_pjw(char *s);
struct nlist *remove_symbol(struct hashtable *h, char *symname);
struct hashnode *unchain_node(struct hashnode *node);
void add_unhashed_symbol(struct hashtable *tbl, struct nlist *nl);
