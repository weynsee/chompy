import socket
import thread
import hhc

from pychmlib.chm import chm

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8081

TYPES = {".gif":"image/gif",
         ".jpg":"image/jpeg",
         ".mht":"multipart/related",
         ".html":"text/html",
         ".htm":"text/html"
         }

_SENTINEL = "STOP"

ERR_NO_HHC=1
ERR_INVALID_CHM=2

SERVER_LOCK = thread.allocate_lock()

def start_server(filename, hhc_callback=None):
    thread.start_new_thread(_serve_chm, (DEFAULT_HOST, DEFAULT_PORT, filename, hhc_callback))
    
def stop_server():
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((DEFAULT_HOST, DEFAULT_PORT))
    sock.send(_SENTINEL)
    sock.close()
    print "shutdown signal sent"
    SERVER_LOCK.acquire() #block method until we are sure server stops
    SERVER_LOCK.release()

def _serve_chm(hostname, port, filename, hhc_callback=None):
    SERVER_LOCK.acquire()
    try:
        try:
            chm_file = chm(filename)
        except Exception, e:
            print e
            raise 
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
        _serve_chm_forever(chm_file, hostname, port)
    finally:
        SERVER_LOCK.release()
    print "server shutdown"
    
def _serve_chm_forever(chm_file, hostname, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((hostname, port))
        sock.listen(1)
        while 1:
            csock, caddr = sock.accept()
            try:
                rfile = csock.makefile('rb', 0)
                try:
                    line = rfile.readline().strip()
                    if line == _SENTINEL:
                        break
                    filename = line[line.find("/"):line.find(" HTTP/")].lower()
                    extension = filename[filename.rfind("."):]
                    type = TYPES.get(extension, "text/html")
                finally:
                    rfile.close()
                    
                wfile = csock.makefile('wb', 0)
                try:
                    try:
                        ui = chm_file.resolve_object(filename)
                        if ui:
                            _respond(ui.get_content(), wfile, type)
                        else:
                            _respond_not_found(wfile)
                    except:
                        _respond_error(wfile)
                finally:
                    wfile.close()
            finally:
                csock.close()
        sock.close()
    finally:
        chm_file.close()
    
def _respond(content, cfile, type="text/html"):
    cfile.write("HTTP/1.0 200 OK\n")
    cfile.write("Content-Type: " + type + "\n")
    cfile.write("\n")
    cfile.write(content)
    
def _respond_error(cfile):
    _respond("Page could not be displayed", cfile)
    
def _respond_not_found(cfile):
    _respond("Page could not be found", cfile)
        
        
if __name__ == '__main__':
    import sys
    filenames = sys.argv[1:]
    if filenames:
        start_server(filenames.pop())
        #serve chm files for 30 seconds
        import time
        time.sleep(30)
        stop_server()
        print "server stopped"
    else:
        print "Please provide a CHM file as parameter"
