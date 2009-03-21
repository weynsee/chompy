import socket
import thread

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

SERVER_LOCK = thread.allocate_lock()

def start_server(chm):
    thread.start_new_thread(_serve_chm, (chm, DEFAULT_HOST, DEFAULT_PORT))
    
def stop_server():
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((DEFAULT_HOST, DEFAULT_PORT))
    sock.send(_SENTINEL)
    sock.close()
    print "shutdown signal sent"
    SERVER_LOCK.acquire() #block method until we are sure server stops
    SERVER_LOCK.release()

def _serve_chm(chm, hostname, port):
    SERVER_LOCK.acquire()
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
                    ui = chm.resolve_object(filename)
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
    SERVER_LOCK.release()
    print "server shutdown"
    
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
        chm_file = chm(filenames.pop())
        start_server(chm_file)
        #serve chm files for 30 seconds
        import time
        time.sleep(30)
        stop_server()
        print "server stopped"
        chm_file.close()
    else:
        print "Please provide a CHM file as parameter"
