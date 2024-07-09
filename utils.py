import json
from myHttp import http
from keys import OPENAI_API_KEY, COHERE_API_KEY, OLLAMA_API_KEY

__all__ = ['endode_js', 'encode_engines', 'encode_v1_models']


def endode_js(js: str):
    '''
    Modify the js file that it thinks all model names are valid.
    '''
    origin_js = js
    if (js.find('/^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/') >= 0):
        print('found')
    else:
        print('not found')
    js = js.replace('/^gpt-3\.5-turbo(?!-instruct)(?!-base)|^gpt-4(?!-base)|^gpt-dv/', '/^.*$/')
    if (js.find('/^gpt-4[a-z]?-(?!vision)(?!base).*/') >= 0):
        print('found')
    else:
        print('not found')
    js = js.replace('/^gpt-4[a-z]?-(?!vision)(?!base).*/', '/^.*$/')
    js = js.replace('"/v1/chat/completions"', '"/v1/chat/completions/"+jtc_password')
    with open('append.js', 'r') as f:
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
    block_list = ['whisper-','tts-','dall-e','embedding-','baggage-','davinci-','ada-']
    
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


def get_models_from_url(base_url: str, api_key: str):
    '''
    url: not ends with /
    '''
    url = base_url + '/models'
    header = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = http(url, Header=header)
    if (resp['status'] < 0):
        raise ConnectionError(f"Can't connect to {base_url}")
    if (resp['status'] > 0):
        raise ConnectionError(f"Invalid response from server, " + str(resp['extra']))
    if(resp['code'] != 200):
        print(f'Error: status code {resp["code"]}')
        print(resp['text'])
        raise Exception("Invalid api key, or other server error.")
    return extract_models(resp['text'])


if __name__ == '__main__':
    print(get_models_from_url('https://api.openai.com/v1', OPENAI_API_KEY))
    # a=http('http://jtc1246.com:9002/v1/models')
    # print(a)
    print(get_models_from_url('http://jtc1246.com:9002/v1', COHERE_API_KEY+'ewg'))
    