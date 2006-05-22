# Copyright (c) 2006 Nanorex, Inc.  All rights reserved.
"""
DnaGenerator.py

$Id$

http://en.wikipedia.org/wiki/DNA
http://en.wikipedia.org/wiki/Image:Dna_pairing_aa.gif
"""

__author__ = "Will"

from DnaGeneratorDialog import DnaGeneratorDialog
from math import atan2, sin, cos, pi
import assembly, chem, bonds, Utility
from chem import molecule, Atom
import env
from HistoryWidget import redmsg, greenmsg
from qt import Qt, QApplication, QCursor, QDialog, QDoubleValidator, QValidator
from VQT import A, V, dot, vlen
from bonds import inferBonds
from files_mmp import insertmmp
import re

def rotateTranslate(v, theta, z):
    c, s = cos(theta), sin(theta)
    x = c * v[0] + s * v[1]
    y = -s * v[0] + c * v[1]
    return V(x, y, v[2] + z)

atompat = re.compile("atom (\d+) \((\d+)\) \((-?\d+), (-?\d+), (-?\d+)\)")

def odd(n):
    return (n & 1) != 0

class Dna:
    """This base class may want to provide some provision for the
    fact that we have a two-base periodicity in Z DNA. Or should that
    all be handled there?
    """
    def insertmmp(self, mol, basefile, tfm):
        lst = [ ]
        for line in open(basefile).readlines():
            m = atompat.match(line)
            if m:
                elem = {
                    0: 'X',
                    1: 'H',
                    6: 'C',
                    7: 'N',
                    8: 'O',
                    15: 'P',
                    }[int(m.group(2))]
                xyz = A(map(float, [m.group(3),m.group(4),m.group(5)]))/1000.0
                lst.append(Atom(elem, tfm(xyz), mol))
        return lst

    def make(self, mol, sequence, strandA, strandB):
        sequence = str(sequence).upper()
        for ch in sequence:
            if ch not in 'GACT':
                raise Exception('Unknown DNA base (not G, A, C, or T): ' + ch)

        if strandA:
            theta = 0.0
            z = 0.5 * self.BASE_SPACING * (len(sequence) - 1)
            for i in range(len(sequence)):
                basefile, zoffset, thetaOffset = \
                          self.strandAinfo(sequence, i)
                def tfm(v, theta=theta+thetaOffset, z1=z+zoffset):
                    return rotateTranslate(v, theta, z1)
                self.insertmmp(mol, basefile, tfm)
                theta -= self.TWIST_PER_BASE
                z -= self.BASE_SPACING

        if strandB:
            theta = 0.0
            z = 0.5 * self.BASE_SPACING * (len(sequence) - 1)
            for i in range(len(sequence)):
                # The 3'-to-5' direction is reversed for strand B.
                basefile, zoffset, thetaOffset = \
                          self.strandBinfo(sequence, i)
                def tfm(v, theta=theta+thetaOffset, z1=z+zoffset):
                    # Flip theta, flip z
                    # Cheesy hack: flip theta by reversing the sign of y,
                    # since theta = atan2(y,x)
                    return rotateTranslate(V(v[0], -v[1], -v[2]), theta, z1)
                self.insertmmp(mol, basefile, tfm)
                theta -= self.TWIST_PER_BASE
                z -= self.BASE_SPACING


class A_Dna(Dna):
    TWIST_PER_BASE = 0  # WRONG
    BASE_SPACING = 0    # WRONG
    def strandAinfo(self, sequence, i):
        raise Exception("A-DNA is not yet implemented -- please try B- or Z-DNA");
    def strandBinfo(self, sequence, i):
        raise Exception("A-DNA is not yet implemented -- please try B- or Z-DNA");

