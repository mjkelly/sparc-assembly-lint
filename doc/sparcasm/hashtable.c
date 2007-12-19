/*
$Log: hashtable.c,v $
Revision 1.4  1997/02/14 06:30:35  bediger
remove dead code: unchain_node() and remove_symbol() are not used.

Revision 1.3  1997/01/05 08:44:31  bediger
changed bucket expansion in reallocate_buckets() to double
number of buckets each time.  This lets the MOD() macro
in hashtable.h work properly.

Revision 1.2  1996/12/14 20:01:02  bediger
removed some ifdef'ed dead code

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/hashtable.c,v 1.4 1997/02/14 06:30:35 bediger Exp bediger $";
 
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <a.out.h>
#include <nlist.h>
#include <string.h>

#include <hashtable.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif


void rehash_hashtable(struct hashtable *h);
void free_hashtable(struct hashtable *h);
void reallocate_buckets(struct hashtable *h);
int  sparsebit(long i);
int  msbbit(long i);

/* chain is the dummy node at head of hash chain */
void
insert_node(struct hashnode *chain, struct hashnode *n)
{
	n->next = chain->next;
	chain->next = n;
	n->next->prev = n;
	n->prev = chain;
}

void
init_hashtable(struct hashtable *h, int buckets, int maxload)
{
	int i;
	int f, z;

	/* Insure that bucket array size is always a multiple of 2.
	 * This amounted to about 10% run-time savings for small files
	 * by avoiding the '%' operator. */

	f = msbbit(buckets);
	z = 1 << f;

	if (z < buckets)
		z <<= 1;

	buckets = z;

	/* buckets and sentinels */
	h->buckets =
		(struct hashnode **)malloc(buckets*sizeof(*h->buckets));
	assert(h->buckets != NULL);
	bzero(h->buckets, buckets*sizeof(*h->buckets));

	h->sentinels =
		(struct hashnode **)malloc(buckets*sizeof(*h->sentinels));
	assert(h->sentinels != NULL);
	bzero(h->sentinels, buckets*sizeof(*h->sentinels));

	for (i = 0; i < buckets; ++i)
	{
		/* first node is a dummy - for convenience and to hold chain stats */

		h->buckets[i] = (struct hashnode *)malloc(sizeof(*h->buckets[i]));
		assert(h->buckets[i] != NULL);

		h->sentinels[i] = (struct hashnode *)malloc(sizeof(*h->sentinels[i]));
		assert(h->sentinels[i] != NULL);

		h->buckets[i]->next = h->sentinels[i];
		h->buckets[i]->prev = h->buckets[i];
		h->sentinels[i]->next = h->sentinels[i];
		h->sentinels[i]->prev = h->buckets[i];

		h->buckets[i]->symbol = NULL;
		h->buckets[i]->value = 0;    /* split count of chain */
		h->buckets[i]->lines_in_chain = 0;    /* split count of chain */
		h->buckets[i]->ord_next = h->buckets[i]->ord_prev = NULL;
	}

	/* bucket allocation */
	h->currentsize = buckets;
	h->allocated = buckets;

	h->maxload = maxload;

	/* bucket splitting */
	h->p = 0;
	h->maxp = buckets;

	h->node_cnt = 0;
	h->rehash_cnt = 0;

	/* in-order-of-addition list */
	h->head = (struct hashnode *)malloc(sizeof(*h->head));
	h->tail = (struct hashnode *)malloc(sizeof(*h->tail));

	h->head->ord_next = h->tail;
	h->head->ord_prev = h->head;

	h->tail->ord_prev = h->head;
	h->tail->ord_next = h->tail;
}

void
rehash_hashtable(struct hashtable *h)
{
	struct hashnode *l;
	struct hashnode *oldbucket, *oldtail;
	int newindex;

	assert(NULL != h);

	++h->rehash_cnt;

	if (h->currentsize >= h->allocated)
		reallocate_buckets(h);

	oldbucket = h->buckets[h->p];
	oldtail = h->sentinels[h->p];
	l = oldbucket->next;

	oldbucket->next = oldtail;
	oldtail->prev = oldbucket;

	oldbucket->lines_in_chain = 0;  /* may not be any lines in chain after rehash */
	++oldbucket->value;      /* number of splits */

	newindex = h->p + h->maxp;

	++h->p;

	if (h->p == h->maxp)
	{
		h->maxp *= 2;
		h->p = 0;
	}

	++h->currentsize;

	while (oldtail != l)
	{
		struct hashnode *t = l->next;
		int index = MOD(l->value, h->maxp);

		if (index < h->p)
			index = MOD(l->value, (2*h->maxp));

		if (index == newindex)
		{
			insert_node(h->buckets[newindex], l);
			++h->buckets[newindex]->lines_in_chain;
		} else {
			insert_node(oldbucket, l);
			++oldbucket->lines_in_chain;
		}

		l = t;
	}
}

void
reallocate_buckets(struct hashtable *h)
{
	int i;
	int newallocated;

	assert(NULL != h);
	assert(NULL != h->buckets);
	assert(NULL != h->sentinels);

	newallocated = h->allocated * 2;

	h->buckets = (struct hashnode **)realloc(
		h->buckets,
		sizeof(struct hashnode *)*newallocated
	);

	assert(NULL != h->buckets);

	h->sentinels = (struct hashnode **)realloc(
		h->sentinels,
		sizeof(struct hashnode *)*newallocated
	);

	assert(NULL != h->sentinels);

	for (i = h->allocated; i < newallocated; ++i)
	{
		h->buckets[i] = (struct hashnode *)malloc(sizeof(*h->buckets[i]));
		h->sentinels[i] = (struct hashnode *)malloc(sizeof(*h->sentinels[i]));

		h->buckets[i]->next = h->sentinels[i];
		h->sentinels[i]->prev = h->buckets[i];
		h->sentinels[i]->next = h->sentinels[i];
		h->buckets[i]->prev = h->buckets[i];
		h->sentinels[i]->ord_next = h->sentinels[i]->ord_prev = h->buckets[i]->ord_next = 
			h->buckets[i]->ord_prev = NULL;

		h->buckets[i]->lines_in_chain = 0;
		h->buckets[i]->value = 0;    /* number of times chain splits, too */
	}

	h->allocated = newallocated;
}

