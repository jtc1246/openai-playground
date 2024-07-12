var enabled = false;
var ip = '127.0.0.1';
var port = '9025';

function update_settings() {
    chrome.storage.sync.get(['enabled', 'ip', 'port'], function(data){
        if(data.enabled === undefined){
            setTimeout(update_settings, 100);
            return;
        }
        enabled = data.enabled;
        if(data.ip === ''){
            ip = '127.0.0.1';
        } else {
            ip = data.ip;
        }
        if(data.port === ''){
            port = '9025';
        } else {
            port = parseInt(data.port).toString();
        }
        setTimeout(update_settings, 100);
    });
}

update_settings();

chrome.webRequest.onBeforeRequest.addListener(
  function(details) {
    if(enabled === false){
        return {};
    }
    let url = details.url;
    if (url.includes('/static/js/main.') && url.includes('openaiapi-site.azureedge.net') && url.endsWith('.js')) {
      console.log(url);
      return {redirectUrl: `http://${ip}:${port}/600c2350.js`};
    }
    if (url === 'https://api.openai.com/v1/models' ||
        url === 'https://api.openai.com/v1/engines' ||
        url.startsWith('https://api.openai.com/v1/login') ||
        url.startsWith('https://api.openai.com/v1/chat/completions/')) {
      console.log(url);
      return {redirectUrl: `http://${details.url.replace("https://api.openai.com",ip+":"+port)}`};
    }
    return {};
  },
  {urls: ["<all_urls>"]},
  ["blocking"]
);

chrome.webRequest.onHeadersReceived.addListener(
  function(details) {
    if(details.url.indexOf('/v1/chat/completions/') !== -1) {
        return {};
    }
    for (var i = 0; i < details.responseHeaders.length; i++) {
      if (details.responseHeaders[i].name.toLowerCase() === 'content-security-policy') {
        // 添加或修改CSP规则允许连接到你的本地服务器
        details.responseHeaders.splice(i, 1);
        break; // 确保只删除第一个找到的CSP头
      }
    }
    console.log(details.url);
    console.log(details.responseHeaders);
    return {responseHeaders: details.responseHeaders};
  },
  {urls: ["<all_urls>"]}, // 或者更具体的URL
  ["blocking", "responseHeaders"]
);