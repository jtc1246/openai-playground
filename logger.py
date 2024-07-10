import os
from queue import Queue
from time import time
from _thread import start_new_thread


LOG_BASE_PATH = ''
log_file = None


log_queue = Queue()


__all__ = ['set_base_path', 'write_raw_api_responses']


def set_base_path(p: str):
    global LOG_BASE_PATH, log_file
    LOG_BASE_PATH = p
    log_file = open(p + '/playground_logs.txt', 'a')
    log_file.write('\n\n')
    start_new_thread(write_queue, (log_queue, log_file))
    log_queue.put('Server started')


def write_raw_api_responses(stream_id: str, data: bytes, index: int):
    index = str(index)
    index = index + ' ' * (5 - len(index))
    content = 'RAW_RESP' + ',  ' + stream_id + '  ' + index + ' ' + str(data)
    log_queue.put(content)


def write_chat_completions_api(stream_id: str, data: str, request_model: str, used_model: str, base_url: str):
    # later part contains more information
    if (len(request_model) > 30):
        request_model = request_model[-30:]
    if (len(used_model) > 30):
        used_model = used_model[-30:]
    request_model = request_model + ' ' * (30 - len(request_model))
    used_model = used_model + ' ' * (30 - len(used_model))
    content = 'CHAT_API' + ',  ' + stream_id + '  R:' + request_model + '  U:' + used_model + '  ' + data
    log_queue.put(content)


def write_queue(q: Queue, file):
    while True:
        content = q.get()
        t = "{:.3f}".format(time() * 1000)
        content = t + ':  ' + content + '\n'
        file.write(content)
        file.flush()


