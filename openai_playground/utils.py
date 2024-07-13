import json
from myHttp import http
from hashlib import sha256
import os
from queue import Queue
from .logger import write_raw_api_responses, write_config_log, write_plain_response,\
                   add_response, update_response, set_token_usage, write_plain_text

__all__ = ['endode_js', 'encode_engines', 'encode_v1_models',
           'get_models_from_url', 'get_models_from_url_ollama',
           'get_hash', "handle_stream_data"]


def endode_js(js: str):
    '''
    Modify the js file that it thinks all model names are valid.
    '''
    origin_js = js
    found_replacer = True
    if (js.find('/^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/') >= 0):
        # print('found')
        write_plain_text('REPLACER_FOUND  /^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/')
        pass
    else:
        # print('not found')
        write_plain_text('REPLACER_NOT_FOUND  /^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/')
        found_replacer = False
    js = js.replace('/^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/', '/^.*$/')
    if (js.find('/^gpt-4[a-z]?-(?!vision)(?!base).*/') >= 0):
        # print('found')
        write_plain_text('REPLACER_FOUND  /^gpt-4[a-z]?-(?!vision)(?!base).*/')
        pass
    else:
        # print('not found')
        write_plain_text('REPLACER_NOT_FOUND  /^gpt-4[a-z]?-(?!vision)(?!base).*/')
        found_replacer = False
    if(found_replacer == False):
        write_plain_text('Warning: Some text that needed to replace is not found in the current js file (because it has changed from origin one). The website might work normally, might not work. If it doesn\'t work, this may be a reason.')
        print('Warning: Some text that needed to replace is not found in the current js file (because it has changed from origin one). The website might work normally, might not work. If it doesn\'t work, this may be a reason.')
    js = js.replace('/^gpt-4[a-z]?-(?!vision)(?!base).*/', '/^.*$/')
    js = js.replace('||2049', '||4097')
    js = js.replace('"/v1/chat/completions"', '"/v1/chat/completions/"+jtc_password')
    file_path = os.path.abspath(__file__)
    file_path = os.path.dirname(file_path) + '/append.js'
    with open(file_path, 'r') as f:
        tmp = f.read()
        js += tmp
    return js


def encode_engines(models: list[str]) -> str:
    data = {"object": "list"}
    l = []
    for m in models:
        l.append({
            "object": "engine",
            "id": m,
            "ready": True,
            "owner": "system",
            "permissions": None,
            "created": None
        })
    data['data'] = l
    return json.dumps(data, ensure_ascii=False)


def encode_v1_models(models: list[str]) -> str:
    data = {"object": "list"}
    l = []
    for m in models:
        l.append({
            "object": "model",
            "id": m,
            "owned_by": "system",
            "created": 1715367049
        })
    data['data'] = l
    # print(json.dumps(data))
    return json.dumps(data, ensure_ascii=False)


def extract_models(data: str) -> list[str]:
    '''
    extract the models from json, if it's from openai, will delete like whisper and tts
    '''
    block_list = ['whisper-','tts-','dall-e','embedding-','babbage-','davinci-','ada-']
    
    try:
        if (type(data) == str):
            data = json.loads(data)
        data2 = data['data']
        results = []
        has_gpt = False
        for info in data2:
            name = info['id']
            assert (type(name) == str)
            if (str.find(name, 'gpt') >= 0):
                has_gpt = True
            results.append(name)
        if(has_gpt):
            l = len(results)
            for i in range(l-1, -1, -1):
                that_name = results[i]
                need_delete = False
                for blocked in block_list:
                    if(str.find(that_name, blocked) >= 0):
                        need_delete = True
                        break
                if(need_delete):
                    results.pop(i)
        return results
    except:
        print(data)
        raise TypeError('Invalid response from server')


def extract_models_ollama(data: str) -> list[str]:
    '''
    extract models from json, for ollama
    '''
    try:
        if (type(data) == str):
            data = json.loads(data)
        data2 = data['models']
        results = []
        has_gpt = False
        for info in data2:
            name = info['model']
            assert (type(name) == str)
            if (str.find(name, 'gpt') >= 0):
                has_gpt = True
            results.append(name)
        return results
    except:
        print(data)
        raise TypeError('Invalid response from server')


def get_models_from_url(base_url: str, api_key: str):
    '''
    url: not ends with /, usually should ends with /v1
    
    will not handle whether api key is correct here, if server doesn't do verification on /v1/models
    '''
    # this comment is the latest: currently designed to provide separate functions for zhipu 
    #     and doubao, which don't have models api, just think all models are available
    # # for zhipu, because it doesn't have models api
    # if('zhipu' in base_url or 'bigmodel.cn' in base_url):
    #     return ['glm-4-0520', 'glm-4', 'glm-4-AirX', 'glm-4-Air', 'glm-4-Flash', 'chatglm-3', 'glm-3-turbo']
    url = base_url + '/models'
    header = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = http(url, Header=header)
    if (resp['status'] < 0):
        raise ConnectionError(f"Can't connect to {base_url}")
    if (resp['status'] > 0):
        write_config_log(f"Error in getting models from {url},  " + str(resp))
        raise ConnectionError(f"Invalid response from server, " + str(resp['extra']))
    if(resp['code'] != 200):
        print(f'Error: status code {resp["code"]}')
        print(resp['text'])
        write_config_log(f"Error in getting models from {url},  " + str(resp))
        raise Exception("Invalid api key, or other server error.")
    write_config_log(f"Models from {url},  " + json.dumps(resp['text'], ensure_ascii=False))
    return extract_models(resp['text'])


