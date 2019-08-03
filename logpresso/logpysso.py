import websocket
import numpy as np 
import uuid
import json

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
            yield str(self.cursor)

class Logpresso :
    client = None
    session = None

    def __init__(self):
        self.client = websocket
        
    def connect(self, host, port, username, password):
        url = "ws://"+ host + ":" + str(port) + "/websocket"                              
        self.session = self.client.create_connection(url)
        param = dict(login_name=username, password = password, use_error_return=True)
        response = self._rpc('org.araqne.logdb.msgbus.ManagementPlugin.login', param)

    def query(self, qry) :
        _param = dict(query=qry, context=None, source="python-client")
        _response = self._rpc('org.araqne.logdb.msgbus.LogQueryPlugin.createQuery', _param)
        _queryId= _response.get('id')
        _field_order = _response.get('field_order')
#        _param = dict(streaming=False, compression='none', id=_queryId)
        _param = dict(streaming=False, id=_queryId)
        self._rpc('org.araqne.logdb.msgbus.LogQueryPlugin.startQuery', _param)
        start = time.time()
        while True:
            _status = self._rpc('org.araqne.logdb.msgbus.LogQueryPlugin.queryStatus', dict(id=_queryId))
            if(_status.get('is_end')) : 
                _param = dict(offset=0, limit=10000, id=_queryId, binary_encode=False)
                _params = self._encode('org.araqne.logdb.msgbus.LogQueryPlugin.getResult', _param)
                self.session.send(_params) 
                break
            time.sleep(0.5)     
        print(self.session.recv())


    def listStreamQueries(self) :
        '''
            스트림 쿼리 목록을 조회합니다.

        '''
        _response = self._rpc("com.logpresso.query.msgbus.StreamQueryPlugin.getStreamQueries")
        return np.array(_response.get('stream_queries'))

    def getStreamQuery(self, name) :
        '''
            지정된 이름의 스트림 쿼리의 상세 내역을 조회합니다.

            @param name : 스트림 쿼리 이름
        '''
        _param = dict(name=name)
        _response = self._rpc("com.logpresso.query.msgbus.StreamQueryPlugin.getStreamQuery", _param)
        return np.array(_response.get('stream_query'))

    def createStreamQuery(self, param) :
        '''
            스트림 쿼리를 생성합니다. 스트림 쿼리 이름이 중복되는 경우 예외가 발생합니다. logger, table, stream 이외의
	        데이터 원본 타입이 지정된 경우 예외가 발생합니다. 새로고침 주기가 음수인 경우 예외가 발생합니다.

            @param  : 생성할 스트림쿼리 정보
              - name            이름
              - description     설명
              - interval        실행 주기
              - source_type     소스 타입 (logger, table, stream)
              - sources         데이터 소스 목록
              - query           수행 쿼리
              - is_enabled      활성화 여부
              - is_async        동기화 여부
        '''        
        self._rpc("com.logpresso.query.msgbus.StreamQueryPlugin.createStreamQuery", param) 


    def updateStreamQuery(self, param) : 
        '''
            스트림 쿼리를 수정합니다. 스트림 쿼리가 존재하지 않는 경우 예외가 발생합니다. logger, table, stream 이외의
	        데이터 원본 타입이 지정된 경우 예외가 발생합니다. 새로고침 주기가 음수인 경우 예외가 발생합니다.

            @param  : 생성할 스트림쿼리 정보
              - name            이름
              - description     설명
              - interval        실행 주기
              - source_type     소스 타입 (logger, table, stream)
              - sources         데이터 소스 목록
              - query           수행 쿼리
              - is_enabled      활성화 여부
              - is_async        동기화 여부              
        '''        
        self._rpc("com.logpresso.query.msgbus.StreamQueryPlugin.updateStreamQuery", param) 


    def removeStreamQuery(self, name) :
        '''
            지정된 이름의 스트림 쿼리를 삭제합니다. 지정된 스트림 쿼리가 존재하지 않거나, 소유자가 아닌 경우 예외가 발생합니다.

            @param name : 스트림 쿼리 이름
        '''
        _param = dict(name=name)        
        self._rpc("com.logpresso.query.msgbus.StreamQueryPlugin.removeStreamQuery", _param)

    def _rpc(self, *args): 
        if len(args) == 1 : _param = {}
        else : _param = args[1]
        _params = self._encode(args[0], _param)
        try :
            self.session.send(_params)      
            _resp = json.loads(self.session.recv())
            _header = _resp[0] 
            _body = _resp[1]
            if _header.get('errorCode') : 
                raise LogpressoError
        except LogpressoError:
            print ("logpresso error! : error code = %s, error msg= %s" % (_header.get('errorCode'), _header.get('errorMessage')))
        except :
            print ("logpresso SDK Error")
        finally :
            return _body

    def _encode(self, method, param) :
        _msg = dict(method=method, guid= str(uuid.uuid4()), source='0',type='Request',target='0')
        return json.dumps([_msg, param])

    def __exit__(self) :
        self.client.close()
 
class LogpressoError(Exception):
    pass
