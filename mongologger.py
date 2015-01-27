"""
https://gist.github.com/kesor/1589672
"""
__version__ = '0.1'

import logging
import time
import struct

from pymongo.connection import Connection
import bson
from bson.errors import InvalidBSON


logger = logging.getLogger('mongologger')


def create_logger():
    """
    """
    if not logger.isEnabledFor('info'):
        return
    # monkey-patch methods to record messages
    Connection._send_message = _instrument(Connection._send_message)
    Connection._send_message_with_response = _instrument(Connection._send_message_with_response)


def _instrument(original_method):

    def instrumented_method(*args, **kwargs):
        message = decode_wire_protocol(args[1][1])
        # if message['msg_id'] in self._used_msg_ids:
        # return original_method(*args, **kwargs)
        # self._used_msg_ids.append(message['msg_id'])
        start = time.time()
        result = original_method(*args, **kwargs)
        logger.info('%.3f %s', message, time.time() - start)
        return result

    return instrumented_method


MONGO_OPS = {
    2001: 'msg',
    2002: 'insert',
    2003: 'reserved',
    2004: 'query',
    2005: 'get_more',
    2006: 'delete',
    2007: 'kill_cursors',
}


def decode_wire_protocol(message):
    """ http://www.mongodb.org/display/DOCS/Mongo+Wire+Protocol """
    _, msg_id, _, opcode, _ = struct.unpack('<iiiii', message[:20])
    op = MONGO_OPS.get(opcode, 'unknown')
    zidx = 20
    collection_name_size = message[zidx:].find('\0')
    collection_name = message[zidx:zidx + collection_name_size]
    zidx += collection_name_size + 1
    skip, limit = struct.unpack('<ii', message[zidx:zidx + 8])
    zidx += 8
    try:
        msg = bson.decode_all(message[zidx:])
    except InvalidBSON:
        msg = 'invalid bson'
    return {
        'op': op, 'collection': collection_name, 'msg_id': msg_id, 'skip': skip, 'limit': limit,
        'query': msg,
    }
