# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
builtin_command_loaders.py -- loaders for NE1 builtin commands.

@version: $Id$
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details.

Module classification: [bruce 080209]

For now, part of Command Sequencer package, since knows
the list of hardcoded commandnames the Command Sequencer uses
to let other code invoke builtin commands, and knows which
ones should be always loaded and in what order.

Someday, after refactoring, it might belong in ne1_startup.
(Maybe it even belongs there now.)

History:

Bruce 080209 split this out of GLPane.py (where it existed
for purely historical reasons). Semantically it was part
of the Command Sequencer, and it's now split out of there
too.

TODO:

Refactor the code that uses this data (in Command Sequencer)
so its _commandTable is a separate object with which
we register the loading code herein, so it can load
some commands lazily.
"""

from commands.BuildCrystal.cookieMode import cookieMode 
from commands.Extrude.extrudeMode import extrudeMode
from commands.Paste.PasteMode import PasteMode
from commands.PartLibrary.PartLibraryMode import PartLibraryMode
from commands.PlayMovie.movieMode import movieMode
from temporary_commands.ZoomToAreaMode import ZoomToAreaMode
from temporary_commands.ZoomInOutMode import ZoomInOutMode
from temporary_commands.PanMode import PanMode
from temporary_commands.RotateMode import RotateMode
from temporary_commands.LineMode import LineMode
from dna.temporary_commands.DnaLineMode import DnaLineMode
from dna.commands.BuildDuplex.DnaDuplex_EditCommand import DnaDuplex_EditCommand
from commands.PlaneProperties.Plane_EditCommand import Plane_EditCommand
from commands.RotaryMotorProperties.RotaryMotor_EditCommand import RotaryMotor_EditCommand
from commands.LinearMotorProperties.LinearMotor_EditCommand import LinearMotor_EditCommand
from commands.BuildAtoms.BuildAtoms_Command import BuildAtoms_Command
from commands.SelectAtoms.SelectAtoms_Command import SelectAtoms_Command
from commands.SelectChunks.SelectChunks_Command import SelectChunks_Command
from dna.commands.BreakStrands.BreakStrands_Command import BreakStrands_Command
from dna.commands.BuildDna.BuildDna_EditCommand import BuildDna_EditCommand
from dna.commands.DnaSegment.DnaSegment_EditCommand import DnaSegment_EditCommand
from dna.commands.DnaStrand.DnaStrand_EditCommand import DnaStrand_EditCommand
from dna.commands.DnaDisplayStyle.DnaDisplayStyle_Command import DnaDisplayStyle_Command
from cnt.commands.BuildNanotube.BuildNanotube_EditCommand import BuildNanotube_EditCommand
from cnt.commands.InsertNanotube.InsertNanotube_EditCommand import InsertNanotube_EditCommand
from cnt.commands.NanotubeSegment.NanotubeSegment_EditCommand import NanotubeSegment_EditCommand
from commands.Move.Move_Command import Move_Command
from commands.Rotate.RotateChunks_Command import RotateChunks_Command
from commands.Translate.TranslateChunks_Command import TranslateChunks_Command
from commands.Fuse.FuseChunks_Command import FuseChunks_Command
from dna.commands.JoinStrands.JoinStrands_Command import JoinStrands_Command
from temporary_commands.RotateAboutPoint_Command import RotateAboutPoint_Command

from dna.commands.MultipleDnaSegmentResize.MultipleDnaSegmentResize_EditCommand import MultipleDnaSegmentResize_EditCommand
def preloaded_command_classes():
    """
    Return a list of command classes for the commands which are always loaded
    on startup, and should always be reinitialized (in this order)
    when new command objects are needed.

    @note: currently this includes all loadable builtin commands,
           but soon we will implement a way for some commands to be
           loaded lazily, and remove many commands from this list.
    """
    # classes for builtin commands (or unsplit modes) which were preloaded
    # by toplevel imports above, in order of desired instantiation:
    command_classes = [
        SelectChunks_Command, 
        SelectAtoms_Command,
        BuildAtoms_Command,
        Move_Command,
        cookieMode, 
        extrudeMode, 
        movieMode, 
        ZoomToAreaMode, 
        ZoomInOutMode,
        PanMode, 
        RotateMode, 
        PasteMode, 
        PartLibraryMode, 
        LineMode, 
        DnaLineMode, 
        DnaDuplex_EditCommand,
        Plane_EditCommand,
        LinearMotor_EditCommand,
        RotaryMotor_EditCommand,
        BreakStrands_Command,
        JoinStrands_Command,
        BuildDna_EditCommand,
        DnaSegment_EditCommand, 
        DnaStrand_EditCommand,
        DnaDisplayStyle_Command,
        BuildNanotube_EditCommand,
        InsertNanotube_EditCommand,
        NanotubeSegment_EditCommand, 
        RotateChunks_Command,
        TranslateChunks_Command, 
        FuseChunks_Command,
        RotateAboutPoint_Command,
        MultipleDnaSegmentResize_EditCommand
    ]
    # note: we could extract each one's commandName (class constant)
    # if we wanted to return them as commandName, commandClass pairs
    return command_classes

# end

