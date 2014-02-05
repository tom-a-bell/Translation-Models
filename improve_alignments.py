#! /usr/bin/python

__author__="Tom Bell <tom.bell.code@gmail.com>"
__date__ ="$Apr 30, 2013"

import sys
import codecs

"""
Find improved alignments between the english and foreign words in a set of
parallel translations based on previously determined alignments from both
p(f|e) and p(e|f) translation directions (e<->f).
"""

# Debug output flag
debug = False

class Parser:
    def __init__(self):
        self.ae = {} # Alignments from p(f|e)
        self.af = {} # Alignments from p(e|f)
        self.n = 0 # Number of sentence pairs

    def read_alignments(self, english_alignments, foreign_alignments):
        """
        Read the previously determined alignments for each (e, f) pair
        based on IBM model 2 estimates for p(f|e) and p(e|f), i.e. for
        both translation directions (e<->f) from the input files.
        """
        if debug: sys.stdout.write("Reading previous alignments...\n")

        file = codecs.open(english_alignments, encoding='utf-8', mode='r')
        file.seek(0)
        for line in file:
            token = line.split()
            k = int(token[0])
            j = int(token[1])
            i = int(token[2])
            self.ae.setdefault(k, set())
            self.ae[k].add((i, j))
        file.close()

        file = codecs.open(foreign_alignments, encoding='utf-8', mode='r')
        file.seek(0)
        for line in file:
            token = line.split()
            k = int(token[0])
            i = int(token[1])
            j = int(token[2])
            self.af.setdefault(k, set())
            self.af[k].add((i, j))
        file.close()

        # Check there are equal numbers of english and foreign alignments
        self.n = len(self.ae)
        if len(self.af) != self.n:
            sys.stderr.write("""ERROR: English and foreign alignment files
                                contain different number of sentences.\n""")
            sys.exit(1)

    def improve_alignments(self, k):
        """
        Improve the alignment for sentence pair k under the following heuristics:

         - take the intersection of the two alignments as the starting point;
         - grow the set by adding one additional alignment point at a time;
         - explore only alignments in the union of the two alignment sets;
         - only add points which align a word that currently has no alignment;
         - restrict potential additions to adjacent or diagonal neighbours
           of current points.
        """

        # Positions of adjacent and diagonal neighbouring points
        neighbours = ((-1, +0), (+1, +0), (+0, -1), (+0, +1),
                      (-1, -1), (-1, +1), (+1, -1), (+1, +1))

        # The two alignments, p(f|e) and p(e|f), for sentence pair k
        ae = self.ae[k]
        af = self.af[k]

        # Calculate the union and intersection of the two alignments
        union = ae.union(af)
        alignment = ae.intersection(af)

        if debug:
            sys.stdout.write("\nGrowing alignment for sentence pair #%d...\n" % k)
            sys.stdout.write("Starting with intersection of p(f|e) and p(e|f):\n")
            for (i, j) in alignment: sys.stdout.write("(%2d,%2d)\n" % (i, j))
            sys.stdout.write("\n")

        # Store the english and foreign words that already
        # have alignments as a tuple of two sets ({i},{j})
        words = (set([i for (i, j) in alignment]),
                 set([j for (i, j) in alignment]))

        # Grow the set by adding one additional alignment point at a time,
        # exploring only alignments in the union of the two alignment sets
        for (i, j) in union.difference(alignment):
            if debug:
                sys.stdout.write("Examining alignment point (%2d,%2d)...\n"
                                 % (i, j))

            # Add adjacent or diagonal neighbours of current alignment points;
            # excluding those which align a word that already has an alignment
            for (di, dj) in neighbours:
                if (i + di, j + dj) in alignment:
                    if debug:
                        sys.stdout.write(" -> neighbour exists (%2d,%2d)... "
                                         % (i + di, j + dj))
                    if i not in words[0] or j not in words[1]:
                        if debug: sys.stdout.write("added\n")
                        alignment.add((i, j))
                        words[0].add(i)
                        words[1].add(j)
                    else:
                        if debug: sys.stdout.write("exists\n")

        # Print out the improved alignments, excluding NULL word alignments
        if debug: sys.stdout.write("\nFinished! Final alignments are:\n")
        for (i, j) in sorted(alignment):
            if j > 0:
                sys.stdout.write("%d %d %d\n" % (k, j, i))

def main(english_alignments, foreign_alignments):
    """
    """
    parser = Parser()

    # Read the previously determined p(f|e) and p(e|f) alignments
    # for each sentence pair from the two input files
    parser.read_alignments(english_alignments, foreign_alignments)

    # Find the most likely alignments for each sentence pair
    for k in range(1, parser.n + 1):
        parser.improve_alignments(k)

def usage():
    sys.stderr.write("""
    Usage: python improve_alignments.py [english_alignments] [foreign_alignments]
        Improve the alignments between words in pairs of english sentences and
        their foreign translations based on previously determined p(f|e) and
        p(e|f) alignments.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
