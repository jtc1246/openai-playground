import os
from queue import Queue
from time import time
from _thread import start_new_thread
import json
import sqlite3
from threading import Lock


LOG_BASE_PATH = ''
log_file = None
database = None


log_queue = Queue()
database_lock = Lock()


__all__ = ['set_base_path', 'write_raw_api_responses', 'write_chat_completions_api',
           'write_chat_error', 'write_plain_text', 'write_config_log', 'write_get_log', 
           'write_post_header', 'write_post_raw', 'write_plain_response',
           'add_request', 'extract_all_requests',
           'extract_all_responses', 'add_response', 'update_response', 'set_token_usage']


def set_base_path(p: str):
    global LOG_BASE_PATH, log_file, database
    LOG_BASE_PATH = p
    log_file = open(p + '/playground_logs.txt', 'a')
    log_file.write('\n\n')
    start_new_thread(write_queue, (log_queue, log_file))
    log_queue.put('Server started')
    database = sqlite3.connect(p + '/playground_database.sqlite3', check_same_thread=False)
    # time is in microsecond, all times after this are in microsecond
    database.execute('''
        Create Table If Not Exists All_Requests (
            id Char(64) Primary Key,
            data Text Not Null,
            time Integer Not Null,
            has_response Boolean Not Null,
            user_model_name Text Not Null,
            origin_model_name Text Not Null
        );
                     ''')
    # start time is the time of receiving first response
    database.execute('''
        Create Table If Not Exists All_Responses (
            id Char(64) Primary Key,
            data Text Not Null,
            start_time Integer Not Null,
            last_update_time Integer Not Null,
            ended Boolean Not Null,
            in_tokens Integer,
            out_tokens Integer
        );
                     ''')
    database.commit()


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
    content = 'CONFIG__' + ',  ' + data
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


def write_plain_response(stream_id:str, data: str, index: int):
    index = str(index)
    index = index + ' ' * (5 - len(index))
    content = "PURE_RSP,  " + stream_id + '  ' + index + ' ' + data
    log_queue.put(content)


# def write


def write_queue(q: Queue, file):
    while True:
        content = q.get()
        t = "{:.3f}".format(time() * 1000)
        content = t + ':  ' + content + '\n'
        file.write(content)
        file.flush()


def add_request(full_id: str, data, user_model_name: str, origin_model_name: str):
    if(type(data) != str):
        data = json.dumps(data, ensure_ascii=False)
    t = int(round(time()*1000000))
    database_lock.acquire()
    database.execute('''
        Insert Into All_Requests (id, data, time, has_response, user_model_name, origin_model_name)
        Values (?, ?, ?, ?, ?, ?);
                     ''', (full_id, data, t, False, user_model_name, origin_model_name))
    database.commit()
    database_lock.release()


def set_has_response(full_id: str):
    database.execute('''
        Update All_Requests
        Set has_response = True
        Where id = ?;
                     ''', (full_id,))
    # database.commit() # don't need to commit here, need to commit once with add_response


def extract_all_requests():
    cursor = database.execute('''
        Select *
        From All_Requests;
                             ''')
    result = cursor.fetchall()
    my_results = []
    for r in result:
        my_results.append(list(r))
        my_results[-1][3] = bool(my_results[-1][3])
    return my_results


def extract_all_responses():
    cursor = database.execute('''
        Select *
        From All_Responses;
                             ''')
    result = cursor.fetchall()
    my_results = []
    for r in result:
        my_results.append(list(r))
        my_results[-1][4] = bool(my_results[-1][4])
    return my_results


def add_response(full_id:str, data:str):
    t = int(round(time()*1000000))
    database_lock.acquire()
    database.execute('''
        Insert Into All_Responses (id, data, start_time, last_update_time, ended)
        Values (?, ?, ?, ?, ?);
                     ''', (full_id, data, t, t, False))
    set_has_response(full_id)
    database.commit()
    database_lock.release()
    

def update_response(full_id: str, data: str):
    t = int(round(time()*1000000))
    database_lock.acquire()
    database.execute('''
        Update All_Responses
        Set data = ?, last_update_time = ?
        Where id = ?;
                     ''', (data, t, full_id))
    database.commit()
    database_lock.release()


def set_token_usage(full_id: str, in_tokens: int = None, out_tokens: int = None):
    t = int(round(time()*1000000))
    database_lock.acquire()
    database.execute('''
        Update All_Responses
        Set in_tokens = ?, out_tokens = ?, last_update_time = ?, ended = True
        Where id = ?;
                     ''', (in_tokens, out_tokens, t, full_id))
    database.commit()
    database_lock.release()


if __name__ == '__main__':
    database = sqlite3.connect('playground_logs/playground_database.sqlite3', check_same_thread=False)
    # time 是 微秒, 之后所有的时间都是微秒
    database.execute('''
        Create Table If Not Exists All_Requests (
            id Char(64) Primary Key,
            data Text Not Null,
            time Integer Not Null,
            has_response Boolean Not Null,
            user_model_name Text Not Null,
            origin_model_name Text Not Null
        );
                     ''')
    database.execute('''
        Create Table If Not Exists All_Responses (
            id Char(64) Primary Key,
            data Text Not Null,
            start_time Integer Not Null,
            last_update_time Integer Not Null,
            ended Boolean Not Null,
            in_tokens Integer,
            out_tokens Integer
        );
                     ''')
    database.commit()
    print(extract_all_requests())
    print(extract_all_responses())

