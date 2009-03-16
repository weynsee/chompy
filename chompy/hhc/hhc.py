from HTMLParser import HTMLParser

class HHCParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self._contexts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'object':
            self._object = HHCObject()
            self._object.__dict__.update(dict(attrs))
        elif tag == 'param':
            param = dict(attrs)
            self._object.__dict__[param['name'].lower()] = param['value']
        elif tag == "ul":
            new_context = self._object
            new_context._set_as_root()
            self._contexts.append(new_context) 

    def handle_endtag(self, tag):
        if tag == 'object':
            if not self._contexts:
                self.root_context = self._object
            else:
                #add the object to the top of the stack's HHCObject
                self._contexts[-1].add_child(self._object)
        elif tag == 'ul':
            self._contexts.pop()
        
class HHCObject:
    
    def __init__(self):
        self.type = ""
        self.is_root = False
        
    def _set_as_root(self):
        self.is_root = True
        self.children = []
        
    def add_child(self, obj):
        self.children.append(obj)


def parse(html):
    parser = HHCParser()
    parser.feed(html)
    parser.close()
    return parser.root_context