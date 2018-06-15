import logging
import socket
import os
import sys
import struct
import threading
import time
from os.path import isfile, join
from datetime import datetime
from time import strftime

import traceback

def ensure_close(f):
  if f is not None:
    f.close()

class TcpSender(threading.Thread):
  def __init__(self, host, port, path):
    threading.Thread.__init__(self)
    self.do_stop = False
    self.host = host
    self.port = port
    self.path = path
    self.sock = None

  def run(self):
    self.do_stop = False
    while True:
      time.sleep(0.5)
      if self.do_stop:
        break

      try:
        self.send_logs(self.path)
      except:
        ensure_close(self.sock)
        self.sock = None
        pass

    ensure_close(self.sock)

  def is_logfile(self, dir_path, filename):
    return True if isfile(join(dir_path, filename)) and filename.endswith('.log') else False

  def get_logfiles(self, dir_path):
    files = [f for f in os.listdir(dir_path) if self.is_logfile(dir_path, f)]
    return files

  def send_logs(self, dir_path):
    if self.sock is None:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self.sock.connect((self.host, self.port))

    files = self.get_logfiles(dir_path)

    file_count = len(files)

    i = 0
    idx_pos = 0
    log_pos = 0
    idx_offset = 0
    log_offset = 0
    last_filename = None

    try:
      last_state = self.load_last_state()
      if last_state is not None:
        (last_filename, idx_offset, log_offset) = last_state

      for filename in files:
        log_path = join(dir_path, filename)
        idx_path = log_path[:log_path.rfind('.')] + '.idx'

        if not os.path.exists(idx_path):
          continue

        if not os.path.exists(log_path):
          continue

        (idx_pos, log_pos) = self.load_file(idx_path, log_path, idx_offset, log_offset)
        idx_offset = 0
        log_offset = 0

        # delete sent files except last one
        if i < file_count - 1:
          os.remove(log_path)
          os.remove(idx_path)

        last_filename = filename
        i += 1

    finally:
      if last_filename is not None:
        self.save_last_state(last_filename, idx_pos, log_pos)

  def load_file(self, idx_path, log_path, idx_offset, log_offset):

    idx_file = None
    log_file = None
    idx_pos = 0
    log_pos = 0

    try:
      idx_file = open(idx_path, 'rb')
      log_file = open(log_path, 'rb')

      if idx_offset > 0:
        idx_file.seek(idx_offset)

      if log_offset > 0:
        log_file.seek(log_offset)

      idx_pos = idx_file.tell()
      log_pos = log_file.tell()
    
      while True:
        b = idx_file.read(1)
        if (b == ''):
          break

        next_len = ord(b)
        chars = log_file.read(next_len)

        self.sock.sendall(chars)

        idx_pos += 1
        log_pos += next_len

    except:
      ensure_close(self.sock)
      self.sock = None
      raise

    finally:
      ensure_close(idx_file)
      ensure_close(log_file)
      return (idx_pos, log_pos)

  def load_last_state(self):
    state_path = join(self.path, 'logpresso.pos')
    f = None
    try:
      if not os.path.exists(state_path):
        return None

      f = open(state_path, 'r')
      lines = f.readlines()
      if len(lines) < 3:
        return None

      filename = lines[0]
      idx_pos = long(lines[1])
      log_pos = long(lines[2])
      return (filename, idx_pos, log_pos)

    finally:
      ensure_close(f)

  def save_last_state(self, filename, idx_pos, log_pos):
    state_path = join(self.path, 'logpresso.pos')
    f = None
    try:
      # ensure directory exists
      if not os.path.exists(self.path):
        os.makedirs(self.path)

      f = open(state_path, 'w')
      f.write(filename + '\n')
      f.write(str(idx_pos) + '\n')
      f.write(str(log_pos) + '\n')

    finally:
      ensure_close(f)

class LogpressoHandler(logging.StreamHandler):
  def __init__(self, transport='tcp', host=None, port=514, path='/root/mysite/log/', max_count=None, max_bytes=None):
    logging.StreamHandler.__init__(self)
    self.transport = transport
    self.host = host
    self.port = port
    self.path = path
    self.max_count = max_count
    self.max_bytes = max_bytes
    self.level = logging.DEBUG
    self.total_count = 0
    self.total_bytes = 0

    if self.transport == 'tcp':
      if (path is None):
        raise Exception('path is required for tcp transport')

      if not self.path.endswith('/'):
        self.path = self.path + '/'

      filename = datetime.now().strftime('%Y%m%d_%H%M%S.%f')
      self.logfile = open(path + filename + '.log', 'a')
      self.idxfile = open(path + filename + '.idx', 'a')

      self.tcp_sender = TcpSender(host, port, path)
      self.tcp_sender.start()

    elif self.transport == 'udp':
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  def close(self):
    self.tcp_sender.do_stop = True
    ensure_close(self.logfile)
    ensure_close(self.idxfile)
    ensure_close(self.sock)

  def emit(self, record):
    msg = self.format(record)
    if (self.transport == 'tcp'):
      self.write_file(msg)
      if self.max_count is not None and self.max_count <= self.total_count:
        self.reopen_files()

      if self.max_bytes is not None and self.max_bytes <= self.total_bytes:
        self.reopen_fiels()

    elif (self.transport == 'udp'):
      self.send_syslog(msg)

  def reopen_files(self):
    ensure_close(self.logfile)
    ensure_close(self.idxfile)

    filename = datetime.now().strftime('%Y%m%d_%H%M%S.%f')
    self.logfile = open(self.path + filename + '.log', 'a')
    self.idxfile = open(self.path + filename + '.idx', 'a')

    self.total_count = 0
    self.total_bytes = 0

  def write_file(self, msg):
    line = msg + '\n'
    encoded = line.encode('utf-8')
    encoded_len = len(encoded)

    self.logfile.write(encoded)
    self.logfile.flush()
    self.idxfile.write(self.int_to_bytes(encoded_len))
    self.idxfile.flush()

    self.total_count += 1
    self.total_bytes += encoded_len

  def int_to_bytes(self, n):
    num_bytes = 0
    if n <= 127:
      num_bytes = 1
    elif n <= 16383:
      num_bytes = 2
    elif n <= 2097151:
      num_bytes = 3
    else:
      raise Exception('log record is too long: ' + n)

    b = struct.pack('>I', n)
    raw = []
    for i in range(0, num_bytes):
      signal_bit = (0x80 if i != num_bytes - 1 else 0)
      v = (signal_bit | (n >> (7 * (num_bytes - i - 1)) & 0x7f))
      raw.append(v)

    return bytearray(raw)

  def send_syslog(self, msg):
    self.sock.sendto(msg, (self.host, self.port))


