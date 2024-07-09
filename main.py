from typing import Any
from myHttp import http
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import time, sleep
from _thread import start_new_thread
from utils import endode_js, encode_engines, encode_v1_models,\
                  get_models_from_url, get_models_from_url_ollama
from mySecrets import hexToStr
import json
from keys import OPENAI_API_KEY, COHERE_API_KEY, OLLAMA_API_KEY, ZHIPU_API_KEY, KIMI_API_KEY, DOUBAO_API_KEY

__all__ = ['create_server', 'start_server_async',
           'add_model', 'add_models', 'add_ollama_model', 'add_ollama_models']

PASSWORD = 'jtc1246'

JS_URL = 'https://openaiapi-site.azureedge.net/public-assets/d/ddd16bc977/static/js/main.600c2350.js'

JS_CONTENT = ''
PORT = 0

def init():
    global JS_CONTENT
    tmp = http(JS_URL, ToJson=False)
    if(tmp['status'] < 0 or tmp['code'] != 200):
        print('Failed to fetch JS file')
        raise Exception('Failed to fetch JS file')
    JS_CONTENT = tmp['text']
    # currently don't need to encode according model list, so just pre generate
    JS_CONTENT = endode_js(JS_CONTENT)


models = []
model_info = {} # {name: (base_url, api_key, origin_name, is_ollama:bool)}


answer = '''要理解Transfer-Encoding: chunked的HTTP请求如何在TCP层面处理，有必要了解HTTP协议与TCP协议的关系。HTTP（超文本传输协议）运行在TCP（传输控制协议）之上，HTTP的请求和响应数据都通过TCP连接传输。

### Transfer-Encoding: chunked的HTTP请求概述

当HTTP请求或响应的头部包含`Transfer-Encoding: chunked`，意味着消息体（数据部分）是以一系列大小不确定的块（chunk）形式传输的，而不是一次性传输整个消息体。这对支持流式传输或发送动态生成内容非常有用。每个块都有自己的大小标识，并且最后一个块是大小为0的块，标识消息体结束。

### TCP层面处理流程

以下是一个通过TCP处理 chunked 传输的简化步骤：

1. **建立TCP连接**: 客户端（通常是浏览器或其他HTTP客户端）和服务器建立一个TCP连接。

2. **发送HTTP请求头部**: 客户端发送HTTP请求头部，其中包含`Transfer-Encoding: chunked`。

    ```
    POST /upload HTTP/1.1
    Host: example.com
    Transfer-Encoding: chunked
    Content-Type: text/plain
    
    ```

3. **发送第一个数据块**: 客户端通过TCP连接发送第一个数据块。

    ```
    5\\r\\n
    Hello\\r\\n
    ```

    - `5\\r\\n`表示数据块的长度（5个字节）
    - `Hello\\r\\n`是实际的数据块内容，后跟换行符

4. **发送后续块**: 每个数据块通过TCP连接依次发送，直到最后一个块。

    ```
    7\\r\\n
    World!\\r\\n
    0\\r\\n
    \\r\\n
    ```

    - `7\\r\\n`表示下一个数据块的长度（7个字节）
    - `World!\\r\\n`是实际的数据块内容，后跟换行符
    - `0\\r\\n`表示这是最后一个块（长度为0）
    - `\\r\\n`表示消息体结束

5. **服务器处理块**: 服务器从TCP连接读取数据，解析每个块的大小与内容，并进行相应的处理。

6. **发送HTTP响应**: 服务器在处理完成后，通过同一个TCP连接返回HTTP响应，这个响应也可能使用chunked传输编码。

例子：

```
HTTP/1.1 200 OK
Transfer-Encoding: chunked
Content-Type: text/plain

7\\r\\n
Success\\r\\n
0\\r\\n
\\r\\n
```

### 总结

HTTP的chunked传输编码通过将消息体分成一系列块，并通过TCP连接逐块发送。每个块包含其大小的元数据，使接收方知道如何正确拼接这些块。TCP连接保证了数据传输的完整性和顺序，因此chunked传输编码可以有效地用于动态内容传输和流式数据传输。'''


