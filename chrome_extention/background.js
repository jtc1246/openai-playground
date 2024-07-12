chrome.webRequest.onBeforeRequest.addListener(
  function(details) {
    let url = details.url;
    if (url.includes('/static/js/main.') && url.includes('openaiapi-site.azureedge.net') && url.endsWith('.js')) {
      console.log(url);
      return {redirectUrl: "http://127.0.0.1:9025/600c2350.js"};
    }
    if (url === 'https://api.openai.com/v1/models' ||
        url === 'https://api.openai.com/v1/engines' ||
        url.startsWith('https://api.openai.com/v1/login') ||
        url.startsWith('https://api.openai.com/v1/chat/completions/')) {
      console.log(url);
      return {redirectUrl: `http://${details.url.replace("https://api.openai.com", "127.0.0.1:9025")}`};
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