/*
 * Inserts a pre-allocated struct nlist into the hashtable named 'h'.
 * The nlist should have the n_name field filled out, not the n_strx
 * field.
 */
int
add_symbol(struct hashtable *h, struct nlist *sym)
{
	struct hashnode *n, *head;
	int bucket_index;
	unsigned int hv;

	assert(NULL != h);
	assert(NULL != sym);

	hv = hash_pjw(sym->n_un.n_name);

	bucket_index = MOD(hv, h->maxp);
	if (bucket_index < h->p)
		bucket_index = MOD(hv, (2*h->maxp));

	/* allocate new node */
	n = (struct hashnode *)malloc(sizeof(*n));
	assert(NULL != n);

	/* fill in newly allocated node */
	n->value = hv;
	n->symbol = sym;

	/* add newly allocated node to appropriate chain */
	head = h->buckets[bucket_index];

	/* just push it on the chain */
	n->next = head->next;
	head->next = n;
	n->next->prev = n;
	n->prev = head;

	/* add newly allocated node to in-order list */
	n->ord_next = h->tail;
	n->ord_prev = h->tail->ord_prev;
	n->ord_prev->ord_next = n;
	h->tail->ord_prev = n;

	++h->buckets[bucket_index]->lines_in_chain;

	++h->node_cnt;

	/* "load" on hashtable too high? */
	if (h->node_cnt/h->currentsize > h->maxload)
		rehash_hashtable(h);

	return 0;
}

void free_hashtable(struct hashtable *h)
{
	int i;
	struct hashnode *p;

	assert(NULL != h);
	assert(NULL != h->buckets);

	p = h->head->ord_next;

	/* free in order of addition: some symbols aren't hashed (stabs)
	 * and this is the only way to pick them up. */

	while (h->tail != p)
	{
		struct hashnode *t = p->ord_next;

		/* symbol names freed when going to n_un.n_strx */
		/* free(p->symbol->n_un.n_name); */
	
		free(p->symbol);

		free(p);
		p = t;
	}

	for (i = 0; i < h->allocated; ++i)
	{
		free(h->buckets[i]);
		free(h->sentinels[i]);
	}

	free(h->buckets);
	free(h->sentinels);
	free(h->head);
	free(h->tail);
}

struct nlist * 
symbol_lookup(struct hashtable *h, char *string_to_lookup)
{
	struct hashnode *hn = NULL;
	struct nlist *r = NULL;

	if (NULL != (hn = node_lookup(h, string_to_lookup)))
		r = hn->symbol;

	return r;
}

void
add_unhashed_symbol(struct hashtable *h, struct nlist *nl)
{
	struct hashnode *n = malloc(sizeof(*n));

	n->next = n->prev = NULL;
	n->symbol = nl;

	n->ord_next = h->tail;
	n->ord_prev = h->tail->ord_prev;
	n->ord_prev->ord_next = n;
	h->tail->ord_prev = n;
}

struct hashnode *
node_lookup(struct hashtable *h, char *string_to_lookup)
{
	struct hashnode *r = NULL;
	unsigned int hashval = hash_pjw(string_to_lookup);
	int index = MOD(hashval, h->maxp);
	struct hashnode *chain;

	if (index < h->p)
		index = MOD(hashval, (2*h->maxp));

	chain = h->buckets[index]->next;

	while (chain != h->sentinels[index])
	{
		if (chain->value == hashval &&
			!strcmp(chain->symbol->n_un.n_name, string_to_lookup))
		{
			r = chain;
			break;
		}

		chain = chain->next;
	}

	return r;
}

#define NBITS_IN_UNSIGNED   32 /* (NBITS(unsigned int))*/
#define SEVENTY_FIVE_PERCENT ((int)(NBITS_IN_UNSIGNED * 0.75))
#define TWELVE_PERCENT ((int)(NBITS_IN_UNSIGNED * 0.125))
#define HIGH_BITS (~((unsigned int)(~0) >> TWELVE_PERCENT))

unsigned int
hash_pjw(char *s)
{
	unsigned int g, h0 = 0;

	while (*s)
	{
		h0 = (h0 << TWELVE_PERCENT) + *s++;
		if ((g = h0 & HIGH_BITS))
			h0 = (h0 ^ (g >> SEVENTY_FIVE_PERCENT)) & ~HIGH_BITS;
	}

	return h0;
}

int
sparsebit(long i)
{
	int p = 0;

	if (i == 0) return(-1);     /* no bits set */

	if ((i & (-i)) != i) return(-1);    /* two or more bits set */

	if (i & 0xAAAAAAAA) p++;
	if (i & 0xCCCCCCCC) p += 2;
	if (i & 0xF0F0F0F0) p += 4;
	if (i & 0xFF00FF00) p += 8;
	if (i & 0xFFFF0000) p += 16;

	return p;
}

int
msbbit(long i)
{
	long i2;

	if (i<0) return(31); /* speed-up assumes a 'long's msb is at pos 31 */

	while ((i2 = (i & (i-1)))) i = i2;

	return(sparsebit(i));
}
