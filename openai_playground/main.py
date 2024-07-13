from typing import Any
from myHttp import http
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import time, sleep
from _thread import start_new_thread
from .utils import endode_js, encode_engines, encode_v1_models,\
                  get_models_from_url, get_models_from_url_ollama,\
                  get_hash, handle_stream_data, handle_log_queue,\
                  generate_models_log, star_api_key
from mySecrets import hexToStr
import json
import requests
from random import randint
from queue import Queue
import os
from .logger import write_chat_completions_api, set_base_path, write_raw_api_responses,\
                   write_chat_error, write_plain_text, write_get_log, write_post_header,\
                   write_post_raw, write_config_log, add_request, extract_all_requests,\
                   extract_all_responses

__all__ = ['create_server', 'start_server_async',
           'add_model', 'add_models', 'add_ollama_model', 'add_ollama_models'
           'add_zhipu_doubao', 'export_data']

PASSWORD = ''

JS_URL = 'https://openaiapi-site.azureedge.net/public-assets/d/ddd16bc977/static/js/main.600c2350.js'

JS_CONTENT = ''
PORT = 0
DATA_DIR = ''

def init():
    global JS_CONTENT
    tmp = http(JS_URL, ToJson=False)
    if(tmp['status'] < 0 or tmp['code'] != 200):
        print('Failed to fetch JS file')
        raise Exception('Failed to fetch JS file')
    JS_CONTENT = tmp['text']
    write_plain_text('JS file loaded successfully.')
    # currently don't need to encode according model list, so just pre generate
    JS_CONTENT = endode_js(JS_CONTENT)


models = []
model_info = {} # {name: (base_url, api_key, origin_name, is_ollama:bool)}


