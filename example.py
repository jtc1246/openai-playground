from keys import OPENAI_API_KEY, COHERE_API_KEY, OLLAMA_API_KEY, ZHIPU_API_KEY, KIMI_API_KEY, DOUBAO_API_KEY
import openai_playground
from time import sleep

PORT = 9025
PASSWORD = 'qwe123'


openai_playground.create_server(PORT, PASSWORD)
print(openai_playground.export_data())
openai_playground.add_model('http://jtc1246.com:9002/v1/', COHERE_API_KEY, 'command-r-plus', 'cohere')
# openai_playground.add_models('https://api.openai.com/v1/', OPENAI_API_KEY, ['gpt-3.5-turbo','gpt-4'], prefix='openai-')
openai_playground.add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-4-turbo-2024-04-09', 'openai-gpt-4')
openai_playground.add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-4o-2024-05-13', 'openai-gpt-4o')
openai_playground.add_model('https://api.openai.com/v1/', OPENAI_API_KEY, 'gpt-3.5-turbo-0125', 'openai-gpt-3.5')
openai_playground.add_ollama_models('http://127.0.0.1:11434', 'ollama')
openai_playground.add_models('https://api.moonshot.cn/v1', KIMI_API_KEY)
openai_playground.add_zhipu_doubao('https://open.bigmodel.cn/api/paas/v4/', ZHIPU_API_KEY, 'glm-4')
openai_playground.add_zhipu_doubao('https://ark.cn-beijing.volces.com/api/v3', DOUBAO_API_KEY, 'ep-20240709181337-fmg27', 'doubao-pro-128k-240628')
openai_playground.start_server_async()
print(f'\nServer started at port {PORT} with password {PASSWORD}')
while True:
    sleep(10)
