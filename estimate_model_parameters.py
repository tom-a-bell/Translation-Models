#! /usr/bin/python

__author__="Tom Bell <tom.bell.code@gmail.com>"
__date__ ="$Apr 28, 2013"

import sys
import codecs

"""
Estimate the parameters for IBM translation model 1 or 2 using the iterative
EM algorithm based on a parallel corpus of english and foreign sentences.
"""

# Debug output flag
debug = False

# Special English word that can be aligned to any foreign word in the corpus
NULL = "NULL"

class EM:
    def __init__(self, model=1):
        self.model = model
        self.t = {} # t(f|e) parameters
        self.q = {} # q(j|i,l,m) parameters
        self.e = [] # Corpus of english sentences
        self.f = [] # Corpus of foreign sentences
        self.n = 0  # Total number of sentence pairs

    def read_corpus(self, english_file, foreign_file):
        """
        Construct the lists of parallel english and foreign sentences and
        add the entries to t(f|e) for each english word and the foreign
        words that appear with it in the parallel translation.
        """
        sys.stdout.write("Reading both parallel corpus files...\n")

        # Create the list of english sentences
        english_file.seek(0)
        for line in english_file:
            sentence = line.split()
            self.e.append(sentence)
        english_file.close()

        # Create the list of parallel foreign translations
        foreign_file.seek(0)
        for line in foreign_file:
            sentence = line.split()
            self.f.append(sentence)
        foreign_file.close()

        # Check there are equal numbers of english and foreign sentences
        self.n = len(self.e)
        if len(self.f) != self.n:
            sys.stderr.write("""ERROR: English and foreign corpus files
                                contain different number of sentences.\n""")
            sys.exit(1)

    def write_parameters(self, output_file):
        """
        Write the estimated parameter values to the specified output file.
        """
        sys.stdout.write("Writing t(f|e) values to output file...\n")

        file = codecs.open(output_file+'.tfe', encoding='utf-8', mode='w')
        for e in self.t:
            for f in self.t[e]:
                file.write("%s %s %E\n" % (e, f, self.t[e][f]))
        file.close()

        if self.model == 1: return

        sys.stdout.write("Writing q(j|i,l,m) values to output file...\n")

        file = codecs.open(output_file+'.qji', encoding='utf-8', mode='w')
        for (i, l, m) in self.q:
            for j in self.q[(i, l, m)]:
                file.write("%d %d %d %d %E\n" % (i, l, m, j, self.q[(i, l, m)][j]))
        file.close()

    def create_parameters(self):
        """
        Create the t(f|e) and q(j|i,l,m) parameter entries.
        """
        sys.stdout.write("Creating sparse set of t(f|e) entries...\n")

        # Create the t(f|e) entries as sets of all
        # possible foreign words per english word
        self.t.setdefault(NULL, set())
        for n in range(self.n):
            words = set(self.f[n])
            for e in self.e[n]:
                self.t.setdefault(e, set())
                self.t[e].update(words)
            self.t[NULL].update(words)

        if self.model == 1: return

        sys.stdout.write("Creating sparse set of q(j|i,l,m) entries...\n")

        # Create the q(j|i,l,m) entries as sets of all
        # possible foreign word positions per sentence
        for n in range(self.n):
            l = len(self.e[n])
            m = len(self.f[n])
            positions = set(range(l + 1))
            for i in range(1, m + 1):
                self.q.setdefault((i, l, m), set())
                self.q[(i, l, m)].update(positions)

    def initialize(self):
        """
        Set initial guess values for t(f|e) and q(j|i,l,m)
        based on words counts and english sentence lengths.
        """
        sys.stdout.write("Setting initial guesses for t(f|e)...\n")

        for e in self.t:
            words = self.t[e]
            count = len(words)
            values = dict([(f, 1/float(count)) for f in words])
            self.t[e] = values

        if self.model == 1: return

        sys.stdout.write("Setting initial guesses for q(j|i,l,m)...\n")

        for (i, l, m) in self.q:
            positions = self.q[(i, l, m)]
            count = len(positions)
            values = dict([(j, 1/float(count)) for j in positions])
            self.q[(i, l, m)] = values

    def iterate(self, num_iterations):
        """
        Estimate the model parameters for the specified
        IBM model by running the iterative EM algorithm.
        """
        sys.stdout.write("Iteratively updating parameter values...\n")

        if self.model == 1:
            for n in range(num_iterations):
                sys.stdout.write("\nStarting EM algorithm (model 1) iteration %d of %d...\n" % (n+1, num_iterations))

                # Reset the expected counts
                count = {}

                # Loop over each sentence pair
                sys.stdout.write(" -> Calculating delta values for each sentence\n")
                for k in range(self.n):
                    l = len(self.e[k])

                    # Calculate the delta values
                    delta = {}
                    for f in self.f[k]:

                        sum = self.t[NULL][f]
                        for e in self.e[k]:
                            sum += self.t[e][f]

                        delta[(NULL, f)] = self.t[NULL][f] / sum
                        for e in self.e[k]:
                            delta[(e, f)] = self.t[e][f] / sum

                    # Update the expected counts
                    for e in [NULL] + self.e[k]:
                        for f in self.f[k]:
                            count.setdefault((e, f), 0)
                            count.setdefault((e), 0)
                            count[(e, f)] += delta[(e, f)]
                            count[(e)] += delta[(e, f)]

                # Revise the estimates for the t(f|e) values
                sys.stdout.write(" -> Revising estimates for all t(f|e) values\n")
                for e in self.t:
                    words = self.t[e]
                    for f in words:
                        self.t[e][f] = count[(e, f)] / count[(e)]

        else:
            for n in range(num_iterations):
                sys.stdout.write("\nStarting EM algorithm (model 2) iteration %d of %d...\n" % (n+1, num_iterations))

                # Reset the expected counts
                count = {}

                # Loop over each sentence pair
                sys.stdout.write(" -> Calculating delta values for each sentence\n")
                for k in range(self.n):
                    l = len(self.e[k])
                    m = len(self.f[k])

                    # Calculate the delta values
                    delta = {}
                    for i in range(1, m + 1):
                        f = self.f[k][i-1]

                        sum = self.q[(i, l, m)][0]*self.t[NULL][f]
                        for j in range(1, l + 1):
                            e = self.e[k][j-1]
                            sum += self.q[(i, l, m)][j]*self.t[e][f]

                        delta[(NULL, f)] = self.q[(i, l, m)][0]*self.t[NULL][f] / sum
                        for j in range(1, l + 1):
                            e = self.e[k][j-1]
                            delta[(e, f)] = self.q[(i, l, m)][j]*self.t[e][f] / sum

                    # Update the expected counts
                    for e in [NULL] + self.e[k]:
                        for f in self.f[k]:
                            count.setdefault((e, f), 0)
                            count.setdefault((e), 0)
                            count[(e, f)] += delta[(e, f)]
                            count[(e)] += delta[(e, f)]

                    for j in range(l + 1):
                        if j == 0: e = NULL
                        else:      e = self.e[k][j-1]
                        for i in range(1, m + 1):
                            f = self.f[k][i-1]
                            count.setdefault((i, l, m, j), 0)
                            count.setdefault((i, l, m), 0)
                            count[(i, l, m, j)] += delta[(e, f)]
                            count[(i, l, m)] += delta[(e, f)]

                # Revise the estimates for the t(f|e) and q(j|i,l,m) values
                sys.stdout.write(" -> Revising estimates for all t(f|e) values\n")
                for e in self.t:
                    words = self.t[e]
                    for f in words:
                        self.t[e][f] = count[(e, f)] / count[(e)]

                sys.stdout.write(" -> Revising estimates for all q(j|i,l,m) values\n")
                for (i, l, m) in self.q:
                    positions = self.q[(i, l, m)]
                    for j in positions:
                        self.q[(i, l, m)][j] = count[(i, l, m, j)] / count[(i, l, m)]

        sys.stdout.write("\nFinished all iterations!\n")

    def test(self, e, f):
        sys.stdout.write("t('%s'|'%s') = %e\n" % (f, e, self.t[e][f]))