class B_Dna(Dna):
    TWIST_PER_BASE = -36 * pi / 180   # degrees
    BASE_SPACING = 3.391              # angstroms
    def strandAinfo(self, sequence, i):
        basename = {
            'C': 'cytosine',
            'G': 'guanine',
            'A': 'adenine',
            'T': 'thymine',
            }[sequence[i]]
        zoffset = 0.0
        thetaOffset = 0.0
        basefile = 'experimental/bdna-bases/%s.mmp' % basename
        return (basefile, zoffset, thetaOffset)

    def strandBinfo(self, sequence, i):
        basename = {
            'G': 'cytosine',
            'C': 'guanine',
            'T': 'adenine',
            'A': 'thymine',
            }[sequence[i]]
        zoffset = 0.0
        # The thetaOffset requires some empirical and apparently non-sensical
        # tweaking to get right. The reason for this is the cheesy hack I did
        # for the theta flip on the B strand. The tidy approach would be to
        # find a center theta for each base, and flip theta around that center.
        # I didn't do this primarily because I wasn't sure the bonds would match
        # up. And this isn't so ugly, we're just tweaking one number.
        thetaOffset = 210 * (pi / 180)
        basefile = 'experimental/bdna-bases/%s.mmp' % basename
        return (basefile, zoffset, thetaOffset)

class Z_Dna(Dna):
    TWIST_PER_BASE = pi / 6     # in radians
    BASE_SPACING = 3.715        # in angstroms

    # Z-DNA has a periodicity of two bases. The odd-numbered basis
    # have one orientation, the even-numbered bases have another.
    # Take care of the directory name, and the alternation of inner and
    # outer bases, which won't occur in A and B DNA.
    def strandAinfo(self, sequence, i):
        basename = {
            'C': 'cytosine',
            'G': 'guanine',
            'A': 'adenine',
            'T': 'thymine',
            }[sequence[i]]
        if odd(i):
            suffix = 'outer'
            zoffset = 2.045
        else:
            suffix = 'inner'
            zoffset = 0.0
        thetaOffset = 0.0
        basefile = 'experimental/zdna-bases/%s-%s.mmp' % (basename, suffix)
        return (basefile, zoffset, thetaOffset)

    def strandBinfo(self, sequence, i):
        basename = {
            'G': 'cytosine',
            'C': 'guanine',
            'T': 'adenine',
            'A': 'thymine',
            }[sequence[i]]
        if odd(i):
            suffix = 'inner'
            zoffset = -0.055
        else:
            suffix = 'outer'
            zoffset = -2.1
        thetaOffset = 0.5 * pi
        basefile = 'experimental/zdna-bases/%s-%s.mmp' % (basename, suffix)
        return (basefile, zoffset, thetaOffset)


#################################

cmd = greenmsg("Insert Dna: ")

class DnaGenerator(DnaGeneratorDialog):

    # pass window arg to constructor rather than use a global, wware 051103
    def __init__(self, win):
        DnaGeneratorDialog.__init__(self, win) # win is parent.  Fixes bug 1089.  Mark 051119.
        self.win = win
        self.dnaType = 'B'
        
        # Default DNA parameters
        #self.dnaTypeButtonGroup.setCheckable(True)
        self.bDnaButton.setChecked(True)
        self.strandAchkbox.setChecked(True)
        self.strandBchkbox.setChecked(True)
        self.seq_linedit.setText('GATTACA')

    def dnaTypeClicked(self, a0):
        if a0 == 2: self.dnaType = 'A'
        elif a0 == 1: self.dnaType = 'B'
        elif a0 == 0: self.dnaType = 'Z'

    def accept(self):
        'Slot for the OK button'
        strandA = self.strandAchkbox.isChecked()
        strandB = self.strandBchkbox.isChecked()
        if strandA or strandB:
            env.history.message(cmd + "Creating DNA. This may take a moment...")
            QApplication.setOverrideCursor( QCursor(Qt.WaitCursor) )
            try:
                mol = molecule(self.win.assy, chem.gensym("DNA-"))
                if self.dnaType == 'A':
                    dna = A_Dna()
                elif self.dnaType == 'B':
                    dna = B_Dna()
                elif self.dnaType == 'Z':
                    dna = Z_Dna()
                dna.make(mol, self.seq_linedit.text(), strandA, strandB)
                inferBonds(mol)
                part = self.win.assy.part
                part.ensure_toplevel_group()
                part.topnode.addchild(mol)
                self.win.mt.mt_update()
                env.history.message(cmd + "Done.")
            except Exception, e:
                env.history.message(cmd + redmsg(" - ".join(map(str, e.args))))
            QApplication.restoreOverrideCursor() # Restore the cursor
        QDialog.accept(self)

    def reject(self):
        'Slot for the Cancel button'
        # End the dialog without saying or doing anything.
        QDialog.accept(self)
