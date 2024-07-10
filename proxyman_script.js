async function onRequest(context, url, request) {
  if(!(url.indexOf('/static/js/main.') !== -1 && url.indexOf('openaiapi-site.azureedge.net') !== -1 && url.endsWith('.js'))
    && url !== 'https://api.openai.com/v1/models'
    && url !== 'https://api.openai.com/v1/engines'
    && !url.startsWith('https://api.openai.com/v1/login')
    && !url.startsWith('https://api.openai.com/v1/chat/completions/')) {
    return request;
  }
  console.log(url);
  request.host = "127.0.0.1";
  request.scheme = 'http';
  request.port = 9025;
  if(url.indexOf('/static/js/main.') !== -1 && url.endsWith('.js')){
    request.path = '/600c2350.js'
  }
  return request;
}

async function onResponse(context, url, request, response) {
  return response;
}