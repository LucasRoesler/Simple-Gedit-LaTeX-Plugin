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
    AUTO_OPEN_PDF = "autoopenpdf"
    CMD_LINE_OPT = "cmdlinetext"
    ENGINE_OPT = "engineopt"

    def __init__(self, datadir):
        object.__init__(self)

        self._ui_path = os.path.join(datadir, 'ui', 'config.ui')
        self._settings = Gio.Settings.new(self.CONSOLE_KEY_BASE)
        self._ui = Gtk.Builder()

    def configure_widget(self):
        self._ui.add_objects_from_file(self._ui_path, ["box1"])

        self.set_auto_open_pdf(self._ui.get_object('autoopenpdf'),
                                   self._settings.get_string(self.AUTO_OPEN_PDF))
        self._ui.connect_signals(self)

        widget = self._ui.get_object('box1')

        return widget

    def set_auto_open_pdf(check_button,value):
        check_button.set_boolean('autoopenpdf', button.get_active())
