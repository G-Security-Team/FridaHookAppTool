from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import requests
import frida

#By:Gr33k
#mail:jiaxingl@126.com


ECHO_PORT = 28080
BURP_PORT = 8080


class RequestHandler(BaseHTTPRequestHandler):
    def do_REQUEST(self):
        content_length = int(self.headers.get('content-length', 0))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.rfile.read(content_length))

    do_RESPONSE = do_REQUEST


def echo_server_thread():
    print('start echo server at port {}'.format(ECHO_PORT))
    server = HTTPServer(('', ECHO_PORT), RequestHandler)
    server.serve_forever()


t = Thread(target=echo_server_thread)
t.daemon = True
t.start()

session = frida.get_usb_device().attach('支付宝')

script = session.create_script('''


try{
    var className = "DTURLRequestOperation";
    var funcName = "- addHTTPBodyParameter:forKey:";

    var hook = eval('ObjC.classes.' + className + '["' + funcName + '"]');
    console.log("[*] Class Name: " + className);
    console.log("[*] Method Name: " + funcName);
    Interceptor.attach(hook.implementation, {
      onEnter: function(args) {
      var v = new ObjC.Object(args[2]);
      send({type: 'REQ', data: v.toString()})
      var op = recv('NEW_REQ', function(val) {
            var s = val.payload;
            var new_s = ObjC.classes.NSString.stringWithString_(s);
            args[2] = new_s;
            });
            op.wait();
      },
      onLeave: function(retval) {  
      }
    });
    
    
    var className1 = "DTURLRequestOperation";
    var funcName1 = "- responseString";
    var err = ObjC.classes.NSError.alloc();
    
    var hook1 = eval('ObjC.classes.' + className1 + '["' + funcName1 + '"]');
    console.log("[*] Class Name: " + className1);
    console.log("[*] Method Name: " + funcName1);
    Interceptor.attach(hook1.implementation, {
      onEnter: function(args) {

      },
      onLeave: function(retval) {
      var re = new ObjC.Object(retval);
      
      send({type: 'RESP', data: re.toString()});
        var op = recv('NEW_RESP', function(val) {
            var new_data = val.payload;
            var new_ret = ObjC.classes.NSString.stringWithString_(new_data);
            retval.replace(new_ret);
            
        });
        op.wait();
      
      }  
    });
    
}
catch(err){
    console.log("[!] Exception2: " + err.message);
}
''')

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        _type, data = payload['type'], payload['data']

        if _type == 'REQ':
            data = str(data)
            r = requests.request('REQUEST', 'http://127.0.0.1:{}/'.format(ECHO_PORT),
                                 proxies={'http': 'http://127.0.0.1:{}'.format(BURP_PORT)},
                                 data=data.encode('utf-8'))
            
            script.post({'type': 'NEW_REQ', 'payload': r.text})



        elif _type == 'RESP':
            r = requests.request('RESPONSE', 'http://127.0.0.1:{}/'.format(ECHO_PORT),
                                 proxies={'http': 'http://127.0.0.1:{}'.format(BURP_PORT)},
                                 data=data.encode('utf-8'))

            script.post({'type': 'NEW_RESP', 'payload': r.text})


script.on('message', on_message)
script.load()
sys.stdin.read()
