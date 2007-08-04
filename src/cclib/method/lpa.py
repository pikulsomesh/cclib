"""
cclib (http://cclib.sf.net) is (c) 2006, the cclib development team
and licensed under the LGPL (http://www.gnu.org/copyleft/lgpl.html).
"""

__revision__ = "$Revision$"

import random

import numpy

from population import Population


class LPA(Population):
    """The Lowdin population analysis"""
    def __init__(self, *args):

        # Call the __init__ method of the superclass.
        super(LPA, self).__init__(logname="LPA", *args)

    def __str__(self):
        """Return a string representation of the object."""
        return "LPA of" % (self.parser)

    def __repr__(self):
        """Return a representation of the object."""
        return 'LPA("%s")' % (self.parser)

    def calculate(self, indices=None, x=0.5, fupdate=0.05):
        """Perform a calculation of Lowdin population analysis.
        
        Keyword arguments:
        indices - list of lists containing atomic orbital indices of fragments
        x - overlap matrix exponent in wavefunxtion projection (x=0.5 for Lowdin)
        """

        if not self.parser.parsed:
            self.parser.parse()

        # Do we have the needed info in the parser?
        if not hasattr(self.parser,"mocoeffs"):
            self.logger.error("Missing mocoeffs")
            return False
        if not (hasattr(self.parser, "aooverlaps") \
                    or hasattr(self.parser, "fooverlaps") ):
            self.logger.error("Missing overlap matrix")
            return False
        if not hasattr(self.parser, "nbasis"):
            self.logger.error("Missing nbasis")
            return False
        if not hasattr(self.parser, "homos"):
            self.logger.error("Missing homos")
            return False

        unrestricted = (len(self.parser.mocoeffs) == 2)
        nbasis = self.parser.nbasis

        # Determine number of steps, and whether process involves beta orbitals.
        self.logger.info("Creating attribute aoresults: [array[2]]")
        alpha = len(self.parser.mocoeffs[0])
        self.aoresults = [ numpy.zeros([alpha, nbasis], "d") ]
        nstep = alpha

        if unrestricted:
            beta = len(self.parser.mocoeffs[1])
            self.aoresults.append(numpy.zeros([beta, nbasis], "d"))
            nstep += beta

        #intialize progress if available
        if self.progress:
            self.progress.initialize(nstep)

        step = 0
        for spin in range(len(self.parser.mocoeffs)):

            for i in range(len(self.parser.mocoeffs[spin])):

                if self.progress and random.random() < fupdate:
                    self.progress.update(step, "Lowdin Population Analysis")

                ci = self.parser.mocoeffs[spin][i]
                if hasattr(self.parser, "aooverlaps"):
                    S = self.parser.aooverlaps
                elif hasattr(self.parser, "fooverlaps"):
                    S = self.parser.fooverlaps

                # Get eigenvalues and matrix of eigenvectors for transformation decomposition (U).
                # Find roots of diagonal elements, and transform backwards using eigevectors.
                # We need two matrices here, one for S^x, another for S^(1-x).
                # We don't need to invert U, since S is symmetrical.
                eigenvalues, U = numpy.linalg.eig(S)
                UI = U.transpose()
                Sdiagroot1 = numpy.identity(len(S))*numpy.power(eigenvalues, x)
                Sdiagroot2 = numpy.identity(len(S))*numpy.power(eigenvalues, 1-x)
                Sroot1 = numpy.dot(U, numpy.dot(Sdiagroot1, UI))
                Sroot2 = numpy.dot(U, numpy.dot(Sdiagroot2, UI))

                temp1 = numpy.dot(ci, Sroot1)
                temp2 = numpy.dot(ci, Sroot2)
                self.aoresults[spin][i] = numpy.multiply(temp1, temp2).astype("d")

                step += 1

        if self.progress:
            self.progress.update(nstep, "Done")

        retval = super(LPA, self).partition(indices)

        if not retval:
            self.logger.error("Error in partitioning results")
            return False

        # Create array for charges.
        self.logger.info("Creating fragcharges: array[1]")
        size = len(self.fragresults[0][0])
        self.fragcharges = numpy.zeros([size], "d")

        for spin in range(len(self.fragresults)):

            for i in range(self.parser.homos[spin] + 1):

                temp = numpy.reshape(self.fragresults[spin][i], (size,))
                self.fragcharges = numpy.add(self.fragcharges, temp)

        if not unrestricted:
            self.fragcharges = numpy.multiply(self.fragcharges, 2)

        return True

if __name__ == "__main__":
    import doctest, lpa
    doctest.testmod(lpa, verbose=False)