def get_models_from_url_ollama(base_url: str, api_key: str):
    '''
    url: on default should end with :11434, no any other path
    
    just ends with port number (if you change the default port, port can be different)
    '''
    url = base_url + '/api/tags'
    header = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = http(url, Header=header)
    if (resp['status'] < 0):
        raise ConnectionError(f"Can't connect to {base_url}")
    if (resp['status'] > 0):
        write_config_log(f"Error in getting models from {url},  " + str(resp))
        raise ConnectionError(f"Invalid response from server, " + str(resp['extra']))
    if(resp['code'] != 200):
        print(f'Error: status code {resp["code"]}')
        print(resp['text'])
        write_config_log(f"Error in getting models from {url},  " + str(resp))
        raise Exception("Invalid api key, or other server error.")
    write_config_log(f"Models from {url},  " + json.dumps(resp['text'], ensure_ascii=False))
    return extract_models_ollama(resp['text'])


def get_hash(s: str) -> str:
    return sha256(s.encode()).hexdigest()


def handle_stream_data(request_obj, data_queue:Queue):
    request_obj.send_response(200)
    request_obj.send_header('Access-Control-Allow-Origin', '*')
    request_obj.send_header('Content-Type', 'text/event-stream; charset=utf-8')
    request_obj.send_header('Transfer-Encoding', 'chunked')
    request_obj.send_header('Connection', 'keep-alive')
    request_obj.end_headers()
    try:
        while True:
            data = data_queue.get()
            if(data == False):
                break
            request_obj.wfile.write(f"{len(data):x}".encode('utf-8'))
            request_obj.wfile.write(b'\r\n')
            request_obj.wfile.write(data)
            request_obj.wfile.write(b'\r\n')
        request_obj.wfile.write(b'0\r\n\r\n')
        request_obj.wfile.flush()
    except:
        pass


def construct_response(data: bytes):
    while(len(data) > 0 and data[-1] == b'\n'):
        data = data[:-1]
    if(len(data) == 0):
        return ''
    parts = data.split(b'\n\n')
    result = ''
    for p in parts:
        p = p[6:]
        try:
            p = p.decode('utf-8')
            p = json.loads(p)
            result += p['choices'][0]['delta']['content']
        except:
            continue
    return result


def get_usage(data: bytes):
    data = data.decode('utf-8')[:-2] # remove the last 2 \n
    parts = data.split('\n\n')
    last_msg = parts[-2]
    last_msg = json.loads(last_msg[6:])
    try:
        in_tokens = last_msg['usage']['prompt_tokens']
        out_tokens = last_msg['usage']['completion_tokens']
        return (in_tokens, out_tokens)
    except:
        return (None, None)


def handle_log_queue(log_queue:Queue, stream_id:str, full_id:str):
    index = 0
    data_till_now = b''
    latest_resp = ''
    added = False
    while True:
        data = log_queue.get()
        if (data == False):
            write_raw_api_responses(stream_id, "END OF RESPONSE", index)
            in_tokens, out_tokens = get_usage(data_till_now)
            print(f'In tokens: {in_tokens}, out tokens: {out_tokens}')
            write_plain_response(stream_id, str([latest_resp]) + ' FINISHED  ' + f'In: {in_tokens}, Out: {out_tokens}', index)
            set_token_usage(full_id, in_tokens, out_tokens)
            break
        data_till_now += data
        latest_resp = construct_response(data_till_now)
        write_raw_api_responses(stream_id, data, index)
        write_plain_response(stream_id, str([latest_resp]), index)
        if(added == False):
            added = True
            add_response(full_id, latest_resp)
        else:
            update_response(full_id, latest_resp)
        index += 1


def generate_models_log(model_info:dict):
    tmp = json.dumps(model_info, ensure_ascii=False)
    model_info = json.loads(tmp)
    for m in model_info:
        model_info[m] = list(model_info[m])
        model_info[m][1] = '' # delete api key
    return json.dumps(model_info, ensure_ascii=False)


def star_api_key(api_key:str) -> str:
    l = len(api_key)
    s = l // 6
    e = l - s
    return api_key[:s] + '*' * (l - s * 2) + api_key[e:]


if __name__ == '__main__':
    # from keys import OPENAI_API_KEY, COHERE_API_KEY, OLLAMA_API_KEY
    print(get_models_from_url('https://api.openai.com/v1', OPENAI_API_KEY))
    print(get_models_from_url('http://jtc1246.com:9002/v1', COHERE_API_KEY))
    print(get_models_from_url_ollama('http://127.0.0.1:11434', 'ollama'))
    