# -*- coding: utf-8 -*-

# This file is part of the Simple LaTeX Gedit Plugin
#
# Copyright (C) 2011 Lucas David-Roesler
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public Licence as published by the Free Software
# Foundation; either version 2 of the Licence, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more
# details.
#
# You should have received a copy of the GNU General Public Licence along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA


import os
from gi.repository import Gio, Gtk, Gdk


__all__ = ("SimpleLaTeXConfigWidget")


class SimpleLaTeXConfigWidget(object):
    BASE_KEY = "org.gnome.gedit.plugins.simplelatex"
    AUTO_OPEN_PDF = "auto-open-pdf"
    CMD_LINE_OPT = "commandline-options"
    ENGINE_OPT = "select-default-engine"
    SYNCTEX_OPT = "separate-synctex"

    def __init__(self, datadir):
        object.__init__(self)

        self._ui_path = os.path.join(datadir, 'config.glade')
        self._settings = Gio.Settings.new(self.BASE_KEY)
        self._ui = Gtk.Builder()

    def configure_widget(self):
        self._ui.add_objects_from_file(self._ui_path, ["box1"])

        # Grab and display the saved settings.
        self.get_auto_open_pdf(self._ui.get_object('autoopenpdf'),
                                   self._settings.get_boolean(self.AUTO_OPEN_PDF))
        self.get_auto_open_pdf(self._ui.get_object('synctex'),
                                   self._settings.get_boolean(self.SYNCTEX_OPT))
        self.get_engine_option(self._ui.get_object('engineopt'),
                                   self._settings.get_enum(self.ENGINE_OPT))
        self.get_command_line(self._ui.get_object('cmdlineopt'),
                                   self._settings.get_string(self.CMD_LINE_OPT))
        # Connect our listeners, so we can actually save any changes made.
        # Note that the signals are acutally defined in the glade file.
        self._ui.connect_signals(self)

        widget = self._ui.get_object('box1')

        return widget

    def get_auto_open_pdf(self,check_button,value):
        # Get the current setting
        check_button.set_active(value)
    def get_command_line(self,entry,value):
        entry.set_text(value)
    def get_engine_option(self,option_box,value):
        # Get the current TeX engine, note that the result from
        # settings is indexed starting at 1, but we need starting
        # at 0.
        option_box.set_active(value-1)

    # Change the setting
    def set_auto_open_pdf(self,check_button):
        self._settings.set_boolean("auto-open-pdf", check_button.get_active())
    def set_command_line(self,entry):
        self._settings.set_string("commandline-options", entry.get_text())
    def set_engine_option(self,combobox):
        self._settings.set_enum("select-default-engine", combobox.get_active()+1)
    def set_synctex(self,check_button):
        self._settings.set_boolean("separate-synctex", check_button.get_active())
