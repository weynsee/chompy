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
            new_context._set_as_inner_node()
            self._contexts.append(new_context) 

    def handle_endtag(self, tag):
        if tag == 'object':
            if not self._contexts:
                self.root_context = self._object
                self._object.is_root = True
            else:
                #add the object to the top of the stack's HHCObject
                self._contexts[ - 1].add_child(self._object)
        elif tag == 'ul':
            self._contexts.pop()
        
class HHCObject:
    
    def __init__(self):
        self.type = None
        self.is_inner_node = False #means this node has leaves
        self.is_root = False
        self.parent = None
        self.name = None
        
    def _set_as_inner_node(self):
        self.is_inner_node = True
        self.children = []
        
    def add_child(self, obj):
        self.children.append(obj)
        obj.parent = self


def parse(html):
    parser = HHCParser()
    parser.feed(html)
    parser.close()
    return parser.root_context

if __name__ == "__main__":
    import sys
    from pychmlib.chm import chm
    filenames = sys.argv[1:]
    if filenames:
        chm_file = chm(filenames.pop())
        hhc_file_contents = chm_file.get_hhc().get_content()
        contents = parse(hhc_file_contents)
        def recur_print(content, spaces=0):
            if spaces > 0:
                print " " * spaces + content.name
            if content.is_inner_node:
                for i in content.children:
                    recur_print(i, spaces + 2)
        recur_print(contents) 
        chm_file.close()
    else:
        print "Please provide a CHM file as parameter"
