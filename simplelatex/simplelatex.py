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
from gi.repository import Gio, GObject, Gtk, Gedit, Wnck, Gdk, PeasGtk
from config import SimpleLaTeXConfigWidget
import os, subprocess

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
      </object>
    </child>
      </object>
    </child>
  </object>
</interface>
"""

log_panel_str="""
<interface>
  <object class="GtkHBox" id="log-panel">
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
      </object>
    </child>
      </object>
    </child>
  </object>
</interface>
"""

class SimpleLatex(GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):
    __gtype_name__ = "SimpleLaTeX"
    
    BASE_KEY = "org.gnome.gedit.plugins.simplelatex"
    AUTO_OPEN_PDF = "auto-open-pdf"
    CMD_LINE_OPT = "commandline-options"
    ENGINE_OPT = "select-default-engine"
    SYNCTEX_OPT = "separate-synctex"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        print "Hurah for a simpleLaTeX"

        self.settings = Gio.Settings.new(self.BASE_KEY)
        self.settings.connect("changed", self.on_settings_changed)
        self._get_settings()
        # create a save action.
        # WORK AROUND: I can't figure out how to make gedit_document_save
        # to work, so I used this idea from the gedit-latex plugin.
        self._save_action = self.window.get_ui_manager().get_action("/MenuBar/FileMenu/FileSaveMenu")

        # Create handlers for closed tabs, we will use this to close
        # the corresponding pdfs that are open.
        handlers = []
        handler_id = self.window.connect("tab-removed",self.on_tab_removed)
        handlers.append(handler_id)

        handler_id = self.window.connect("tab-added",self.on_tab_added)
        handlers.append(handler_id)

        self.window.set_data("TabHandlers",handlers)
        
        # Insert menu items
        self._insert_menu()
        # Create the output panel
        self._create_outputpanel()

    def do_create_configure_widget(self):
        config_widget = SimpleLaTeXConfigWidget(self.plugin_info.get_data_dir())

        return config_widget.configure_widget()
        

    def do_deactivate(self):
        self._remove_menu()

        # Deactivate all of the tab handlers.
        handlers = self.window.get_data("TabHandlers")
        for handler_id in handlers:
            self.window.disconnect(handler_id)

    def do_update_state(self):
        pass

    def on_settings_changed(self,settings,key):
        self._get_settings()

    def on_tab_removed(self, window, tab, data=None):
        # Get the name of the closed tab
        document = tab.get_document()
        doc_name = document.get_short_name_for_display()[:-4]
        if document.get_mime_type() == "text/x-tex":
            self._close_pdf(doc_name)

    def on_tab_added(self, window, tab, data=None):
        # It seems that we need to wait for this menu item to be construced,
        # after tab creation seems to work.
        self._synctex = self.window.get_ui_manager().get_action("/MenuBar/ToolsMenu/ToolsOps_2/Synctex")
        # If we have a TeX document, then we try using synctex to open
        # the document.  This will only work if the *.synctex file is there
        document = tab.get_document()
        if document.get_mime_type() == "text/x-tex":
            handler_id = document.connect("loaded",self._tab_opens_pdf)
            self.window.set_data("TabOpensPDF",handler_id)

    def _get_settings(self):
        self.auto_open_pdf = self.settings.get_boolean(self.AUTO_OPEN_PDF)
        self.tex_engine = self.settings.get_string(self.ENGINE_OPT)
        self.tex_options = self.settings.get_string(self.CMD_LINE_OPT)
        self.synctex_opt = self.settings.get_boolean(self.SYNCTEX_OPT)

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

    def _tab_opens_pdf(self,document,event):
        # Use synctex to try and open the pdf.
        self._synctex.activate()
        # Now we wait for the window to open and refocus on gedit
        screen = Wnck.Screen.get_default()
        h_id = screen.connect("window-opened",self._focus_gedit)
        self.window.set_data("WindowListener",h_id)

        # kill the tab listener
        listener = self.window.get_data("TabOpensPDF")
        document.disconnect(listener)
        

    def _focus_gedit(self,screen,window):
        # We refocus on Gedit, we assume that this is occurring as a
        # result of synctex being called upon the document being opened,
        # so the last window in the stack should be the pdf and the
        # second to last is Gedit.  It seems to work. 
        screen.force_update()
        window_list = screen.get_windows_stacked()
        gedit_window = window_list[-2]

        # Not sure about using a timestampe of zero here. Wnck throughs
        # a warning, so it would be good to learn more about x11 timestamps
        gedit_window.activate(1)

        # kill the listener
        listener = self.window.get_data("WindowListener")
        screen.disconnect(listener)


    def _split_screen(self,screen):
        # not ready yet!
        height = screen.get_height()
        width = screen.get_width
        print width
        #half_width = width * .5
        window_list = screen.get_windows_stacked()
        
        a = window_list[-1] # pdf
        b = window_list[-2] # gedit

        a.unmaximize()
        b.unmaximize()

        #a.set_geometry(0, 255, 0, 0, half_width, height)
        #b.set_geometry(0, 255, half_width + 1, 0 , half_width - 1, height)

    def _get_doc_info(self,doc):
        # Get the active document info and make them globally available
        ##
        #doc = self.window.get_active_document()
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
        panel.add_item(self._log_widget,"Raw TeX Log","Raw TeX Log",None)
        # And focus it
        #panel.activate_item(self._log_widget)
        logtab = Gtk.Builder()
        logtab.add_from_string(log_panel_str)
        self.proc_text_view = logtab.get_object('view')
        self.proc_log_widget = logtab.get_object('log-panel')
        panel.add_item(self.proc_log_widget,'Tex Log','TeX Log',None)
        panel.activate_item(self.proc_log_widget)
        return False

    def _process_log(self,log_text):
        # Write the log file
        log_buffer = self._log_text_view.get_buffer()
        log_buffer.set_text(log_text,-1)

        short_name = self._short_name
        file_folder = self._file_folder
        file_location = self._file_location
        
        errors = subprocess.check_output(["rubber-info --errors " + file_folder + short_name + ".log"],shell=True)
        checks = subprocess.check_output(["rubber-info --check " + file_folder + short_name + ".log"],shell=True)
        refs = subprocess.check_output(["rubber-info --refs " + file_folder + short_name + ".log"],shell=True)
        logbuf = self.proc_text_view.get_buffer()
        processed_log = errors + refs + checks
        
        logbuf.set_text(processed_log.replace(self._file_name+':',''),-1)
        self.window.get_bottom_panel().activate_item(self.proc_log_widget)


    def _running_tex(self,message):
        log_buffer = self._log_text_view.get_buffer()
        log_buffer.set_text(message,-1)

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
            # if the window name starts with pdf_name we close it
            if pos == 0:
                app_window.close(1)
                
    def _menu_close_pdf(self,widget,what):
        doc = self.window.get_active_document()
        doc_name = doc.get_short_name_for_display()[:-4]
        self._close_pdf(doc_name)
        return False


    def _create_tex_command(self):
        # Not needed any longer
        program = self.tex_engine
        options = self.tex_options + " {LONGFILE}"
        command = program + ' ' + options
        return command

    def _run_synctex(self):
        synctex_cmd = "synctex update -o "
        synctex_cmd += self._file_location
        synctex_cmd += " "
        synctex_cmd += self._file_folder
        result = os.system(synctex_cmd)
        print synctex_cmd

    def _call_tex(self,widget,event):
        # Actually call tex.
        ####################
        # Get the file info
        file_location = self._file_location
        file_name = self._file_name
        file_folder = self._file_folder
        short_name = self._short_name

        # Get rid of the save listener
        listener = self.window.get_data("SaveListen")
        self.window.get_active_document().disconnect(listener)
        
        # Construct the pdflatex command
        tex_command = self.tex_engine
        tex_command += " " + self.tex_options
        tex_command += " {NAME}".format(SHORTNAME=short_name,NAME=file_name)

        # Go to the file folder and run tex on the document
        os.chdir(file_folder)
        tex_return = os.system(tex_command)

        if self.synctex_opt:
            self._run_synctex()

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
        #############################
        doc = self.window.get_active_document()
        self._get_doc_info(doc)

        # If the document is a TeX file, we save and compile it.
        if self._mime == "text/x-tex":
            self._save_action.activate()
            # Open bottom panel and tell the user that TeX is running
            self._running_tex("  Running pdfLaTeX ... ")
            self.window.get_bottom_panel().activate_item(self._log_widget)
            self.window.get_bottom_panel().set_property("visible",True)
            
            # Dont' run TeX until the save is complete.
            latex = doc.connect("saved",self._call_tex)
            self.window.set_data("SaveListen",latex)
        else:
            print "This is not a tex file"
        return False
