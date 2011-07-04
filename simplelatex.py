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
from gi.repository import GObject, Gtk, Gedit, Wnck, Gdk
import os, re

# Insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="Latex" action="RunLaTeX"/>
      </placeholder>
      <placeholder name="ToolsOps_2">
        <menuitem name="ClosePDf" action="ClosePDF"/>
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
        # to work, so I used this idea from the gedit-latex plugin.
        self._save_action = self.window.get_ui_manager().get_action("/MenuBar/FileMenu/FileSaveMenu")

        # Create handlers for closed tabs, we will use this to close
        # the corresponding pdfs that are open.
        handlers = []
        handler_id = self.window.connect("tab-removed",self.on_tab_removed)
        handlers.append(handler_id)

        self.window.set_data("TabClosingHandlers",handlers)
        
        # Insert menu items
        self._insert_menu()
        # Create the output panel
        self._create_outputpanel()

    def do_deactivate(self):
        self._remove_menu()

        # Deactivate all of the tab handlers.
        handlers = self.window.get_data("TabClosingHandlers")
        for handler_id in handlers:
            self.window.disconnect(handler_id)

    def do_update_state(self):
        pass

    def on_tab_removed(self, window, tab, data=None):
        # Get the name of the closed tab
        document = tab.get_document()
        doc_name = document.get_short_name_for_display()[:-4]
        print doc_name
        if document.get_mime_type() == "text/x-tex":
            self._close_pdf(doc_name)

    def _insert_menu(self):
        # Get the Gtk.UIManager
        manager = self.window.get_ui_manager()

        #Create a new action group
        self._action_group = Gtk.ActionGroup(name="SimpleLaTeXActions")
        self._action_group.add_actions([("RunLaTeX",None,
                                         _("Run LaTeX"),"<Ctrl>T",
                                         _("Run LaTeX"),self._run_latex),
                                         ("ClosePDF",None,
                                         _("Close the Pdf"),None,
                                         _("Close the Pdf"),self._menu_close_pdf)])
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

    def _get_doc_info(self):
        # Get the active document info and make them globally available
        ##
        doc = self.window.get_active_document()
        # Get the file info
        self._file_location = doc.get_uri_for_display()
        self._file_name = doc.get_short_name_for_display()
        self._mime = doc.get_mime_type()

        # Format the file info for the pdflatex command
        self._file_folder = self._file_location[:-len(self._file_name)]
        self._short_name = self._file_name[:-4]
        return False

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
    def _running_tex(self,message):
        log_buffer = self._log_text_view.get_buffer()
        log_buffer.set_text(message,-1)
        start = log_buffer.get_start_iter()
        end = log_buffer.get_end_iter()
        # TODO : there are no errors, but the tag is not working
        tag = Gtk.TextTag()
        tag.set_property("foreground","red")
        #tag.set_property("font","Inconsolta 10")
        #tag.set_property("weight",700)
        log_buffer.apply_tag(tag,start,end)

    def _scroll_to_end(self):
        log_buffer = self._log_text_view.get_buffer()
        iter = log_buffer.get_end_iter()
        self._log_text_view.scroll_to_iter(iter, 0.0, False, 0.5, 0.5)
        return False

    def _close_pdf(self,doc_name):
        # Make the pdf name.
        pdf_name = doc_name + ".pdf"
        # get the screen and search for the pdf
        screen = Wnck.Screen.get_default()
        screen.force_update()
        window_list = screen.get_windows()
        # cycle through the window list, if we find a pdf matching the
        # expected TeX output, we close it.
        for app_window in window_list:
            window_name  = app_window.get_name()
            pos = window_name.find(pdf_name)
            if pos == 0:
                app_window.close(0)
                
    def _menu_close_pdf(self,widget,what):
        doc = self.window.get_active_document()
        doc_name = doc.get_short_name_for_display()[:-4]
        self._close_pdf(doc_name)
        return False

    def _get_synctex(self):
        self._synctex = self.window.get_ui_manager().get_action("/MenuBar/ToolsMenu/ToolsOps_2/Synctex")
        return False


    def _create_tex_command(self):
        program = "pdflatex"
        options = "-file-line-error -halt-on-error -shell-escape -synctex=1 -jobname={0} {1}"
        command = program + ' ' + options
        return command

    def _call_latex(self,widget,event):
        # Actually call tex.
        ##
        # Get the file info
        file_location = self._file_location
        file_name = self._file_name
        file_folder = self._file_folder
        short_name = self._short_name

        # Get rid of the save listener
        listener = self.window.get_data("SaveListen")
        self.window.get_active_document().disconnect(listener)
        
        # Construct the pdflatex command
        tex_command = self._create_tex_command().format(short_name,file_name)

        # Go to the file folder and run tex on the document
        os.chdir(file_folder)
        tex_return = os.system(tex_command)

        # Add log to output panel
        log_file = open(file_folder + short_name + ".log","r")
        log_text = log_file.read()
        log_file.close()
        self._process_log(log_text)
        if tex_return == 0:
            self.window.get_bottom_panel().set_property("visible",False)
            self._synctex.activate()
        else:
            self._scroll_to_end()
            self.window.get_bottom_panel().set_property("visible",True)
        return False

    def _run_latex(self,action,what):
        # Save the file and run latex
        ##
        doc = self.window.get_active_document()
        # Prepare the synctex action, we have to wait until now
        # because we need to wait for the synctex plugin to load.
        self._get_synctex()
        self._get_doc_info()

        # If the document is a TeX file, we save and compile it.
        if self._mime == "text/x-tex":
            self._save_action.activate()
            self._running_tex("  Running pdfLaTeX ... ")
            # Open bottom panel and tell the user that TeX is running
            self.window.get_bottom_panel().set_property("visible",True)
            latex = doc.connect("saved",self._call_latex)
            self.window.set_data("SaveListen",latex)
        else:
            print "This is not a tex file"
        return False
