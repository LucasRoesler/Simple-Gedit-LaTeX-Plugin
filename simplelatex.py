from gettext import gettext as _
from gi.repository import GObject, Gtk, Gedit

# Insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="SimpleLatex" action="SimpleLatex"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class SimpleLatex(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "SimpleLaTeX"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        pass

    def do_deactivate(self):
        pass

    def do_update_state(self):
        pass    
