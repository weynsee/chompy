import socket
from pychmlib.chm import chm

DEFAULT_HOST = ''
DEFAULT_PORT = 8081

TYPES = {".gif":"image/gif",
         ".jpg":"image/jpeg",
         ".mht":"multipart/related",
         ".html":"text/html",
         ".htm":"text/html"
         }

class CHMServer:
    
    def __init__(self, hostname=DEFAULT_HOST, port=DEFAULT_PORT):
        self.hostname = hostname
        self.port = port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket = sock
        self.isRunning = False
        
    def serve(self, chm):
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)
        self.isRunning = True
        while True:
            csock, caddr = self.socket.accept()
            try:
                cfile = csock.makefile('rw', 0)
                try:
                    line = cfile.readline().strip()
                    filename = line[line.find("/"):line.find(" HTTP/")].lower()
                    extension = filename[filename.rfind("."):]
                    type = TYPES.get(extension, "text/html")
                    try:
                        ui = chm.resolve_object(filename)
                        if ui:
                            respond(ui.get_content(), cfile, type)
                        else:
                            respondNotFound(cfile)
                    except:
                        respondError(cfile)
                finally:
                    cfile.close()
            finally:
                csock.close()
        
    def shutdown(self):
        print "shutting the server down"
        if self.isRunning:
            self.socket.close()
            

def respond(content, cfile, type="text/html"):
    while True:
        line = cfile.readline().strip()
        if line == '':
            cfile.write("HTTP/1.0 200 OK\n")
            cfile.write("Content-Type: "+type+"\n")
            cfile.write("\n")
            cfile.write(content)
            break
    
def respondError(cfile):
    respond("Page could not be displayed", cfile)
    
def respondNotFound(cfile):
    respond("Page could not be found", cfile)
        
if __name__ == '__main__':
    c = CHMServer()
    chm_file = chm("pychmlib/test/chm_files/iexplore.chm")
    try:
        c.serve(chm_file)
    finally:
        chm_file.close()
        c.shutdown()