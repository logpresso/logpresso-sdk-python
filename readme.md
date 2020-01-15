# 로그프레소 파이썬 SDK

## 의존성

- future
- numpy
- pyjnius >= 1.1.2dev0

## EGG 다운로드

**설치 전에 반드시 아래의 의존성 문제를 해결할것**

- [logpresso-sdk-python for python 2.7](http://staging.araqne.org/logpresso-1.0.0-py2.7.egg)
- [logpresso-sdk-python for python 3.6](http://staging.araqne.org/logpresso-1.0.0-py3.6.egg)

```
easy_install logpresso-1.0.0-py2.7.egg
OR
easy_install logpresso-1.0.0-py3.6.egg
```


## 의존성 빌드 및 설치(pyjnius 최신버전)

2018년 6월 현재 pip 에 등록되어 있는 pyjnius 1.1.1 버전은 outdate 되어 제대로 동작하지 않으나 깃헙에 공개되어 있는 버전은 잘 동작하므로 이를 다운로드 받아 직접 설치할 필요가 있다.

#### Linux or Mac

직접 빌드하고자 하는 경우 python 헤더(Python.h)가 설치되어 있어야 합니다. `yum install python-devel` 혹은 배포판에 따라 이에 준하는 명령을 이용해 설치. gcc 가 없을 경우 gcc 도 설치해야 합니다.

```
git clone https://github.com/stania/pyjnius
cd pyjnius
python setup.py install
```

#### Windows

이디엄에서 빌드한 윈도우즈용 64비트 pyjnius는 다음 위치에서 다운로드 가능하다.

- [pyjnius for python 2.7, 64bit](http://staging.araqne.org/pyjnius-1.1.2_stania-py2.7-win-amd64.egg)
- [pyjnius for python 3.6, 64bit](http://staging.araqne.org/pyjnius-1.1.2_stania-py3.6-win-amd64.egg)

직접 pyjnius 빌드를 시도(`python setup.py bdist_egg`)하면 VC build tools 설치를 요구한다. 다음 위치를 방문하여 설치가 가능하다.

- python 2.7: http://www.microsoft.com/en-us/download/details.aspx?id=44266
- python 3.6: 
    - ~http://landinghub.visualstudio.com/visual-cpp-build-tools~
    - https://visualstudio.microsoft.com/ko/vs/older-downloads/ 
      하단의 *재배포 가능 패키지 및 빌드 도구*를 선택하고 *Microsoft Built Tools 2015 업데이트 3*을 선택하여 설치
    - 인스톨러 안에서 VC++ 빌드 도구 선택
    - v14.0 관련 툴을 추가로 우측에서 선택하여 설치 후 bdist_egg 재시도

## 직접 빌드하기

#### python 3 
```
python setup.py download
python setup.py bdist_egg
easy_install dist/logpresso-1.0.0-py3.6.egg
```

#### python 2
```
python setup.py download
python setup.py bdist_egg
easy_install dist/logpresso-1.0.0-py2.7.egg
```

## 실행 예제

### test_client.py
```
import jnius_config
jnius_config.add_options('-Xmx512m')
from logpresso import LogpressoClient
import time

with LogpressoClient('localhost', 8888, 'USER', 'PASSWORD') as client:
    query = 'table limit=10 sys_cpu_logs | eval arr = array(double(idle), string(kernel), user)'
    with client.query(query) as cursor:
        for row in cursor:
            print(row._id, row._table, time.strftime("%Y-%m-%d %H:%M:%S", row._time),
                  dict(row.data()), (row.idle, row.kernel, row.user))

    row = {'col1': 'val1', 'col2': -1, 'col3': [-0.25, 0, 0.25], 'col4': np.arange(3), 'col5': np.random.rand(3)}
    for i in range(5):
        row['id'] = i
        f = client.insert('python_insert', row)
    # must wait for completion of last insert
    client.await(1000)
```

### *nix bash
```
export JAVA_HOME=/usr/java/latest
python test_client.py
```

### Windows
```
set JAVA_HOME=C:\Java\jdk1.8.0_171
set PATH=%JAVA_HOME%\jre\bin\server;%PATH%
python test_client.py
```

----
----
아래의 내용은 outdate 상태이지만 기록을 위해 남겨둠

## Django 웹 프레임워크 로그 수집 설정 예시
settings.py 파일에 아래의 로깅 설정을 추가합니다.
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'logpresso': {
            'level': 'DEBUG',
            'class': 'logpresso.logging.LogpressoHandler',
            'formatter': 'verbose',
            'transport': 'tcp',
            'host': '127.0.0.1',
            'port': 5140,
            'max_count': 20000
            },
    'loggers': {
        'django.request': {
            'handlers': ['logpresso'],
            'level': 'DEBUG',
            'propagate': True,
            },
        }
    }
```
