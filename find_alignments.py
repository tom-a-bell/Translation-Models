#! /usr/bin/python

__author__="Tom Bell <tom.bell.code@gmail.com>"
__date__ ="$Apr 28, 2013"

import sys
import codecs

"""
Find alignments for the english and foreign words in parallel translations
using IBM translation model 1 or 2 based on previously determined t(f|e)
and q(j|i,l,m) parameter estimates from a parallel training corpus.
"""

# Debug output flag
debug = False

# Special English word that can be aligned to any foreign word in the corpus
NULL = "NULL"

class Parser:
    def __init__(self, model=1):
        self.model = model
        self.t = {}
        self.q = {}

    def read_parameters(self, parameter_file):
        """
        Read the previously determined t(f|e) and q(j|i,l,m)
        values from the input files.
        """
        if debug: sys.stdout.write("Reading parameter estimates...\n")

        file = codecs.open(parameter_file+'.tfe', encoding='utf-8', mode='r')
        file.seek(0)
        for line in file:
            token = line.split()
            e = token[0]
            f = token[1]
            t = float(token[2])
            self.t.setdefault(e, dict())
            self.t[e][f] = t
        file.close()

        if self.model == 1: return

        file = codecs.open(parameter_file+'.qji', encoding='utf-8', mode='r')
        file.seek(0)
        for line in file:
            token = line.split()
            i = int(token[0])
            l = int(token[1])
            m = int(token[2])
            j = int(token[3])
            q = float(token[4])
            self.q.setdefault((i, l, m), dict())
            self.q[(i, l, m)][j] = q
        file.close()

    def find_alignments(self, k, e, f):
        """
        Find the most likely word alignment based
        on the t(f|e) and q(j|i,l,m) values.
        """

        a = []
        l = len(e)
        m = len(f)
        for i in range(1, m + 1):
            if debug:
                sys.stdout.write("\nFinding alignment for: f_"+str(i)+" = '"+f[i-1]+"'\n")
            max = self.q[(i, l, m)][0]*self.t[NULL][f[i-1]]
            argmax = 0
            for j in range(1, l + 1):
                if self.q[(i, l, m)][j]*self.t[e[j-1]][f[i-1]] > max:
                    max = self.q[(i, l, m)][j]*self.t[e[j-1]][f[i-1]]
                    argmax = j
            a.append(argmax)
            if debug:
                sys.stdout.write("Most likely alignment: a_i = "+str(a[i-1])+" ('"+e[a[i-1]-1]+"')\n")

        # Print out the alignments, excluding NULL word alignments
        for i in range(m):
            if a[i] > 0:
                sys.stdout.write("%d %d %d\n" % (k + 1, a[i], i + 1))

def main(parameter_file, english_file, foreign_file):
    """
    """
    parser = Parser(model=2)

    # Read the previously determined t(f|e) and q(j|i,l,m) parameter values
    parser.read_parameters(parameter_file)

    e = [] ; f = []
    file = codecs.open(english_file, encoding='utf-8', mode='r')
    for line in file:
        sentence = line.split()
        e.append(sentence)
    file.close()
    file = codecs.open(foreign_file, encoding='utf-8', mode='r')
    for line in file:
        sentence = line.split()
        f.append(sentence)
    file.close()

    # Find the most likely alignments for each sentence pair
    for k in range(len(e)):
        parser.find_alignments(k, e[k], f[k])

def usage():
    sys.stderr.write("""
    Usage: python find_alignments.py [parameter_file] [english_file] [foreign_file]
        Find the most likely alignment between the words in an english sentence and
        the parallel foreign translation based on previously determined t(f|e) [and
        q(j|i,l,m) if using IBM model 2] parameters.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
