# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""

@author: Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id$

History:
2008-08-04 Created to aid command stack refactoring. 


TODO: 2008-08-04
- cleanup after command toolbar refactoring. 
- more documentation,
- have more flyouts use this new superclass

@see: Ui_PartLibraryFlyout (a subclass)

REVIEW: should this be moved into the widgets package? [bruce 080827 question]
"""

from utilities.exception_classes import AbstractMethod
from ne1_ui.NE1_QWidgetAction import NE1_QWidgetAction
from PyQt4.Qt import SIGNAL
from utilities.icon_utilities import geticon

from utilities.GlobalPreferences import KEEP_SIGNALS_ALWAYS_CONNECTED
from utilities.GlobalPreferences import USE_COMMAND_STACK

class Ui_AbstractFlyout(object):
    
    def __init__(self, command):
        """
        Create necessary flyout action list and update the flyout toolbar in
        the command toolbar with the actions provided by the object of this
        class.                             
        """
        self.command = command
        self.command_for_exit_action = self.command #bruce 080827 guess
        self.parentWidget = self.command.propMgr            
        self.win =self.command.win                       
        self._isActive = False
        self._createActions(self.parentWidget)
        self._addWhatsThisText()
        self._addToolTipText()
        
        if KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(True)
        
    def _action_in_controlArea_to_show_this_flyout(self):
        """
        To be cleaned up. The current implementation of command toolbar code 
        needs an action in the 'Control Area' of the command toolbar 
        to be provided as an argument in order to update the Flyout toolbar
        Example: If its BuildAtoms FlyoutToolbar, in order to display it, 
        the updateCommandToolbar method needs the 'depositAtomsAction' 
        i.e. the action corresponding to BuildAtoms command to be send 
        as an argument (so that it knows to check the Control Area' button 
        under which this action is defined as a subitem.  this is confusing
        and will be cleaned up. Also it is buggy in case of , for example,
        Paste mode whose action is not present as a submenu in any of the 
        Conteol Area buttons. 
        """
        raise AbstractMethod()   
    
    def _getExitActionText(self):
        """
        Raises AbstractMethod. Subclasses must override this method.
        @see: self._createActions()
        @see: attribute, self.command_for_exit_action
        """
        raise AbstractMethod()
        
    def _createActions(self, parentWidget):
        """
        Define flyout toolbar actions for this mode.
        @see: self._getExitActionText() which defines text for exit action.

        @note: subclasses typically extend this method to define more actions.
        """
        #@NOTE: In Build mode, some of the actions defined in this method are also 
        #used in Build Atoms PM. (e.g. bond actions) So probably better to rename 
        #it as _init_modeActions. Not doing that change in mmkit code cleanup 
        #commit(other modes still implement a method by same name)-ninad20070717
                
        self.exitModeAction = NE1_QWidgetAction(parentWidget, win = self.win)
        exitActionText = self._getExitActionText()
        self.exitModeAction.setText(exitActionText)
        self.exitModeAction.setIcon(geticon('ui/actions/Toolbars/Smart/Exit.png'))
        self.exitModeAction.setCheckable(True)
        self.exitModeAction.setChecked(True)   
            
                
    def connect_or_disconnect_signals(self, isConnect):
        """
        Connect or disconnect widget signals sent to their slot methods.
        This can be extended in subclasses. By default it handles only
        self.exitModeAction.
        
        @param isConnect: If True the widget will send the signals to the slot 
                          method. 
        @type  isConnect: boolean
        
        @see: self.activateFlyoutToolbar, self.deActivateFlyoutToolbar
        """
        if isConnect:
            change_connect = self.win.connect
        else:
            change_connect = self.win.disconnect
        
        change_connect(self.exitModeAction, SIGNAL("triggered()"),
                       self._exitModeActionSlot)
        return

    def _exitModeActionSlot(self): #bruce 080827 split this out, revised for USE_COMMAND_STACK
        """
        Do what's appropriate when self.exitModeAction is triggered. 
        """
        if USE_COMMAND_STACK:
            self.command_for_exit_action.command_Done()
        else:
            # note: this would not always exit the correct command.
            # as of 080827 the action appears to be disabled in those cases.
            # [bruce 080827 comment]
            self.win.toolsDone()
        return

    def activateFlyoutToolbar(self):
        """
        Updates the flyout toolbar with the actions this class provides. 
        """    
        if self._isActive:
            return
        
        self._isActive = True
        
        self.updateCommandToolbar()
        
        self.exitModeAction.setChecked(True)
        
        if not KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(True)
                    
    
    def deActivateFlyoutToolbar(self):
        """
        Updates the flyout toolbar with the actions this class provides.
        """
        if not self._isActive:
            return 
        
        self._isActive = False
        
        if not KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(False)   
            
        self.updateCommandToolbar(bool_entering = False)
            
    def updateCommandToolbar(self, bool_entering = True):
        """
        Update the command toolbar.
        """        
        obj = self
        self.win.commandToolbar.updateCommandToolbar(
            self._action_in_controlArea_to_show_this_flyout(),
            obj, 
            entering = bool_entering)
        
        return
    
    def _addWhatsThisText(self):
        """
        Add 'What's This' help text for all actions on toolbar. 
        Default implementation does nothing. Should be overridden in subclasses
        """
        pass
    
    def _addToolTipText(self):
        """
        Add 'Tool tip' help text for all actions on toolbar. 
        Default implementation does nothing. Should be overridden in subclasses
        """
        pass
        

