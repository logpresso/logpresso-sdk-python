import glob, time, os
import future
import jnius_config
#jnius_config.add_options('-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=9506')
try:
    jnius_config.add_classpath(glob.glob(os.path.dirname(os.path.realpath(__file__))+'/araqne-logdb-client-*-package.jar')[0])
except IndexError:
    raise Exception('cannot find araqne-logdb-client jar')
import jnius
from jnius import autoclass, JavaException

class Cursor:
    cursor = None
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.cursor:
            self.cursor.close()

    def __iter__(self):
        while self.cursor.hasNext():
            yield Row(self.cursor.next())

class LogpressoClient:
    client = None
    def __init__(self, host, port, username, password):
        self.client = autoclass('org.araqne.logdb.client.LogDbClient')()
        self.client.connect(host, port, username, password)

    def query(self, query):
        return Cursor(self.client.query(query))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.client:
            self.client.close()

    def __getattr__(self, key):
        return self.client.__getattr__(key)

class Row():
    jmap = None
    def __init__(self, jmap):
        if not isinstance(jmap, jnius.JavaClass) or not jmap.__javaclass__ == 'java/util/HashMap':
            raise TypeError('not java/util/HashMap')
        self.jmap = jmap

    def __getitem__(self, key):
        if key is '_time':
            _time = self.jmap.get('_time')
            if isinstance(_time, jnius.JavaClass) and _time.__javaclass__ == 'java/util/Date':
                return time.localtime(_time.getTime() / 1000)
            else:
                return _time
        else:
            return self.jmap.get(key)
    
    def get(self, key, default=None):
        ret = self.jmap.get(key)
        if ret:
            return ret
        else:
            return default
        
    def __contains__(self, key):
        return self.jmap.containsKey(key)
    
    def keys(self):
        _iter = self.jmap.keySet().iterator()
        while _iter.hasNext():
            yield _iter.next()
        _iter = None

    def items(self):
        raise NotImplemented

    def values(self):
        _iter = self.jmap.valueSet().iterator()
        while _iter.hasNext():
            yield _iter.next()
        _iter = None

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return dict(self.items()) == dict(other.items())
    
    def __setitem__(self, key, value):
        raise KeyError

    def __delitem__(self, key):
        raise KeyError
        
    def __iter__(self):
        _iter = self.jmap.entrySet().iterator()
        while _iter.hasNext():
            _e = _iter.next()
            yield _e.getKey(), _e.getValue()
        _iter = None
    
    def __len__(self):
        return self.jmap.size()
    
    def __getattr__(self, key):
        return self.__getitem__(key)
    
    def data(self):
        _iter = self.jmap.entrySet().iterator()
        while _iter.hasNext():
            _e = _iter.next()
            if _e.getKey() in ('_id', '_table', '_time'):
                continue
            yield _e.getKey(), _e.getValue()
        _iter = None

# vim: set ts=4 sw=4 sws=4 ai expandtab smarttab :
