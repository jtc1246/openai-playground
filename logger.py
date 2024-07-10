import os
from queue import Queue
from time import time
from _thread import start_new_thread
import json


LOG_BASE_PATH = ''
log_file = None


log_queue = Queue()


__all__ = ['set_base_path', 'write_raw_api_responses', 'write_chat_completions_api', 'write_chat_error', 'write_plain_text', 'write_config_log', 'write_get_log', 'write_post_illegal', 'write_post_raw']


def set_base_path(p: str):
    global LOG_BASE_PATH, log_file
    LOG_BASE_PATH = p
    log_file = open(p + '/playground_logs.txt', 'a')
    log_file.write('\n\n')
    start_new_thread(write_queue, (log_queue, log_file))
    log_queue.put('Server started')


def write_raw_api_responses(stream_id: str, data: bytes, index: int):
    try:
        data = data.decode('utf-8')
        data = str([data])
    except:
        data = str(data)
    index = str(index)
    index = index + ' ' * (5 - len(index))
    content = 'RAW_RESP' + ',  ' + stream_id + '  ' + index + ' ' + data
    log_queue.put(content)


def write_chat_completions_api(stream_id: str, data: str, request_model: str, used_model: str, base_url: str):
    # later part contains more information
    if (len(request_model) > 30):
        request_model = request_model[-30:]
    if (len(used_model) > 30):
        used_model = used_model[-30:]
    request_model = request_model + ' ' * (30 - len(request_model))
    used_model = used_model + ' ' * (30 - len(used_model))
    content = 'CHAT_API' + ',  ' + stream_id + '  R:' + request_model + '  U:' + used_model + '  ' + data + '  ' + base_url
    log_queue.put(content)


def write_chat_error(stream_id: str, data: str, status: int):
    status = str(status)
    status = status + ' ' * (3 - len(status))
    content = 'CHAT_ERR' + ',  ' + stream_id + '  ' + status + '  ' + data
    log_queue.put(content) 


def write_plain_text(data: str):
    content = 'PLN_TEXT' + ',  ' + data
    log_queue.put(content)


def write_config_log(data: str):
    content = 'CONFIG_' + ',  ' + data
    log_queue.put(content)


def write_get_log(path, ip, header, status):
    status = str(status)
    status = status + ' ' * (3 - len(status))
    ip = ip + ' ' * (15 - len(ip))
    path = path + ' ' * (50 - len(path))
    content = 'HTTP_GET' + ',  ' + path + '  ' + status + '  ' + ip + '  ' + json.dumps(header, ensure_ascii=False)
    log_queue.put(content)


def write_post_header(path: str, ip, header, desc):
    '''
    This is only for wrong path or password, wrong model name doesn't belong to this
    '''
    desc = desc + ' ' * (20 - len(desc))
    ip = ip + ' ' * (15 - len(ip))
    path = path + ' ' * (50 - len(path))
    content = 'POST_HDR,  ' + desc + '  ' + path + '  ' + ip + '  ' + json.dumps(header, ensure_ascii=False)
    log_queue.put(content)


def write_post_raw(path: str, ip: str, header: str, data: bytes, stream_id: str):
    try:
        data = data.decode('utf-8')
        data = str([data])
    except:
        data = str(data)
    ip = ip + ' ' * (15 - len(ip))
    path = path + ' ' * (50 - len(path))
    content = 'POST_RAW' + ',  ' + stream_id + '  ' + path + '  ' + ip + '  ' + json.dumps(header, ensure_ascii=False) + '  ' + data # bytes
    log_queue.put(content)


# def write


def write_queue(q: Queue, file):
    while True:
        content = q.get()
        t = "{:.3f}".format(time() * 1000)
        content = t + ':  ' + content + '\n'
        file.write(content)
        file.flush()


