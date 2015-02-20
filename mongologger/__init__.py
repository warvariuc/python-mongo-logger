"""
Based on: https://gist.github.com/kesor/1589672
"""
from ._version import __version__

import logging
import time
import struct
import json
import datetime
import traceback
import inspect

from pymongo.mongo_client import MongoClient
import bson
from bson.errors import InvalidBSON


logger = logging.getLogger('mongologger')


def create_logger(until_modules=('pymongo', 'mongoengine'), stack_size=3):
    """Create and activate the Mongo-Logger.
    Args:
        modules (list): list of top level module names until which the stack should be shown;
          pass an empty sequence to show the whole stack
        stack_size (int): how many frames before any of `modules` was entered to show; pass
          -1 to show the whole stack or 0 to show no stack
    """
    if not logger.isEnabledFor('info'):
        return
    # monkey-patch methods to record messages
    MongoClient._send_message = _instrument(MongoClient._send_message, until_modules, stack_size)
    MongoClient._send_message_with_response = _instrument(MongoClient._send_message_with_response,
                                                          until_modules, stack_size)
    return logger


def _instrument(original_method, until_modules, stack_size):
    """Monkey-patch the given pymongo function which sends queries to MongoDB.
    """
    def instrumented_method(*args, **kwargs):
        start_time = time.time()
        result = original_method(*args, **kwargs)
        duration = time.time() - start_time
        try:
            message = decode_wire_protocol(args[1][1])
            stack = ('\n' + ''.join(get_stack(until_modules, stack_size))).rstrip()
            logger.info('%.3f %s %s %s%s', duration, message['op'], message['collection'],
                        json.dumps(message['query'], cls=JSONEncoder), stack)
        except Exception as exc:
            logger.info('%.3f *** Failed to log the query *** %s', duration, exc)
        return result

    return instrumented_method


def get_stack(until_modules, stack_size):
    """
    """
    frames = inspect.stack()[2:]
    frame_index = None
    for i, (frame, _, _, _, _, _) in enumerate(frames):
        module_name, _, _ = frame.f_globals['__name__'].partition('.')
        if module_name in until_modules:
            frame_index = i
        elif frame_index is not None:
            # found first frame before the needed module frame was entered
            break
        
    if frame_index is not None:
        del frames[:frame_index + 1]
        if stack_size >= 0:
            del frames[stack_size:]

    stack = [(filename, lineno, name, lines[0])
             for frame, filename, lineno, name, lines, _ in frames]

    return traceback.format_list(stack)


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


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.time)):
            return o.isoformat()
        elif isinstance(o, bson.ObjectId):
            return str(o)
        return super(JSONEncoder, self).default(o)
