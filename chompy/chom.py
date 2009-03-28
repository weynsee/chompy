# Copyright 2009 Wayne See
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import server
import appuifw
import e32
import chm_filebrowser
import os
import e32dbm

CONF_FILE = u"E:\\Data\\chompy\\chompy.cfg"
INIT_FILE = u"E:\\Data\\chompy\\online.html"
LOCAL_FILE = u"E:\\Data\\chompy\\offline.html"
SEPARATOR = u"/"

INIT_HTML = u"""<html>
<body>
<script type="text/javascript">
location.replace("http://localhost:""" + unicode(server.PORT) + """/%s")
</script>
</body>
</html>
"""

ERROR_TEMPLATE = """<html>
<body>
%s
</body>
</html>
"""

ERR_READING = u"CHM File cannot be read"
ERR_NO_HHC = u"CHM File contains no HHC file"

if not os.path.exists("E:\\Data\\chompy"):
    os.makedirs("E:\\Data\\chompy")

class Chompy:
    
    def __init__(self):
        self.app_lock = e32.Ao_lock()
        self.fb = chm_filebrowser.Filebrowser()
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
        else:
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
        res = appuifw.popup_menu([u"Offline Mode", u"Online Mode"])
        if res == 0:
            self.open_offline(filename)
        elif res == 1:
            self.open_online(filename)
        
    def open_online(self, filename):
        server.start(filename, self.hhc_callback)
        stall()
        
    def open_offline(self, filename):
        stall()
        e32.ao_yield()
        import pychmlib
        try:
            chm_file = pychmlib.chm.chm(filename)
        except:
            appuifw.note(ERR_READING, "error")
            self.refresh()
            return
        try:
            hhc_file = chm_file.get_hhc()
            if hhc_file:
                import hhc
                hhc_obj = hhc.parse(hhc_file.get_content())
                viewer = HHCViewer(filename, hhc_obj, chm_file.encoding)
                viewer.set_as_offline(chm_file)
                viewer.show()
                self.quit()
            else:
                appuifw.note(ERR_NO_HHC, "error")
                self.refresh()
                return
        finally:
            chm_file.close()
        
    def load_hhc_viewer(self, filename=None, contents=None, encoding=None, error=None):
        if not error:
            viewer = HHCViewer(filename, contents, encoding)
            viewer.show()
            server.stop() #if there is an error, no need to stop server
            self.exit_screen()
        else:
            if error == server.ERR_INVALID_CHM:
                appuifw.note(ERR_READING, "error")
            elif error == server.ERR_NO_HHC:
                appuifw.note(ERR_NO_HHC, "error")
            self.refresh()
        
    def remove(self):
        index = self.lb.current()
        del self.recent[index]
        self.update_list(index)
    
    def quit(self):
        self.save_recent()
        self.app_lock.signal()
        
    def refresh(self):
        menu_list = [(u"Browse for file", self.browse), (u"Exit", self.quit)]
        if self.recent:
            menu_list.insert(0, (u"Open", self.open))
            menu_list.insert(2, (u"Remove", self.remove))
        appuifw.app.menu = menu_list
        appuifw.app.exit_key_handler = self.quit
        appuifw.app.title = u"chompy"
        appuifw.app.body = self.lb
        
    def exit_screen(self):
        appuifw.app.menu = []
        appuifw.app.exit_key_handler = self.quit
        appuifw.app.title = u"chompy"
        text = appuifw.Text()
        text.set(u"Application can now be safely closed.")
        appuifw.app.body = text
    
    def show(self):
        self.lb = appuifw.Listbox(self.get_list(), self.lb_observe)
        self.refresh()
        self.app_lock.wait()
        self.lb = None
        self.hhc_callback = None
        self.fb = None
        appuifw.app.body = None
        appuifw.app.exit_key_handler = None

class HHCViewer:
    
    def __init__(self, filename, hhc_obj, encoding):
        self.title = os.path.basename(filename)
        self.chm_file = None
        self.current_context = hhc_obj
        self.encoding = encoding
        self.app_lock = e32.Ao_lock()
        
    def set_as_offline(self, chm_file):
        self.chm_file = chm_file
    
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
            if selected.local:
                res = appuifw.popup_menu([u"Load page", u"List contents"])
                if res == 0:
                    self.load_in_viewer(selected.local)
                elif res == 1:
                    self.load_directory(selected)
            else:
                self.load_directory(selected)
        else:
            self.load_in_viewer(selected.local)
            
    def load_directory(self, entry):
        self.current_context = entry
        entries = self.to_displayable_list()
        self.lb.set_list(entries)
    
    def load_in_viewer(self, local):
        if self.chm_file:
            self.load_offline(local)
        else:
            self.load_online(local)
            
    def load_online(self, local):
        self.open_local_html(INIT_FILE, INIT_HTML % local)
        
    def open_local_html(self, filename, content):
        html_file = open(filename, "wb")
        try:
            html_file.write(content)
        finally:
            html_file.close()
        browser_lock = e32.Ao_lock()
        viewer = appuifw.Content_handler(browser_lock.signal)
        viewer.open(filename)
        browser_lock.wait()
        
    def load_offline(self, local):
        stall(u"Please wait while page is extracted from the archive...")
        e32.ao_yield()
        ui = self.chm_file.resolve_object("/"+local)
        try:
            if ui:
                content = ui.get_content()
            else:
                content = ERROR_TEMPLATE % "Page cannot be found"
        except:
            content = ERROR_TEMPLATE % "Page could not be displayed"
        try:
            self.open_local_html(LOCAL_FILE, content)
            self.refresh()
        except:
            self.refresh()
            
    def quit(self):
        appuifw.app.exit_key_handler = None
        self.app_lock.signal()
        
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
        self.lb = None
        appuifw.app.body = None


def stall(msg = u"Please wait while CHM file is being read..."):
    appuifw.app.menu = []
    appuifw.app.title = u"Loading..."
    text = appuifw.Text()
    text.style = appuifw.STYLE_ITALIC
    text.set(msg)
    appuifw.app.body = text
    appuifw.app.exit_key_handler = stop_quit
    
def stop_quit():
    appuifw.note(u"Cannot exit until process has finished", "info")


if __name__ == '__main__':
    Chompy().show()