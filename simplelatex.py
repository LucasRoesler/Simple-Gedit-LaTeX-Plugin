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


from gettext import gettext as _
from gi.repository import GObject, Gtk, Gedit
import os

# Insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="Latex" action="RunLaTeX"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

# Create the output panel for the log file
output_panel_str="""
<interface>
  <object class="GtkHBox" id="output-panel">
    <property name="visible">True</property>
    <child>
      <object class="GtkScrolledWindow" id="scrolledwindow1">
    <property name="visible">True</property>
    <property name="hscrollbar_policy">GTK_POLICY_AUTOMATIC</property>
    <property name="vscrollbar_policy">GTK_POLICY_AUTOMATIC</property>
    <property name="shadow_type">GTK_SHADOW_IN</property>
    <child>
      <object class="GtkTextView" id="view">
        <property name="visible">True</property>
        <property name="editable">False</property>
        <property name="wrap_mode">GTK_WRAP_WORD</property>
        <property name="cursor_visible">False</property>
        <property name="accepts_tab">False</property>
        <signal name="button_press_event" handler="on_view_button_press_event"/>
        <signal name="motion_notify_event" handler="on_view_motion_notify_event"/>
        <signal name="visibility_notify_event" handler="on_view_visibility_notify_event"/>
      </object>
    </child>
      </object>
    </child>
  </object>
</interface>
"""


class SimpleLatex(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "SimpleLaTeX"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        print "Hurah for a simpleLaTeX"

        # create a save action.
        # WORK AROUND: I can't figure out how to make gedit_document_save
        # to work, so I used this idea from teh gedit-latex plugin.
        self._save_action = self.window.get_ui_manager().get_action("/MenuBar/FileMenu/FileSaveMenu")
        
        # Insert menu items
        self._insert_menu()
        # Create the output panel
        self._create_outputpanel()

    def do_deactivate(self):
        self._remove_menu()

    def do_update_state(self):
        pass

    def _insert_menu(self):
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()

        #Create a new action group
        self._action_group = Gtk.ActionGroup(name="SimpleLaTeXActions")
        self._action_group.add_actions([("RunLaTeX",None,
                                         _("Run LaTeX"),"<Ctrl>T",
                                         _("Run LaTeX"),self._run_latex)])
        manager.insert_action_group(self._action_group,-1)
        self._ui_id=manager.add_ui_from_string(ui_str)

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
        panel.add_item(self._log_widget,"TeX Log","TeX Log",None)
        # And focus it
        panel.activate_item(self._log_widget)
        return False

    def _process_log(self,log_text):
        # Write the log file
        log_buffer = self._log_text_view.get_buffer()
        log_buffer.set_text(log_text,-1)
        return False

    def _scroll_to_end(self):
        log_buffer = self._log_text_view.get_buffer()
        iter = log_buffer.get_end_iter()
        self._log_text_view.scroll_to_iter(iter, 0.0, False, 0.5, 0.5)
        return False


    def _create_tex_command(self):
        delay = "sleep 1; "
        program = "pdflatex"
        options = "-file-line-error -halt-on-error -shell-escape -synctex=1 -jobname={0} {1}"
        command = delay + program + ' ' + options
        return command

    def _call_latex(self,widget,event):
        doc = self.window.get_active_document()
        # Get the file info
        file_location = doc.get_uri_for_display()
        file_name = doc.get_short_name_for_display()

        # Format the file info for the pdflatex command
        file_folder = file_location[:-len(file_name)]
        short_name = file_name[:-4]
        # Construct the pdflatex command
        tex_command = self._create_tex_command().format(short_name,file_name)

        # Run pdflatex after the document has finished saving
        os.chdir(file_folder)
        tex_return = os.system(tex_command)

        # Add log to output panel
        log_file = open(file_folder + short_name + ".log","r")
        log_text = log_file.read()
        log_file.close()
        self._process_log(log_text)
        self._scroll_to_end()
        if tex_return == 0:
           self.window.get_bottom_panel().set_property("visible",False)
           #self._synctex.activate()
        else:
           self.window.get_bottom_panel().set_property("visible",True)
        return False

    def _run_latex(self,action,what):
        doc = self.window.get_active_document()
        mime = doc.get_mime_type()
        if mime == "text/x-tex":
            self._save_action.activate()
            latex = doc.connect("saved",self._call_latex)
        else:
            print "This is not a tex file"
        return False