class Request(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_GET(self):
        path=self.path
        print(path)
        if(path not in ['/v1/models','/v1/engines', '/600c2350.js']
           and  not path.startswith('/v1/login/')):
            write_get_log(path, self.client_address[0], dict(self.headers), 404)
            self.send_response(404)
            self.send_header('Content-Length', 0)
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.flush()
            return
        if path == '/v1/models':
            write_get_log(path, self.client_address[0], dict(self.headers), 200)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'keep-alive')
            data = encode_v1_models(models).encode('utf-8')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        if path == '/v1/engines':
            write_get_log(path, self.client_address[0], dict(self.headers), 200)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'keep-alive')
            data = encode_engines(models).encode('utf-8')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        if path.startswith('/v1/login/'):
            path = path[len('/v1/login/'):]
            try:
                password = hexToStr(path)
            except:
                password = ''
            if(password != PASSWORD):
                print('login denied')
                write_get_log(self.path, self.client_address[0], dict(self.headers), 401)
                self.send_response(401)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Content-Length', 2)
                self.end_headers()
                self.wfile.write(b'{}')
                self.wfile.flush()
                return
            print('login approved')
            write_get_log(self.path, self.client_address[0], dict(self.headers), 200)
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Length', 2)
            self.end_headers()
            self.wfile.write(b'{}')
            self.wfile.flush()
            return
        if path == '/600c2350.js':
            write_get_log(path, self.client_address[0], dict(self.headers), 200)
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Connection', 'keep-alive')
            js = JS_CONTENT # currently don't need to encode according model list
            js = js.encode('utf-8')
            self.send_header('Content-Length', len(js))
            self.send_header
            self.end_headers()
            self.wfile.write(js)
            self.wfile.flush()
            return
        
    def do_POST(self):
        path = self.path
        print(path)
        # return 404 for incorrect url
        if(not path.startswith('/v1/chat/completions/')):
            write_post_header(path, self.client_address[0], dict(self.headers), 'Incorrect url')
            self.send_response(404)
            self.send_header('Content-Length', 0)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.flush()
            return
        pw = path[len('/v1/chat/completions/'):]
        try:
            pw = hexToStr(pw)
        except:
            pw = ''
        # password incorrect
        if(pw != PASSWORD):
            write_post_header(path, self.client_address[0], dict(self.headers), 'Password incorrect')
            self.send_response(404)
            data = {
                "error": {
                    "message": "Not logged in, please refresh the page and input password again.", 
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None
                }
            }
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        write_post_header(path, self.client_address[0], dict(self.headers), 'Login success')
        body = self.rfile.read(int(self.headers['Content-Length']))
        stream_id = get_hash(str(time()) + str(randint(0, 10000000000)) + str(body))
        full_id = stream_id
        stream_id = stream_id[-12:]
        write_post_raw(path, self.client_address[0], dict(self.headers), body, stream_id)
        body = json.loads(body)
        model_name = body['model']
        # model not found
        if(model_name not in models):
            write_plain_text(f'{stream_id}  Model {model_name} not found in {models}.')
            print(f'Model {model_name} not found.')
            self.send_response(404)
            data = {
                "error": {
                    "message": f"No model named {model_name}.", 
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None
                }
            }
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        print(body)
        # set url
        base_url = model_info[model_name][0]
        api_key = model_info[model_name][1]
        origin_name = model_info[model_name][2]
        is_ollama = model_info[model_name][3]
        if(is_ollama):
            url = base_url + '/v1/chat/completions'
        else:
            url = base_url + '/chat/completions'
        body['model'] = origin_name
        # update json data, change to old version
        for i in range(len(body['messages'])-1, -1, -1):
            if(len(body['messages'][i]['content']) == 0):
                body['messages'].pop(i)
                continue
            if(len(body['messages'][i]['content'])>1 or body['messages'][i]['content'][0]['type'] != 'text'):
                write_plain_text(f'{stream_id}  Unsupported type of message received.')
                print('Unsupported type of message received.')
                self.send_response(404)
                data = {
                    "error": {
                        "message": "Image and other type of message is not supported.", 
                        "type": "invalid_request_error",
                        "param": None,
                        "code": None
                    }
                }
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                self.send_header('Content-Length', len(data))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                self.wfile.write(data)
                self.wfile.flush()
                return
            body['messages'][i]['content'] = body['messages'][i]['content'][0]['text']
        write_chat_completions_api(stream_id, json.dumps(body,ensure_ascii=False), model_name, origin_name, url)
        body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        header = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Content-Length': str(len(body)),
        }
        add_request(full_id, body.decode('utf-8'), model_name, origin_name)
        resp = requests.post(url, headers=header, data=body, stream=True)
        # success, in transfer-encoding chunked mode
        if(resp.status_code == 200 and resp.headers.get('Transfer-Encoding') == 'chunked'):
            # use stream here
            client_queue = Queue() # sent to client
            log_queue = Queue() # for logs
            start_new_thread(handle_stream_data, (self, client_queue))
            start_new_thread(handle_log_queue, (log_queue, stream_id, full_id))
            for chunk in resp.iter_content(chunk_size=None):
                client_queue.put(chunk)
                log_queue.put(chunk)
            print("stream ended")
            client_queue.put(False)
            log_queue.put(False)
            return
        else:
            # error handling, don't use stream
            s = resp.status_code
            data = resp.content
            # special case for cohere, https://github.com/missuo/cohere2openai
            # it will not have transfer-encoding chunked if response is too short.
            if(b'data: [DONE]' in data):
                # write_raw_api_responses(stream_id, data, 0)
                # write_raw_api_responses(stream_id, "END OF RESPONSE", 1)
                # self.send_response(200)
                # self.send_header('Transfer-Encoding', 'chunked')
                # self.send_header('Access-Control-Allow-Origin', '*')
                # self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                # self.send_header('Connection', 'keep-alive')
                # self.end_headers()
                # self.wfile.write(f'{len(data):X}'.encode('utf-8'))
                # self.wfile.write(b'\r\n')
                # self.wfile.write(data)
                # self.wfile.write(b'\r\n')
                # self.wfile.write(b'0\r\n\r\n')
                # self.wfile.flush()
                client_queue = Queue() # sent to client
                log_queue = Queue() # for logs
                start_new_thread(handle_stream_data, (self, client_queue))
                start_new_thread(handle_log_queue, (log_queue, stream_id, full_id))
                log_queue.put(data)
                client_queue.put(data)
                print("stream ended")
                client_queue.put(False)
                log_queue.put(False)
                return
            # put http status and error msg from that service in error message, as detailed as possible
            # also give some hint in some case
            try:
                data = data.decode('utf-8')
            except:
                data = str(data)[2:-1]
            write_chat_error(stream_id, data, s)
            msg = f'Error: http status {s}. Error message from {url}: {data}'
            # special case for cohere
            if(s == 200):
                msg += ' This means an error occurred, but that service doesn\'t provide error message, and \
                    has status 200. But this is an error, may due to invalid api key.'
            # for zhipu
            if('"code":"1210"' in msg):
                msg += ' 这个错误来自智谱AI, 原因大概率是 temperature 和 top_p 设置不当。请注意, 智谱AI要求 temperature 和 top_p 都是 严格大于0, 严格小于1。'
            data = {
                "error": {
                    "message": msg, 
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None
                }
            }
            self.send_response(404)
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Content-Length', 0)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'openai-organization,content-type,authorization')
        self.end_headers()
        self.wfile.flush()
    
    def log_message(self, *args) -> None:
        pass
    
    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass


