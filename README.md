# openai-playground

## Introduction

Use other openai-compatible API services in OpenAI Playground.

It supports:

- Add any openai-compatible API service.
- In stream mode.
- Chatting history storage and export.

This is a useful tool for those AI services that have awful playground experience.

#### Demo:

<img src="resources/demo_2x_speed.gif">

## Usage

### 1. Requirements

- Has OpenAI API account, and can login (don't need to have money).
- Has Chrome on desktop, and can install extensions.
- python >= 3.9

### 2. Installation (the order of following 2 steps doesn't matter)

#### 2.1 Install python package

```bash
pip install openai-playground
```

#### 2.2 Install Chrome extension

**Step for running python server and Chrome on different devices (ignore this if on same device)**: If want to run python server and use Chrome on different devices (i.e. you can't access to server through 127.0.0.1 or localhost in Chrome), you need to do some more steps, which are at the last on this README. This step must be done before the following. Else, you can ignore this.

```bash
git clone https://github.com/jtc1246/openai-playground.git
cd openai-playground
```
Or [download the zip](https://github.com/jtc1246/openai-playground/archive/refs/heads/main.zip), and go to openai-playground-main folder.

Then, open Chrome, go to `chrome://extensions/`, turn on `Developer mode`, click `Load unpacked`, and select the `chrome_extension` folder in the `openai-playground` folder.

<img src="resources/chrome_extension.png">

### 3. Actual Usage

#### 3.1 Run python program

Do basic setups (port, password, storage path, etc.) in python, you can see an example in [example.py](example.py). The python functions usage will be intorduced in the next section.

#### 3.2 Setup Chrome extension

1. Click this extension icon, then it will show the setup page. 
2. Select the "Enable" checkbox, to enable it. 
3. Enter the IP (or domain) and port, then click "Set" to save the settings. 
4. Click "Go" to go to OpenAI Playground (platform\.openai.com/playground).

<img src="resources/extension_page.png" width="40%">

## Python Functions

You can see an example in [example.py](example.py).

### General introduction

You need to do following things in the python code:

1. Set the port and password of this server. (use `create_server` function)
2. Add models, need to input base url, your api key, and model name. (have 5 functions here, will be introduced later) 
3. Start the server. (use `start_server_async` function)
4. Use other operations to block the main thread, because `start_server_async` will return immediately and run in background. (just sleep is OK)

### Functions

#### 1. `create_server`

```python
def create_server(port:int, password:str, data_dir:str='./playground_logs') -> None:
```

Create the playground server. Just create, will not start. You need to add models to it and then call `start_server_async` later.

Arguments:

1. password: the password the needs to be input in the browser, for authorization
2. data_dir: the directory to store the database and logs. Will create if not exists.



#### 2. `add_model`

```python
def add_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
```

Add a model to the playground, need openai format API. Need to implement both `<base_url>/models` and `<base_url>/chat/completions`

Arguments:

1. base_url: should include `/v1` if it's openai, start with `http://` or `https://`. Either have or not have the last `/` is OK. E.g. for openai, it should be `https://api.openai.com/v1`. It will access `<base_url>/models` and `<base_url>/chat/completions`
2. model_name: need to be exactly same as the name in your service
3. new_name: the name you want to show in the playground, if not provided, will be same as model_name

#### 3. `add_models`

```python
def add_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
```

Add a list of models to the playground, need openai format API. Need to implement both `<base_url>/models` and `<base_url>/chat/completions`. If models_ is empty, will add all available models.

Arguments:

1. base_url: should include `/v1` if it's openai, start with `http://` or `https://`. Either have or not have the last `/` is OK. E.g. for openai, it should be `https://api.openai.com/v1`. It will access `<base_url>/models` and `<base_url>/chat/completions`
2. models_: a list of model names you want to add, model name should be exactly same as the name in your service. If it is an empty list, will add all available models.
3. prefix and postfix: the name shown in the playground will be `prefix + model_name + postfix`

#### 4. `add_ollama_model`

```python
def add_ollama_model(base_url:str, api_key:str, model_name:str, new_name: str=None) -> None:
```

For ollama, if you don't know what ollama is, just ignore this function.

Mostly same as `add_model`.

For base_url, on default should end with :11434, no any other path. Just ends with port number (if you change the default port, port can be different)

For api_key, it's not checked, but you must provide, even an empty str is OK.

#### 5. `add_ollama_models`

```python
def add_ollama_models(base_url:str, api_key:str, models_:list[str] = [], prefix:str='', postfix:str='') -> None:
```

For ollama, if you don't know what ollama is, just ignore this function.

Mostly same as `add_models`.

For base_url, on default should end with :11434, no any other path. Just ends with port number (if you change the default port, port can be different)

For api_key, it's not checked, but you must provide, even an empty str is OK.

#### 6. `add_zhipu_doubao`

```python
def add_zhipu_doubao(base_url: str, api_key:str, model_name:str, new_name: str=None) -> None:
```

For non-Chinese users, just ignore this function.

针对没有 `/v1/models`、只有 `/v1/chat/completions` 的API (目前已知的有智谱AI和豆包)

这个函数会直接把模型添加进去, 不会检查 可用的模型和 API key 是否正确

其它和 `add_model` 相同, 这个函数没有 一次添加多个模型的版本

#### 7. `start_server_async`

```python
def start_server_async() -> None:
```

Start the server, in async mode. (return immediately, run in background, the code after this can be executed)

This function should be called after `create_server`.

#### 8. `export_data`

```python
def export_data():
```

Export the data of history requests and responses.

## How it works

The Chrome extension blocks the API requests to openai server, and forwards them to our python server. Our python server then call the API we added, and return the results to the browser.

## Step for using non-127.0.0.1 IP

Since Chrome don't allow to access http urls in https page (and this also can't be realized by extension), you need to modify the Chrome start command to allow this. And then use this chrome to install extension and use the playground.

On macOS,

```bash
open -n -a "Google Chrome" --args --allow-running-insecure-content --user-data-dir="/tmp/chrome_dev_session"
```

On Windows,

```bash
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --allow-running-insecure-content --user-data-dir="%TEMP%\chrome_dev_session"
```

On Linux,

```bash
google-chrome --allow-running-insecure-content --user-data-dir="/tmp/chrome_dev_session"
```
