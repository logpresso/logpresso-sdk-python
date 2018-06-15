import glob, time, os
import future
import jnius_config
jnius_config.add_options('-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=9506')
try:
    jnius_config.add_classpath(glob.glob(os.path.dirname(os.path.realpath(__file__))+'/araqne-logdb-client-*-package.jar')[0])
except IndexError:
    raise Exception('cannot find araqne-logdb-client jar')
import jnius
import numpy as np
from jnius import autoclass, JavaException, JavaClass

_debug = False

JObject = autoclass('java.lang.Object')
JMap = autoclass('java.util.HashMap')
JInteger = autoclass('java.lang.Integer')
JLong = autoclass('java.lang.Long')
JLongArray = autoclass('[J')
JDoubleArray = autoclass('[D')
JObjectArray = autoclass('[Ljava.lang.Object;')
JDouble = autoclass('java.lang.Double')
JArrayList = autoclass('java.util.ArrayList')
JList = autoclass('java.util.List')
TimeUnit = autoclass('java.util.concurrent.TimeUnit')
JByteBuffer = autoclass('java.nio.ByteBuffer')
JByteOrder = autoclass('java.nio.ByteOrder')
JRArray = autoclass('java.lang.reflect.Array')
JRArray.newInstance.set_rvalue_conversion(False)

JRow = autoclass('org.araqne.logdb.client.Row')

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
    _last_future = None
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

    def await(self, timeout = 0):
        if self._last_future:
            try: 
                if timeout == 0:
                    self._last_future.get()
                else:
                    self._last_future.get(timeout, TimeUnit.MILLISECONDS)
            except Exception as e:
                print(e)
                pass

    def insert(self, table_name, rows):
        if _debug:
            try:
                print(dir(rows))
                print(rows.__javaclass__)
            except:
                pass

        if type(rows) is dict:
            self._last_future = self.client.insert(table_name, JRow(_convert(rows)))
            return self._last_future
        if type(rows) is list or type(rows) is tuple:
            _rows = JArrayList(len(rows))
            for item in rows:
                if type(item) is Row:
                    _rows.add(JRow(item.jmap))
                else:
                    _rows.add(JRow(_convert(item)))
        else:
            _rows = rows

        self._last_future = self.client.insert(table_name, jnius.cast(JList, _rows))
        return self._last_future

    def __getattr__(self, key):
        print(type(key), key)
        return self.client.__getattribute__(key)

def _convert(v):
    _t = type(v)
    if _t is int:
        return JLong(v)
    elif _t is float:
        return JDouble(v)
    elif _t is dict:
        return _from_dict(v)
    elif _t is list or _t is tuple:
        return _from_seq(v)
    elif isinstance(v, JavaClass):
        print('cvcv:', v.__javaclass__)
        return v
    else:
        return v
        #raise Exception('Unsupported Type: ' + str(type(v)))

def _from_seq(v):
    ret = JArrayList(len(v))
    for item in v:
        ret.add(_convert(item))
    return ret

def _from_dict(d):
    m = JMap()
    for k, v in d.items():
        m.put(k, _convert(v))
    return m

class Row():
    jmap = None
    def __init__(self, jmap):
        if type(jmap) == dict:
            jmap = _from_dict(jmap)
        elif not isinstance(jmap, JavaClass) or not jmap.__javaclass__ == 'java/util/HashMap':
            raise TypeError('not java/util/HashMap')
        self.jmap = jmap

    def __getitem__(self, key):
        if key is '_time':
            _time = self.jmap.get('_time')
            if isinstance(_time, JavaClass) and _time.__javaclass__ == 'java/util/Date':
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