init()


def create_server(port:int, password:str, data_dir:str='./playground_logs') -> None:
    '''
    Create the playground server. Just create, will not start. You need to add models to it and then call `start_server_async` later.
    
    Arguments:
    
    1. password: the password the needs to be input in the browser, for authorization
    2. data_dir: the directory to store the database and logs. Will create if not exists.
    '''
    global PORT, PASSWORD
    if(port <=0 or port >=65536):
        raise ValueError('Invalid port number: ' + str(port))
    # PORT = port
    if(len(password) == 0):
        raise TypeError('Password cannot be empty.')
    PASSWORD = password
    if(data_dir.endswith('/')):
        data_dir = data_dir[:-1]
    os.makedirs(data_dir, exist_ok=True)
    set_base_path(data_dir)
    PORT = port
    write_config_log(f"Create server, with port {PORT} and password {PASSWORD}. Latest config: " + generate_models_log(model_info))

def add_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
    '''
    Add a model to the playground, need openai format API. Need to implement both `<base_url>/models` and `<base_url>/chat/completions`
    
    Arguments:
    
    1. base_url: should include `/v1` if it's openai, start with `http://` or `https://`. Either have or not have the last `/` is OK. E.g. for openai, it should be `https://api.openai.com/v1`. It will access `<base_url>/models` and `<base_url>/chat/completions`
    2. model_name: need to be exactly same as the name in your service
    3. new_name: the name you want to show in the playground, if not provided, will be same as model_name
    '''
    write_config_log(f"add_model: base_url: {base_url}, api_key: {star_api_key(api_key)}, model_name: {model_name}, new_name: {new_name}")
    if(not base_url.startswith('http://') and not base_url.startswith('https://')):
        raise ValueError('Invalid url. Url should start with http:// or https://')
    if(base_url[-1] == '/'):
        base_url = base_url[:-1]
    if(model_name == '' or new_name == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name == None):
        new_name = model_name
    if(model_name.replace(' ', '').replace('\n', '') == '' or new_name.replace(' ', '').replace('\n', '') == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name in models):
        raise ValueError(f'Model name {new_name} already exists.')
    all_models = get_models_from_url(base_url, api_key)
    if(model_name not in all_models):
        raise ValueError(f'No model called {model_name} from {base_url}. Available models: {all_models}')
    models.append(new_name)
    model_info[new_name] = (base_url, api_key, model_name, False)
    print(f'Model {new_name} added successfully.')
    write_config_log("Model added, latest config: " + generate_models_log(model_info))


def add_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
    '''
    Add a list of models to the playground, need openai format API. Need to implement both `<base_url>/models` and `<base_url>/chat/completions`. If models_ is empty, will add all available models.
    
    Arguments:
    
    1. base_url: should include `/v1` if it's openai, start with `http://` or `https://`. Either have or not have the last `/` is OK. E.g. for openai, it should be `https://api.openai.com/v1`. It will access `<base_url>/models` and `<base_url>/chat/completions`
    2. models_: a list of model names you want to add, model name should be exactly same as the name in your service. If it is an empty list, will add all available models.
    3. prefix and postfix: the name shown in the playground will be `prefix + model_name + postfix`
    '''
    write_config_log(f"add_models: base_url: {base_url}, api_key: {star_api_key(api_key)}, models_: {models_}, prefix: {prefix}, postfix: {postfix}")
    if(not base_url.startswith('http://') and not base_url.startswith('https://')):
        raise ValueError('Invalid url. Url should start with http:// or https://')
    if(base_url[-1] == '/'):
        base_url = base_url[:-1]
    # first check the model name legality
    if(len(set(models_)) != len(models_)):
        raise ValueError('Have duplicate model names.')
    for model_name in models_:
        if(model_name == ''):
            raise ValueError('Model name cannot be empty.')
        if(model_name.replace(' ', '').replace('\n', '') == ''):
            raise ValueError('Model name cannot be empty.')
        if((prefix + model_name + postfix) in models):
            raise ValueError(f'Model name {prefix + model_name + postfix} already exists.')
    all_models = get_models_from_url(base_url, api_key)
    if(len(models_) ==0):
        models_ = all_models
    for model_name in models_:
        if((prefix + model_name + postfix) in models):
            raise ValueError(f'Model name {prefix + model_name + postfix} already exists.')
    added_models = []
    missing_models = []
    for m in models_:
        if(m in all_models):
            added_models.append(prefix + m + postfix)
            models.append(prefix + m + postfix)
            model_info[prefix + m + postfix] = (base_url, api_key, m, False)
        else:
            missing_models.append(m)
    write_config_log("Model added, latest config: " + generate_models_log(model_info))
    if(len(missing_models) ==0):
        print(f'All models added successfully. {added_models}')
        return
    if(len(added_models) > 0):
        print(f'These models added successfully: {added_models}')
    print(f'These models not found: {missing_models} from {base_url}. Available models: {all_models}')
    raise Exception()


