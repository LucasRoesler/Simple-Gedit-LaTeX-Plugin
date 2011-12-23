# -*- coding: utf-8 -*-

# This file is part of the Simple LaTeX Gedit Plugin
#
# Copyright (C) 2011 Lucas David-Roesler
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public Licence as published by
# the Free Software Foundation; either version 2 of the Licence, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public Licence for more details.
#
# You should have received a copy of the GNU General Public Licence along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import os
from gi.repository import Gio, GObject, Gtk, Gedit, Wnck, Gdk, PeasGtk


__all__ = ("SimpleLatexInterface")

class SimpleLatexInterface(object):

    def __init__(self, datadir,window):
        object.__init__(self)

        self._menu = os.path.join(datadir, 'menu_ui')
        self._ui = Gtk.Builder()
        self.window = window

    def _insert_menu(self):
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()

        #Create a new action group
        self._action_group = Gtk.ActionGroup(name="SimpleLaTeXActions")
        self._action_group.add_actions([("RunpdfLaTeX",None,
                                         _("Run pdfLaTeX"),"<Ctrl>T",
                                         _("Run pdfLaTeX"),self._run_latex),
                                         ("ClosePDF",None,
                                         _("Close the Pdf"),None,
                                         _("Close the Pdf"),self._menu_close_pdf),
                                         ("RunTeX",None,
                                         _("Run TeX"),None,
                                         _("Run TeX"),self._pass),
                                         ("RunXeTeX",None,
                                         _("Run XeTeX"),None,
                                         _("Run XeTeX"),self._pass),
                                         ("RunLaTeX",None,
                                         _("Run LaTeX"),None,
                                         _("Run LaTeX"),self._pass),
                                         ("RunMakeIndex",None,
                                         _("MakeIndex"),None,
                                         _("MakeIndex"),self._pass),
                                         ("RunBibtex",None,
                                         _("Bibtex"),None,
                                         _("Bibtex"),self._pass),
                                         ("OtherEngines",None,
                                         _("Other Tex Engines"),None,
                                         _("Other Tex Engines"),self._pass)])
        manager.insert_action_group(self._action_group,-1)
        #self._ui_id=manager.add_ui_from_string(ui_str)
        self._ui_id=manager.add_ui_from_file(self._menu)

    def _remove_menu(self):
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()
        # Remove the ui
        manager.remove_ui(self._ui_id)
        # Remove the action group
        manager.remove_action_group(self._action_group)
        # Make sure the manager updates
        manager.ensure_update()

    def _create_outputpanel(self):
        # Prepare output panel
        output_panel = Gtk.Builder()
        output_panel.add_from_string(output_panel_str)
        log_text_view = output_panel.get_object('view')
        self._log_text_view = log_text_view
        self._log_widget = output_panel.get_object('output-panel')

        # Insert panel
        panel = self.window.get_bottom_panel()
        panel.add_item(self._log_widget,"Raw TeX Log","Raw TeX Log",None)
        # And focus it
        #panel.activate_item(self._log_widget)
        logtab = Gtk.Builder()
        logtab.add_from_string(log_panel_str)
        self.proc_text_view = logtab.get_object('view')
        self.proc_log_widget = logtab.get_object('log-panel')
        panel.add_item(self.proc_log_widget,'Tex Log','TeX Log',None)
        panel.activate_item(self.proc_log_widget)
        return 
