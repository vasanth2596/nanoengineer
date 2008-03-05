# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
WholeChain.py - a complete chain or ring of PAM atoms, made of one or more
smaller chains (or 1 smaller ring), with refs to markers and a strand or segment

@author: Bruce
@version: $Id$
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
"""

from dna.model.dna_model_constants import LADDER_END0
from dna.model.dna_model_constants import LADDER_END1

from dna.model.DnaMarker import DnaMarker # for isinstance
from dna.model.DnaMarker import DnaSegmentMarker # constructor
from dna.model.DnaMarker import DnaStrandMarker # constructor

from debug import print_compact_traceback

class WholeChain(object):
    """
    A WholeChain knows a sequence of 1 or more smaller chains
    (of DNA PAM atoms) which are linked into a single longer chain or ring
    (or which were so linked when it was constructed).
    (If it's not a ring, then it must be a maximal chain,
    i.e. not able to be extended with more atoms at the ends,
    at the time it's constructed.)

    It is immutable once constructed, as are its smaller chains.
    Modifications to the underlying chaining from which it and its
    smaller chains are derived result in its becoming invalid
    (in various ways needed by different users of it)
    and (for some of those users) replaced by one or more newly
    constructed wholechains.

    Its jobs and role in the DNA Data Model include:

    - Understand base indexing for any whole segment or strand.

    - Be able to find (and/or keep track of) all the DnaMarkers
    along its atoms.

    - Help a DnaMarker scan its atoms to decide where to move to,
    and help it actually move.

    - Decide which marker should determine strand or segment identity
    and base indexing scheme for the atoms in this wholechain
    (if it's valid). Markers might contain user-settable attributes
    (or inherit those from their owning strand or segment) to know
    how to do this, e.g. a higher or lower priority in controlling
    base indexing, policies for which direction to move in and how
    to adjust base index when moving, how to move when new bases
    are inserted (detectable if these go between the two marker
    atoms), etc. [### todo: say some of that on DnaMarker docstring]

    Specialized kinds of markers might serve as, for example,
    startpoints or endpoints of sequence constraints, or good places
    for a base index discontinuity in a ring (if the index origin
    should not be used).

    Invariants, and how it maintains them:

    - At any given time, just after any dna updater run, the valid WholeChains
    are in 1-1 correspondence with the set of DnaSegment and DnaStrand objects,
    via their controlling markers.

    - Just after any dna updater run, each WholeChain knows about the DnaMarkers
    on its atoms, of which there are one or more, with exactly one being a 
    "controlling marker", which determines the identity of the
    DnaSegment and DnaStrand object which own the wholechain's atoms,
    and determines the base indexing scheme they use (origin and direction).
    
    - When things change (i.e. when user operations make wholechains invalid),
    and the dna updater runs again (always before the next undo checkpoint
    takes its snapshot of the model state), the dna updater
    (and methods in the markers and chains) decide how to maintain this
    association (wholechain -> controlling marker -> owning strand or segment)
    based on how the controlling marker moves and whether it stays / stops being
    / becomes controlling. (The wholechain chooses
    or makes a new controlling marker as needed for this.)

    - To do this, the wholechain uses the now-invalid wholechains to help it
    figure out when and how to modify existing DnaSegment or DnaStrand objects,
    and/or delete them or make new ones. (It does this mainly by moving
    DnaMarkers whose atoms got deleted to new locations (of non-deleted atoms)
    along their old wholechains, and then having new wholechains decide which
    markers should determine their strand's or segment's identity, by being
    the wholechain's one "controlling marker".)

    State:
    
    - A WholeChain contains no state for undo/copy/save; that's in the associated
    DnaSegment and DnaStrand objects and their DnaMarkers. (The set of DnaMarkers
    belonging to a DnaSegment and DnaStrand object is the same as the set of
    all the valid markers along its wholechain's atoms.)
    """

    # default values of subclass-specific constants
    _DnaMarker_class = None # class of DnaMarker to make
    
    # default values of instance variables
    _strand_or_segment = None
    _controlling_marker = None
    _num_bases = -1 # unknown, to start with (used in __repr__)
    _all_markers = () # (used in __repr__, could be needed before __init__ done)
    
    def __init__(self, dict_of_rails): # fyi: called by update_PAM_chunks
        """
        Construct self, own our chunks (and therefore our atoms).

        @note: this does not choose or make a marker or own our markers.
        For that see own_markers.
        
        @param dict_of_rails: maps id(rail) -> rail for all rails in wholechain
        """
        assert dict_of_rails, "a WholeChain can't be empty"
##            # needed for self._arbitrary_chunk
        self._dict_of_rails = dict_of_rails

##        chunk = None # for self._arbitrary_chunk; modified during loop
        markers = {} # collects markers from all our atoms during loop
        num_bases = 0
        end0_baseatoms = self._end0_baseatoms = {} # end0 atom key -> rail (aka chain)
        end1_baseatoms = self._end1_baseatoms = {}
        for rail in dict_of_rails.itervalues():
            baseatoms = rail.baseatoms
            num_bases += len(baseatoms)
            end0_baseatoms[baseatoms[0].key] = rail
            end1_baseatoms[baseatoms[-1].key] = rail
            chunk = baseatoms[0].molecule
            chunk.set_wholechain(self)
            for atom in rail.baseatoms:
                for jig in atom.jigs: ### ASSUMES markers are already moved and valid again (on correct live atoms) @@@
                    if isinstance(jig, DnaMarker):
                        marker = jig
                        assert not marker.killed(), "marker %r is killed" % ( marker, )
                            # might fail if they're not yet all in the model @@@
                        # cache the set of these on the rail? might matter when lots of old rails.
                        # does it matter which of its atoms we are? Not if we remove duplicates...
                        markers[id(marker)] = marker
            continue

        self._num_bases = num_bases # used only for debug (eg repr) so far, but later will help with base indexing
        
##        self._arbitrary_chunk = chunk
##        assert self._arbitrary_chunk

        self._all_markers = markers.values()
        
        return # from __init__

    def destroy(self): # 080120 7pm untested
        # note: can be called from chunk._undo_update from one of our chunks;
        # try to make it ok to call this multiple times
        for marker in self._all_markers:
            marker.forget_wholechain(self)
        self._all_markers = ()
        self._controlling_marker = None
        self._strand_or_segment = None # review: need to tell it to forget us, too? @@@
        for chain in self.chains():
            chunk = chain.baseatoms[0].molecule
##            chain.destroy() # IMPLEM @@@@ [also, goodness is partly a guess]
            if hasattr(chunk, 'forget_wholechain'): # KLUGE
                chunk.forget_wholechain(self)
            continue
        self._dict_of_rails = {}
        return
    
    def chains(self):
        """
        Return our chains, IN ARBITRARY ORDER (that might be revised)
        """
        return self._dict_of_rails.values()

    def end_chains(self): # bruce 080212
        """
        Return a list of those of our chains which have ends.
        (asserted to be length 0 or 1 or 2; length 1 is possible
        if we are a 1-chain ring.)
        """
        res = [chain for chain in self.chains() if chain.at_wholechain_end()]
        assert len(res) <= 2
        return res

    def end_baseatoms(self):
        """
        Return a list of our end_baseatoms, based on chain.neighbor_baseatoms
        for each of our chains (set by dna updater, not always valid during it).

        @note: result is asserted length 0 or 2; will be 0 if we are a ring
        or 2 if we are a chain.

        @note: Intended for use by user ops between dna updater runs.
        """
        res = []
        for chain in self.end_chains():
            res.extend(chain.wholechain_end_baseatoms())
        assert len(res) in (0,2), "impossible set of %r.end_baseatoms(): %r" % \
               (self, res)
        return res
        
    def __repr__(self):
        classname = self.__class__.__name__.split('.')[-1]
        res = "<%s (%d bases, %d markers) at %#x>" % \
              (classname, self._num_bases, len(self._all_markers), id(self))
        return res
    
    def all_markers(self):
        """
        Assuming we still own all our atoms (not checked),
        return all the DnaMarkers on them.
        """
        return self._all_markers

    def own_markers(self):
        """
        Choose or make one of your markers to be controlling,
        then tell them all that you own them and whether
        they're controlling (which might kill some of them).
        (But don't move them in the model tree, not even the newly made ones.)
        
        Also cache whatever base-indexing info is needed
        (in self, our rails/chains/chunks, and/or their atoms).
        [As of 080116 this part is not yet needed or done.]
        """
        self._controlling_marker = self._choose_or_make_controlling_marker()
        for marker in self._all_markers[:]:
##            print "debug loop: %r.own_marker %r" % (self, marker)
            controllingQ = (marker is self._controlling_marker)
            ## assert not marker.killed(), \
            # [precaution 080222 - change assert to debug print & bug mitigation:]
            if marker.killed():
                print "\n***BUG: " \
                   "marker %r (our controlling = %r) is killed" % \
                   ( marker, controllingQ )
                # this might fail if they're not yet all in the model,
                # but we put them there when we make them, and we don't kill them when they
                # lose atoms, so they ought to be there @@@
                # (it should not fail from them being killed between __init__ and now
                #  and unable to tell us, since nothing happens in caller to kill them)
                self._f_marker_killed(marker) #k guess 080222
                continue
            marker.set_wholechain(self, controlling = controllingQ)
                # own it; tell it whether controlling (some might die then,
                # and if so they'll call self._f_marker_killed
                # which removes them from self._all_markers)
            continue
        for marker in self._all_markers[:]:
            # [precaution 080222 - change assert to debug print & bug mitigation:]
            ## assert not marker.killed(), \
            if marker.killed():
                print "\n***BUG: " \
                    "marker %r died without telling %r" % (marker, self)
                self._f_marker_killed(marker)
            continue
        
        # todo: use controlling marker to work out base indexing per rail...
        
        return

    def _f_marker_killed(self, marker):
        """
        [friend method for DnaMarker]
        One of our markers is being killed
        (and calls this to advise us of that).
        [Also called by self if we realize that failed to happen.]
        """
        try:
            self._all_markers.remove(marker)
        except:
            msg = "bug: can't remove %r from %r._all_markers: " % (marker, self)
            print_compact_traceback( msg)
            pass
        return

    # ==
    
    def find_strand_or_segment(self):
        """
        Return our associated DnaStrandOrSegment, which is required
        to be already defined in self.
        """
        assert self._strand_or_segment
        return self._strand_or_segment

    def find_or_make_strand_or_segment(self):
        """
        Return our associated DnaStrandOrSegment. If we don't yet know it
        or don't have one, ask our controlling marker (which we must have
        before now) to find or make it.
        """
        if self._strand_or_segment:
            return self._strand_or_segment
        assert self._controlling_marker, "%r should have called _choose_or_make_controlling_marker before now" % self
        strand_or_segment = self._controlling_marker._f_get_owning_strand_or_segment(make = True)
        assert strand_or_segment
        self._strand_or_segment = strand_or_segment
        return strand_or_segment

    # == ### review below

    def _choose_or_make_controlling_marker(self):
        """
        [private]
        Choose one of our markers to control this chain, or make a new one
        (at a good position on one of our atoms) to do that.
        Return it, but don't save it anywhere (caller must do that).
        """
        marker = self._choose_controlling_marker()
        if not marker:
            marker = self._make_new_controlling_marker()
        assert marker
        return marker
    
    def _choose_controlling_marker(self):
        """
        [private]
        Look at the existing markers on our atoms which are able to be
        controlling markers.
        If there are none, return None.
        Otherwise choose one of them to be our controlling marker,
        and return it (don't save it anywhere, or tell any markers
        whether they are controlling now; caller must do those things
        if/when desired; fyi, as of 080116 own_markers does this).

        If one or more are already controlling, it will be one of them. [### REVIEW -- not sure this point is right]
        If more than one are controlling, we have rules to let them compete.
        If none is, ditto.
        """
        all_markers = self.all_markers() # valid anytime after __init__
        candidates = [marker
                      for marker in all_markers
                      if marker.wants_to_be_controlling()]
        if not candidates:
            return None
        # choose one of the candidates
        list_of_preferred_markers_this_time = [] ### stub - in real life let external code add markers to this list, pop them all here
        items = []
        for marker in candidates:
            order_info = (marker in list_of_preferred_markers_this_time, # note: False < True in Python
                          marker.control_priority,
                          marker.get_oldness(), # assume oldness is unique -- inverse of something allocated by a counter
                          )
            items.append( (order_info, marker) )
        items.sort()
        return items[-1][1]

    def _make_new_controlling_marker(self):
        """
        [private]
        self has no marker which wants_to_be_controlling().
        Make one (on some good choice of atom on self)
        (and in the same group in the model tree as that atom)
        and return it. (Don't store it as our controlling marker,
        or tell it it's controlling -- caller must do that if desired.
        But *do* add it to our list of all markers on our atoms.)

        @note: we always make one, even if this is a 1-atom wholechain
        (which means (for now) that it's not possible to make a good
         or fully correct one).
        We do that because the callers really need every wholechain to have one.
        """
        # improvements, 080222: should pick end atom with lowest .key, but to be easier and work for rings,
        # might pick end atom of any chain with lowest key (over all chains). Also this is best for segments
        # and also ok for strands but maybe not best for strands (who should look at Ax atoms in same basepairs,
        # but note, these can be same for different strand atoms!).

        end_atoms = self.end_baseatoms() # should find 2 atoms unless we're a ring
        if not end_atoms:
            # we're a ring - just consider all end atoms of all our chains
            # (don't bother not including some twice for length-1 chains,
            #  no need in following code)
            end_atoms = []
            for chain in self.chains():
                end_atoms.append( chain.baseatoms[0] )
                end_atoms.append( chain.baseatoms[-1] )
            pass
        assert end_atoms

        candidates = [(atom.key, atom) for atom in end_atoms]
            # todo: for strands, first sort by attached Ax key?
            # todo: include info to help find next_atom?
        candidates.sort() # lowest key means first-made basepair by Dna Generator
        atom = candidates[0][1]
        
        # now pick the best next_atom

        chain, index = self._find_end_atom_chain_and_index( atom)
            # Q. is index for end1 positive or -1?
            # A. positive (or 0 for length-1 chain), but following code doesn't care.
            # Q. does best next_atom come from same chain if possible?
            # A. (guess yes, doing that for now)
        direction_into_chain = index and -1 or 1
        
        if len(chain.baseatoms) > 1:
            next_atom = chain.baseatoms[index + direction_into_chain]
        elif chain.neighbor_baseatoms[LADDER_END1]: # ignore index and direction_into_chain
            next_atom = chain.neighbor_baseatoms[LADDER_END1]
        elif chain.neighbor_baseatoms[LADDER_END0]:
            next_atom = chain.neighbor_baseatoms[LADDER_END0] # reverse direction!
            atom, next_atom = next_atom, atom
        else:
            # a 1-atom wholechain, hmm ...
            # DnaMarker support for this added 080216, not fully tested
            # (note that a 1-atom wholechain *ring* is not possible,
            #  but if it was it'd be handled by the above if/else cases)
            next_atom = atom

        # now make the marker on those atoms
        # (todo: in future, we might give it some user settings too)
        assert atom.molecule, "%r has no .molecule" % atom
        
        assy = atom.molecule.assy
        
        assert assy
        assert atom.molecule.part, "%r has no .part; .molecule is %r" % (atom, atom.molecule)
        assert next_atom.molecule, "%r has no .molecule" % next_atom
        assert next_atom.molecule.part, "%r has no .part; .molecule is %r" % (next_atom, next_atom.molecule)
        assert atom.molecule.part is next_atom.molecule.part, \
               "%r in part %r, %r in part %r, should be same" % \
               (atom, atom.molecule.part, next_atom, next_atom.molecule.part)
        
        marker_class = self._DnaMarker_class # subclass-specific constant
        marker = marker_class(assy, [atom, next_atom]) # doesn't give it a wholechain yet

        # give it a temporary home in the model (so it doesn't seem killed) --
        # in fact, it matters where we put it, since later code assumes it
        # *might* already be inside the right DnaStrandOrSegment (and checks
        # this). So we put it in the same group as the marked atom.

        part = atom.molecule.part
        part.place_new_jig(marker)
            # (overkill in runtime, but should be correct, since both marker's
            #  atoms should be in the same group)
        
        # and remember it's on our atoms
        self._all_markers.append(marker)
        
        return marker

    def _find_end_atom_chain_and_index(self, atom):
        """
        Assume atom is an end_baseatom of one of our chains (aka rails).
        (If not true, raise KeyError.)
        Find that chain and its index in it, and return them as (chain, index).
        The index is nonnegative, meaning that we use 0 for
        either end of a length-1 chain (there is no distinction
        between the ends in that case).
        """
        try:
            chain = self._end0_baseatoms[atom.key]
            return chain, 0
        except KeyError:
            chain = self._end1_baseatoms[atom.key]
                # raise KeyError if atom is not an end_atom of any of our chains
            return chain, len(chain) - 1
        pass
        
    # todo: methods related to base indexing

    # todo: methods to help move markers, derived from or related to
    # _f_move_to_live_atom_step1 and _step2 in dna_updater_chunks.py
    
    pass # end of class WholeChain

# ==

class Axis_WholeChain(WholeChain):
    _DnaMarker_class = DnaSegmentMarker
    """
    A WholeChain for axis atoms.
    """
    pass

class Strand_WholeChain(WholeChain):
    _DnaMarker_class = DnaStrandMarker
    """
    A WholeChain for strand atoms.
    """
    pass

# ==

def new_Group_around_Node(node, group_class): #e refile, might use in other ways too [not used now, but might be correct]
    node.part.ensure_toplevel_group() # might not be needed
    name = "(internal Group)" # stub
    assy = node.assy
    dad = None #k legal?? arg needed?
    group = group_class(name, assy, dad) # same args as for Group.__init__(self, name, assy, dad) [review: reorder those anytime soon??]
    node.addsibling(group)
    group.addchild(node)
    return group

    
# end