def add_ollama_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
    '''
    For ollama, if you don't know what ollama is, just ignore this function.
    
    Mostly same as `add_model`.
    
    For base_url, on default should end with :11434, no any other path. Just ends with port number (if you change the default port, port can be different)
    
    For api_key, it's not checked, but you must provide, even an empty str is OK.
    '''
    write_config_log(f"add_ollama_model: base_url: {base_url}, api_key: {star_api_key(api_key)}, model_name: {model_name}, new_name: {new_name}")
    if(not base_url.startswith('http://') and not base_url.startswith('https://')):
        raise ValueError('Invalid url. Url should start with http:// or https://')
    if(base_url[-1] == '/'):
        base_url = base_url[:-1]
    if(model_name == '' or new_name == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name == None):
        new_name = model_name
    if(model_name.replace(' ', '').replace('\n', '') == '' or new_name.replace(' ', '').replace('\n', '') == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name in models):
        raise ValueError(f'Model name {new_name} already exists.')
    all_models = get_models_from_url_ollama(base_url, api_key)
    if(model_name not in all_models):
        raise ValueError(f'No model called {model_name} from {base_url}. Available models: {all_models}')
    models.append(new_name)
    model_info[new_name] = (base_url, api_key, model_name, True)
    print(f'Model {new_name} added successfully.')
    write_config_log("Model added, latest config: " + generate_models_log(model_info))


def add_ollama_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
    '''
    For ollama, if you don't know what ollama is, just ignore this function.
    
    Mostly same as `add_models`.
    
    For base_url, on default should end with :11434, no any other path. Just ends with port number (if you change the default port, port can be different)
    
    For api_key, it's not checked, but you must provide, even an empty str is OK.
    '''
    write_config_log(f"add_ollama_models: base_url: {base_url}, api_key: {star_api_key(api_key)}, models_: {models_}, prefix: {prefix}, postfix: {postfix}")
    if(not base_url.startswith('http://') and not base_url.startswith('https://')):
        raise ValueError('Invalid url. Url should start with http:// or https://')
    if(base_url[-1] == '/'):
        base_url = base_url[:-1]
    # first check the model name legality
    if(len(set(models_)) != len(models_)):
        raise ValueError('Have duplicate model names.')
    for model_name in models_:
        if(model_name == ''):
            raise ValueError('Model name cannot be empty.')
        if(model_name.replace(' ', '').replace('\n', '') == ''):
            raise ValueError('Model name cannot be empty.')
        if((prefix + model_name + postfix) in models):
            raise ValueError(f'Model name {prefix + model_name + postfix} already exists.')
    all_models = get_models_from_url_ollama(base_url, api_key)
    if(len(models_) ==0):
        models_ = all_models
    for model_name in models_:
        if((prefix + model_name + postfix) in models):
            raise ValueError(f'Model name {prefix + model_name + postfix} already exists.')
    added_models = []
    missing_models = []
    for m in models_:
        if(m in all_models):
            added_models.append(prefix + m + postfix)
            models.append(prefix + m + postfix)
            model_info[prefix + m + postfix] = (base_url, api_key, m, True)
        else:
            missing_models.append(m)
    write_config_log("Model added, latest config: " + generate_models_log(model_info))
    if(len(missing_models) ==0):
        print(f'All models added successfully. {added_models}')
        return
    if(len(added_models) > 0):
        print(f'These models added successfully: {added_models}')
    print(f'These models not found: {missing_models} from {base_url}. Available models: {all_models}')
    raise Exception()


