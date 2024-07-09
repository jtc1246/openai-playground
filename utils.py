import json

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
