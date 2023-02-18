#!/usr/bin/env python

'''
    nrepl.bencode
    -------------
    This module provides BEncode-protocol support.
    :copyright: (c) 2013 by Chas Emerick.
    :license: MIT, see LICENSE for more details.
'''


from io import StringIO, BytesIO
import array, numbers, sys
from io import BytesIO

def _read_byte(s):
    return s.read(1)

def _read_int(s, terminator=None, init_data=None):
    int_chrs = init_data or []
    while True:
        c = _read_byte(s)
        if not (c.isdigit() or c == b'-') or c == terminator or not c:
            break
        else:
            int_chrs.append(c)
    return int(b''.join(int_chrs))


def _read_bytes(s, n):
    data = BytesIO()
    cnt = 0
    while cnt < n:
        m = s.read(n - cnt)
        if not m:
            raise Exception("Invalid bytestring, unexpected end of input.")
        data.write(m)
        cnt += len(m)
    data.flush()
    # Taking into account that Python3 can't decode strings
    try:
        ret = data.getvalue().decode("UTF-8")
    except AttributeError:
        ret = data.getvalue()
    return ret


def _read_delimiter(s):
    d = _read_byte(s)
    if d.isdigit():
        d = _read_int(s, ":", [d])
    return d


def _read_list(s):
    data = []
    while True:
        datum = _read_datum(s)
        if datum is None:
            break
        data.append(datum)
    return data


def _read_map(s):
    i = iter(_read_list(s))
    return dict(zip(i, i))


_read_fns = {b"i": _read_int,
             b"l": _read_list,
             b"d": _read_map,
             b"e": lambda _: None,
             # EOF
             None: lambda _: None}


def _read_datum(s):
    delim = _read_delimiter(s)
    if delim != b'':
        return _read_fns.get(delim, lambda s: _read_bytes(s, delim))(s)


def _write_datum(x, out):
    if isinstance(x, (str, bytes)):
        # x = x.encode("UTF-8")
        # TODO revisit encodings, this is surely not right. Python
        # (2.x, anyway) conflates bytes and strings, but 3.x does not...
        out.write(str(len(x.encode('utf-8'))).encode('utf-8'))
        out.write(b":")
        out.write(x.encode('utf-8'))
    elif isinstance(x, numbers.Integral):
        out.write(b"i")
        out.write(str(x).encode('utf-8'))
        out.write(b"e")
    elif isinstance(x, (list, tuple)):
        out.write(b"l")
        for v in x:
            _write_datum(v, out)
        out.write(b"e")
    elif isinstance(x, dict):
        out.write(b"d")
        for k, v in x.items():
            _write_datum(k, out)
            _write_datum(v, out)
        out.write(b"e")
    out.flush()


def encode(v):
    "bencodes the given value, may be a string, integer, list, or dict."
    s = BytesIO()
    _write_datum(v, s)
    return s.getvalue().decode('utf-8')


def decode_file(file):
    while True:
        x = _read_datum(file)
        if x is None:
            break
        yield x


def decode(string):
    "Generator that yields decoded values from the input string."
    return decode_file(BytesIO(string.encode('utf-8')))


class BencodeIO(object):
    def __init__(self, file, on_close=None):
        self._file = file
        self._on_close = on_close

    def read(self):
        return _read_datum(self._file)

    def __iter__(self):
        return self

    def next(self):
        v = self.read()
        if not v:
            raise StopIteration
        return v

    def __next__(self):
        # In Python3, __next__ it is an own special class.
        v = self.read()
        if not v:
            raise StopIteration
        return v

    def write(self, v):
        return _write_datum(v, self._file)

    def flush(self):
        if self._file.flush:
            self._file.flush()

    def close(self):
        # Run the on_close handler if one exists, which can do something
        # useful like cleanly close a socket. (Note that .close() on a
        # socket.makefile('rw') does some kind of unclean close.)
        if self._on_close is not None:
            self._on_close()
        else:
            self._file.close()

if __name__ == '__main__':
    import json, socket, threading
    conn = socket.create_connection(("localhost", 5555))

    def read_loop(conn):
        while msg := conn.recv(4096):
            payload = msg.decode()
            parsed = next(decode(payload))
            cs_common.debug("RCV", json.dumps(parsed))
    threading.Thread(daemon=True, target=read_loop, args=(conn,)).start()

    for line in sys.stdin:
        try:
            parsed = json.loads(line)
            encoded = encode(parsed)
            # print("SND RAW", encoded.encode())
            conn.sendall(encoded.encode())
        except json.JSONDecodeError:
            print("Not a valid JSON")
