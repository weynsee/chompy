from __future__ import nested_scopes
from pychmlib.chm import chm

import server
import appuifw
import e32
import filebrowser
import os
import e32dbm
import hhc

CONF_FILE = u"E:\\Data\\chompy\\chompy.cfg"
INIT_FILE = u"E:\\Data\\chompy\\tmp.html"
SEPARATOR = u"/"

INIT_HTML = u"""<html>
<body>
<script type="text/javascript">
document.location = "http://""" + unicode(server.DEFAULT_HOST) + """:""" + unicode(server.DEFAULT_PORT) + """/%s"
</script>
</body>
</html>
"""

if not os.path.exists("E:\\Data\\chompy"):
    os.makedirs("E:\\Data\\chompy")

class Chompy:
    
    def __init__(self):
        self.app_lock = e32.Ao_lock()
        self.fb = filebrowser.Filebrowser()
        self.load_recent()
        self.hhc_callback = e32.ao_callgate(self.load_hhc_viewer)
        
    def load_recent(self):
        try:
            db = e32dbm.open(CONF_FILE, "c")
            recent = db["recent"] 
            if recent:
                self.recent = recent.split(SEPARATOR)
            else:
                self.recent = [] 
            db.close()
        except:
            self.recent = []
        
    def save_recent(self):
        db = e32dbm.open(CONF_FILE, "wf")
        try:
            db["recent"] = SEPARATOR.join(self.recent)
        finally:
            db.close()

    def browse(self):
        self.fb.show()
        selected = self.fb.selected
        if selected:
            file = unicode(selected)
            if file not in self.recent:
                self.recent.append(file)
                self.update_list(len(self.recent) - 1)    
            self.open(file)
        self.refresh()
        
    def to_display(self, filename):
        return unicode(os.path.basename(filename))
        
    def update_list(self, selected_index=None):
        if self.recent:
            self.lb.set_list(self.get_list(), selected_index)
        else:
            self.lb.set_list(self.get_list())
            
    def get_list(self):
        if self.recent:
            return map(self.to_display, self.recent)
        else:
            return [u"Select file"]
        
    def lb_observe(self, index=None):
        if index is None:
            index = self.lb.current()
        if not self.recent:
            self.browse()
        else:
            self.open(self.recent[index])
    
    def open(self, filename=None):
        if filename is None:
            filename = self.recent[self.lb.current()]
        server.start_server(filename, self.hhc_callback)
        self.stall()
        
    def load_hhc_viewer(self, filename=None, contents=None, encoding=None, error=None):
        if not error:
            viewer = HHCViewer(filename, contents, encoding)
            viewer.show()
            server.stop_server() #if there is an error, no need to stop server
            self.quit()
        else:
            if error == server.ERR_INVALID_CHM:
                appuifw.note(u"CHM File cannot be read", "error")
            elif error == server.ERR_NO_HHC:
                appuifw.note(u"CHM File contains no HHC file", "error")
            self.refresh()
        
    def remove(self):
        index = self.lb.current()
        del self.recent[index]
        self.update_list(index)
    
    def quit(self):
        self.app_lock.signal()
        self.save_recent()
        self.lb = None
        self.hhc_callback = None
        
    def stall(self):
        appuifw.app.menu = []
        appuifw.app.title = u"Loading..."
        text = appuifw.Text()
        text.style = appuifw.STYLE_ITALIC
        text.set(u"Please wait while CHM file is being read...")
        appuifw.app.body = text
        appuifw.app.exit_key_handler = None
        
    def refresh(self):
        menu_list = [(u"Browse for file", self.browse), (u"Exit", self.quit)]
        if self.recent:
            menu_list.insert(0, (u"Open", self.open))
            menu_list.insert(2, (u"Remove", self.remove))
        appuifw.app.menu = menu_list
        appuifw.app.exit_key_handler = self.quit
        appuifw.app.title = u"chompy"
        appuifw.app.body = self.lb
    
    def show(self):
        self.lb = appuifw.Listbox(self.get_list(), self.lb_observe)
        self.refresh()
        self.app_lock.wait()

class HHCViewer:
    
    def __init__(self, filename, hhc_obj, encoding):
        self.title = os.path.basename(filename)
        self.current_context = hhc_obj
        self.encoding = encoding
        self.app_lock = e32.Ao_lock()
    
    def to_displayable_list(self):
        entries = map(lambda x: x.name.decode(self.encoding), self.current_context.children)
        if not self.current_context.is_root:
            entries.insert(0, u"..")
        return entries
    
    def lb_observe(self, index=None):
        if index is None:
            index = self.lb.current()
        if index == 0 and not self.current_context.is_root:
            #go back up
            selected = self.current_context.parent
        else:
            selected_index = index
            if not self.current_context.is_root:
                selected_index -= 1
            selected = self.current_context.children[selected_index]
        if selected.is_inner_node:
            self.current_context = selected
            entries = self.to_displayable_list()
            self.lb.set_list(entries)
        else:
            self.load_in_viewer(selected)
    
    def load_in_viewer(self, entry):
        f = file(INIT_FILE, "w")
        print "looking up", (INIT_HTML % entry.local)
        f.write(INIT_HTML % entry.local)
        f.close()
        lock = e32.Ao_lock()
        viewer = appuifw.Content_handler(lock.signal)
        viewer.open(INIT_FILE)
        lock.wait()
            
    def quit(self):
        self.app_lock.signal()
        self.lb = None
        
    def open(self):
        self.lb_observe()
        
    def refresh(self):
        appuifw.app.menu = [(u"Open", self.open), (u"Exit", self.quit)]
        appuifw.app.exit_key_handler = self.quit
        appuifw.app.title = self.title
        appuifw.app.body = self.lb
        
    def show(self):
        entries = self.to_displayable_list() 
        self.lb = appuifw.Listbox(entries, self.lb_observe)
        self.refresh()
        self.app_lock.wait()


if __name__ == '__main__':
    Chompy().show()