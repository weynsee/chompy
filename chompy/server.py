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

from pychmlib.chm import chm

import socket
import thread
import hhc

HOST = '127.0.0.1'
PORT = 8081

TYPES = {".gif":"image/gif",
         ".jpg":"image/jpeg",
         ".mht":"multipart/related",
         ".html":"text/html",
         ".htm":"text/html"
         }

ERR_NO_HHC = 1
ERR_INVALID_CHM = 2

LOCK = thread.allocate_lock()

STOP_SERVER = False

def start(filename, hhc_callback=None):
    thread.start_new_thread(_serve_chm, (HOST, PORT, filename, hhc_callback))
    
def stop():
    if LOCK.locked():
        global STOP_SERVER
        STOP_SERVER = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            #request shutdown signal
            sock.connect((HOST, PORT))
            sock.close()
            LOCK.acquire() #block method until we are sure server stops
            LOCK.release()
        except:
            pass #cannot connect to server

def _serve_chm(hostname, port, filename, hhc_callback=None):
    LOCK.acquire()
    try:
        try:
            chm_file = chm(filename)
        except Exception, e:
            hhc_callback(error=ERR_INVALID_CHM)
            return
        if hhc_callback:
            hhc_file = chm_file.get_hhc()
            if hhc_file:
                contents = hhc.parse(hhc_file.get_content())
                encoding = chm_file.encoding
                hhc_callback(filename, contents, encoding)
            else:
                chm_file.close()
                hhc_callback(error=ERR_NO_HHC)
                return #no hhc, so what's the sense of continuing?
        try:
            _serve_chm_forever(chm_file, hostname, port)
        except Exception, e:
            # server shutting down because of error
            pass
    finally:
        LOCK.release()
    
def _serve_chm_forever(chm_file, hostname, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((hostname, port))
        sock.listen(5)
        try:
            while 1:
                csock, caddr = sock.accept()
                if STOP_SERVER:
                    break
                _service(csock, chm_file)
        finally:
            sock.close()
    finally:
        chm_file.close()
    
def _read_request(remote):
    return remote.recv(128).strip()
        
def _write_response(remote, chm_file, filename, type):
    try:
        if STOP_SERVER:
            return
        ui = chm_file.resolve_object(filename)
        if ui:
            if STOP_SERVER:
                return
            _respond(ui.get_content(), remote, type)
        else:
            _respond_not_found(remote)
    except:
        _respond_error(remote)
    
def _service(csock, chm_file):
    try:
        line = _read_request(csock)
        filename = line[line.find("/"):line.find(" HTTP/")].lower()
        extension = filename[filename.rfind("."):]
        type = TYPES.get(extension, "text/html")
        _write_response(csock, chm_file, filename, type)    
    except socket.error:
        csock.close()
    else:
        csock.close()

_HTTP_RESPONSE = "HTTP/1.1 200 OK\r\nContent-Length: %d\r\nContent-Type: %s\r\n\r\n%s"

def _respond(content, remote, type="text/html"):
    remote.sendall(_HTTP_RESPONSE % (len(content), type, content))
    
def _respond_error(cfile):
    _respond("Page could not be displayed", cfile)
    
def _respond_not_found(cfile):
    _respond("Page could not be found", cfile)
        
        
if __name__ == '__main__':
    import sys
    filenames = sys.argv[1:]
    if filenames:
        start(filenames.pop())
        #serve chm files for 30 seconds
        import time
        time.sleep(30)
        stop()
    else:
        print "Please provide a CHM file as parameter"