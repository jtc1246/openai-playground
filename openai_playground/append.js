

function stringToHex(str) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(str);
    let hex = '';
    for (let byte of bytes) {
        hex += byte.toString(16).padStart(2, '0');
    }
    return hex;
}

var jtc_password = ''

function login() {
    /**
     * Login process:
     * When page loaded, prompt user to input password, send to server, until correct
     * If password incorrect, return 401, if all ok, return 200
     * Use sync xmlhttprequest
     */
    var url = 'https://api.openai.com/v1/login/';
    var stored_pw = localStorage.getItem('jtc_password');
    var pw;
    if (stored_pw === null) {
        pw = prompt('Please input the password: ');
        console.log(pw);
        while (pw === '' || pw === null) {
            pw = prompt('Please input the password (passwork can\'t be empty): ');
        }
    } else {
        pw = stored_pw;
    }
    var correct = false;
    while (correct === false) {
        var request = new XMLHttpRequest();
        request.open('GET', url + stringToHex(pw), false);
        try{
            request.send();
        } catch (e) {
            alert("Network error, please refresh the page and try again. " + e);
            throw new Error();
        }
        if (request.status === 200 || request.status === 202) {
            correct = true;
            jtc_password = stringToHex(pw);
            localStorage.setItem('jtc_password', pw);
        } else if (request.status === 401) {
            pw = prompt('Password incorrect, please try again: ');
            while (pw === '' || pw === null) {
                pw = prompt('Please input the password (passwork can\'t be empty): ');
            }
        } else {
            alert('Unknown error, please refresh the page and try again.');
        }
    }
}

window.addEventListener('DOMContentLoaded', login);
