#
# filebrowser.py
#
# A very simple file browser script to demonstrate the power of Python
# on Series 60.
#      
# Copyright (c) 2005 Nokia Corporation
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
#

import os
import appuifw
import e32
import dir_iter

class Filebrowser:
    def __init__(self):
        self.script_lock = e32.Ao_lock()
        self.dir_stack = []
        self.current_dir = dir_iter.Directory_iter(e32.drive_list())
        self.left_arrow_clicked = False
        self.selected = None

    def show(self):
        from key_codes import EKeyLeftArrow
        entries = self.current_dir.list_repr()
        if not self.current_dir.at_root:
            entries.insert(0, (u"..", u""))
        self.lb = appuifw.Listbox(entries, self.lbox_observe)
        self.lb.bind(EKeyLeftArrow, self.left_arrow_handler)
        self.refresh()
        self.script_lock.wait()
        self.lb = None
        
    def left_arrow_handler(self):
        self.left_arrow_clicked = True
        self.lbox_observe(0)

    def refresh(self):
        appuifw.app.title = u"File browser"
        appuifw.app.menu = []
        appuifw.app.exit_key_handler = self.exit_key_handler
        appuifw.app.body = self.lb

    def do_exit(self):
        self.exit_key_handler()

    def exit_key_handler(self):
        appuifw.app.exit_key_handler = None
        self.selected = None #nothing was selected
        self.script_lock.signal()

    def lbox_observe(self, ind=None):
        if not ind == None:
            index = ind
        else:
            index = self.lb.current()
        focused_item = 0
        
        if self.current_dir.at_root and self.left_arrow_clicked:
            self.left_arrow_clicked = False
            return #No op 

        if self.current_dir.at_root:
            self.dir_stack.append(index)
            self.current_dir.add(index)
        elif index == 0:                              # ".." selected
            focused_item = self.dir_stack.pop()
            self.current_dir.pop()
        elif os.path.isdir(self.current_dir.entry(index - 1)):
            self.dir_stack.append(index)
            self.current_dir.add(index - 1)
        else:
            item = self.current_dir.entry(index - 1)
            self.selected = item
            self.script_lock.signal()
            return
        entries = self.current_dir.list_repr()
        if not self.current_dir.at_root:
            entries.insert(0, (u"..", u""))
        self.lb.set_list(entries, focused_item)

if __name__ == '__main__':
    Filebrowser().show()
