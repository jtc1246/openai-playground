document.addEventListener('DOMContentLoaded', function(){
    var enable_checkbox = document.getElementById('enable');
    var ip_input = document.getElementById('ip');
    var port_input = document.getElementById('port');
    var set_button = document.getElementById('set');
    var feedback = document.getElementById('feedback');

    chrome.storage.sync.get(['enabled', 'ip', 'port'], function(data){
        if(data.enabled === undefined){
            chrome.storage.sync.set({'enabled': false, 'ip': '', 'port': ''});
            return;
        }

        enable_checkbox.checked = data.enabled;
        ip_input.value = data.ip;
        port_input.value = data.port;
    });

    enable_checkbox.addEventListener('change', function(){
        var enabled = enable_checkbox.checked;
        console.log(`enabled: ${enabled}`);
        chrome.storage.sync.set({'enabled': enabled});
    });

    set_button.addEventListener('click', function(){
        var ip = ip_input.value;
        var port = port_input.value;
        if(ip === ''){
            ip = '127.0.0.1';
        }
        if(port === ''){
            port = '9025';
        }
        var port_int = parseInt(port);
        console.log(port_int);
        if(port_int <= 0 || port_int > 65535 || isNaN(port_int)){
            feedback.innerHTML = 'Port number should be in the range of 1 ~ 65535';
            feedback.style.color = 'red';
            return;
        }
        chrome.storage.sync.set({'ip': ip, 'port': port});
        feedback.innerHTML = 'Saved successfully';
        feedback.style.color = 'green';
    });
})