def main(english_file, foreign_file):
    """
    Create an instance of the EM algorithm class, open the parallel corpus files
    read all the sentences contained within them and estimate parameter values
    for t(f|e) and a_ij by iterating N times.
    """
    estimator = EM(model=2)

    file1 = codecs.open(english_file, encoding='utf-8', mode='r')
    file2 = codecs.open(foreign_file, encoding='utf-8', mode='r')

    # Read the corpus files and construct the english and foreign sentence lists
    estimator.read_corpus(file1, file2)

    # Create the t(f|e) and q(j|i,l,m) parameter entries
    estimator.create_parameters()

    # Set the initial guess values for t(f|e) and q(j|i,l,m)
    estimator.initialize()

    # Estimate values for t(f|e) by performing 5 iterations of the EM algorithm
    estimator.model = 1
    estimator.iterate(5)

    # Estimate values for t(f|e) and q(j|i,l,m) by performing another 5 iterations
    estimator.model = 2
    estimator.iterate(5)

    # Write the estimated values for t(f|e) and q(j|i,l,m) to file
    estimator.write_parameters(english_file)

def usage():
    sys.stderr.write("""
    Usage: python estimate_model_parameters.py [english_file] [foreign_file]
        Estimate the parameters for IBM translation model 1 or 2 using the
        iterative EM algorithm based on a parallel corpus; save the values
        to output file(s).\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