class Request(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path
        print(path)
        # print(self.headers['Cookie'])
        if(path not in ['/v1/models','/v1/engines', '/600c2350.js']
           and  not path.startswith('/v1/login/')):
            self.send_response(404)
            self.send_header('Content-Length', 0)
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.flush()
            return
        # self.send_response(200)
        # self.send_header('Content-Type', 'application/json')
        # self.send_header('Access-Control-Allow-Origin', '*')
        if path == '/v1/models':
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
            password = hexToStr(path)
            if(password != PASSWORD):
                self.send_response(401)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Content-Length', 2)
                self.end_headers()
                self.wfile.write(b'{}')
                self.wfile.flush()
                return
            print(200)
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
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Connection', 'keep-alive')
            # js = endode_js(JS_CONTENT)
            js = JS_CONTENT # currently don't need to encode according model list
            js = js.encode('utf-8')
            self.send_header('Content-Length', len(js))
            # self.send_header('Content-Type', 'application/javascript')
            self.send_header
            self.end_headers()
            self.wfile.write(js)
            # self.wfile.write(JS_CONTENT)
            self.wfile.flush()
            return
        
    def do_POST(self):
        path = self.path
        print(path)
        if(not path.startswith('/v1/chat/completions/')):
            self.send_response(404)
            self.send_header('Content-Length', 0)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.wfile.flush()
            return
        pw = path[len('/v1/chat/completions/'):]
        pw = hexToStr(pw)
        if(pw != PASSWORD):
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
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = json.loads(body)
        model_name = body['model']
        if(model_name not in models):
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
        print('stream')
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Transfer-Encoding', 'chunked')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        ans = answer
        ended = False
        while(ended == False):
            try:
                sleep(0.1)
                tmp = ans[0:10]
                ans = ans[10:]
                data = {"id":"chatcmpl-9ipfOZcUIw8DEQe4q8ncQXTK8xywv","object":"chat.completion.chunk","created":1720472066,"model":"gpt-4-0613","system_fingerprint":None,"choices":[{"index":0,"delta":{"content":tmp},"logprobs":None,"finish_reason":None}],"usage":None}
                data = json.dumps(data, ensure_ascii=False)
                data = 'data: ' + data + '\n\n'
                if(tmp == ''):
                    data = ''
                    self.wfile.write(b'E\r\ndata: [DONE]\n\n\r\n')
                    self.wfile.write(b'0\r\n\r\n')
                    self.wfile.flush()
                    break
                data = data.encode('utf-8')
                self.wfile.write(f"{len(data):X}".encode('utf-8'))
                self.wfile.write(b'\r\n')
                self.wfile.write(data)
                self.wfile.write(b'\r\n')
            except (BrokenPipeError, ConnectionResetError):
                break
        
    
    def do_OPTIONS(self):
        self.send_response(200)
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
# server = ThreadingHTTPServer(('0.0.0.0', 9025), Request)
# start_new_thread(server.serve_forever, ())

# while True:
#     sleep(10)

def create_server(port:int, database_path:str, log_path:str) -> None:
    global PORT
    if(port <=0 or port >=65536):
        raise ValueError('Invalid port number: ' + str(port))
    PORT = port

def add_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
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


def add_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
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
    if(len(missing_models) ==0):
        print(f'All models added successfully. {added_models}')
        return
    if(len(added_models) > 0):
        print(f'These models added successfully: {added_models}')
    print(f'These models not found: {missing_models} from {base_url}. Available models: {all_models}')
    raise Exception()


def add_ollama_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
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


def add_ollama_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
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
    if(len(missing_models) ==0):
        print(f'All models added successfully. {added_models}')
        return
    if(len(added_models) > 0):
        print(f'These models added successfully: {added_models}')
    print(f'These models not found: {missing_models} from {base_url}. Available models: {all_models}')
    raise Exception()


def add_zhipu_doubao(base_url: str, api_key:str, model_name:str, new_name: str=None) -> None:
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


def start_server_async() -> None:
    if (PORT == 0):
        raise Exception("Please first call create_server.")
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Request)
    start_new_thread(server.serve_forever, ())


if __name__ == '__main__':
    create_server(9025, './database.db', './log.txt')
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
    # while True:
    #     sleep(10)