def add_zhipu_doubao(base_url: str, api_key:str, model_name:str, new_name: str=None) -> None:
    '''
    For non-Chinese users, just ignore this function.
    
    针对没有 `/v1/models`、只有 `/v1/chat/completions` 的API (目前已知的有智谱AI和豆包)
    
    这个函数会直接把模型添加进去, 不会检查 可用的模型和 API key 是否正确
    
    其它和 `add_model` 相同, 这个函数没有 一次添加多个模型的版本
    '''
    write_config_log(f"add_zhipu_doubao: base_url: {base_url}, api_key: {star_api_key(api_key)}, model_name: {model_name}, new_name: {new_name}")
    if(not base_url.startswith('http://') and not base_url.startswith('https://')):
        raise ValueError('Invalid url. Url should start with http:// or https://')
    if(base_url[-1] == '/'):
        base_url = base_url[:-1]
    if(model_name == '' or new_name == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name == None):
        new_name = model_name
    if(model_name.replace(' ', '').replace('\n', '') == '' or new_name.replace(' ', '').replace('\n', '') == ''):
        raise ValueError('Model name cannot be empty.')
    if(new_name in models):
        raise ValueError(f'Model name {new_name} already exists.')
    models.append(new_name)
    model_info[new_name] = (base_url, api_key, model_name, False)
    print(f'Model {new_name} added, but its availability and correctness of api key is not tested.')
    write_config_log("Model added, latest config: " + generate_models_log(model_info))


def start_server_async() -> None:
    '''
    Start the server, in async mode. (return immediately, run in background, the code after this can be executed)
    
    This function should be called after `create_server`.
    '''
    if (PORT == 0):
        raise Exception("Please first call create_server.")
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Request)
    write_config_log("Start the server, latest config: " + generate_models_log(model_info))
    start_new_thread(server.serve_forever, ())
    print(f'Server started, latest models: {generate_models_log(model_info)}')


def export_data():
    '''
    Export the data of history requests and responses.
    '''
    all_requests = extract_all_requests()
    all_responses = extract_all_responses()
    all = []
    responses_dict = {}
    for r in all_responses:
        responses_dict[r[0]] = r
    for r in all_requests:
        record = {}
        request_id = r[0]
        request_data = r[1]
        request_time = r[2]
        has_response = r[3]
        user_model_name = r[4]
        origin_model_name = r[5]
        record['id'] = request_id
        record['request_data'] = json.loads(request_data) # it must be json
        record['request_time_us'] = request_time
        record['has_response'] = has_response
        record['user_model_name'] = user_model_name
        record['origin_model_name'] = origin_model_name
        if(has_response):
            response = responses_dict[request_id]
            response_data = response[1]
            first_response_time = response[2]
            end_time = response[3]
            ended_successfully = response[4]
            input_tokens = response[5]
            output_tokens = response[6]
            record['response_data'] = response_data
            record['first_response_time_us'] = first_response_time
            record['end_time_us'] = end_time
            record['ended_successfully'] = ended_successfully
            record['input_tokens'] = input_tokens
            record['output_tokens'] = output_tokens
        all.append(record)
    return all
            
        


if __name__ == '__main__':
    # from keys import OPENAI_API_KEY, COHERE_API_KEY, OLLAMA_API_KEY, ZHIPU_API_KEY, KIMI_API_KEY, DOUBAO_API_KEY
    create_server(9025, 'jtc1246')
    print(export_data())
    add_model('http://jtc1246.com:9002/v1/',COHERE_API_KEY,'command-r-plus','cohere')
    # add_models('https://api.openai.com/v1/', OPENAI_API_KEY, ['gpt-3.5-turbo','gpt-4'], prefix='openai-')
    add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-4-turbo-2024-04-09', 'openai-gpt-4')
    add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-4o-2024-05-13', 'openai-gpt-4o')
    add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-3.5-turbo-0125', 'openai-gpt-3.5')
    add_ollama_models('http://127.0.0.1:11434', 'ollama')
    add_models('https://api.moonshot.cn/v1', KIMI_API_KEY)
    add_zhipu_doubao('https://open.bigmodel.cn/api/paas/v4/', ZHIPU_API_KEY, 'glm-4')
    add_zhipu_doubao('https://ark.cn-beijing.volces.com/api/v3', DOUBAO_API_KEY, 'ep-20240709181337-fmg27', 'doubao-pro-128k-240628')
    start_server_async()
    while True:
        sleep(10)
