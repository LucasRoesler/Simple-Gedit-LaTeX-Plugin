General Information
===================

This is a simple LaTeX plugin for Gedit.  The goal is to have a plugin
that creates a command to run LaTeX on the current Gedit document
and then use the SyncTeX plugin to open the pdf.

Goals
-----
In large part this is a learning exercise. It is also a result of me
being impatient for the gedit-latex plugin to get updated for Gnome3. I
also don't want quite as many features as the gedit-latex plugin
provides.  All I need is a clean interface and a keyboard short cut
that runs LaTeX.

Some future goals are to

* The current SyncTeX support is pretty raw.  It would be good to make
  sure that the plugin is installed and activated when this plugin is
  activated.
* Create a true install script.

Current Features
----------------

* Compile the current tex document using `<Ctrl>t`
* Auto-open the pdf when a tex document is open
* Auto-close the pdf when the tex document is closed
* Run Bibtex and MakeIndex on the current file

Dependencies 
============
* Rubber - https://launchpad.net/rubber - this allows us to easily process the tex log file.

Installation
============

Simply copy `simplatex.plugin` and the folder `simplatex` to

    ~/.local/share/gedit/plugins

you can use
    
    cp -r simplelatex* ~/.local/share/gedit/plugins

copy `org.gnome.get.plugins.simplelatex.gschema.xml` to

    /usr/share/glib-2.0/schemas/

you can use
    
    sudo cp org.gnome.get.plugins.simplelatex.gschema.xml /usr/share/glib-2.0/schemas/
    
and then run 

    sudo glib-compile-schemas /usr/share/glib-2.0/schemas/
    
Now your ready to go!

Contributing
============

Get the code at

    git clone git://github.com/TheAxeR/Simple-Gedit-LaTeX-Plugin.git
    
