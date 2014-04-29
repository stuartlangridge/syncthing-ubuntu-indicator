from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import sys, tty, termios, time, random, string, json
from datetime import tzinfo, timedelta, datetime

class TZ(tzinfo):
    def utcoffset(self, dt): return timedelta(minutes=60)

class Handler(BaseHTTPRequestHandler):
    
    def log_request(self, *args):
        pass
    
    def do_GET(self):
        global QUEUE
        self.send_response(200)
        self.end_headers()
        now = time.time()
        foundevents = False
        while 1:
            if QUEUE:
                self.wfile.write(json.dumps(QUEUE))
                QUEUE = []
                foundevents = True
                break
            elif time.time() - now > 10:
                break
            else:
                time.sleep(1)
        if not foundevents:
            self.wfile.write(json.dumps([make_action(ACTIONS[0], -1)]))
        self.wfile.write('\n')
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    timeout = 6

def printtime():
    while 1:
        if not TYPING:
            print time.asctime(), TYPING, "\r",

def randomLetters():
    return "".join([random.choice(string.uppercase) for x in range(10)])

CREATED = {}
def create(thing):
    if thing not in CREATED: CREATED[thing] = []
    val = randomLetters()
    CREATED[thing].append(val)
    return val
def use(thing):
    if thing not in CREATED: return randomLetters()
    if not CREATED[thing]: return randomLetters()
    return CREATED[thing].pop()

ACTIONS = [
    {"type": "TIMEOUT", "params": lambda: {}},
    {"type": "NODE_CONNECTED", "params": lambda: {"node": create("node")}},
    {"type": "NODE_DISCONNECTED", "params": lambda: {"node": use("node")}},
    {"type": "PULL_START", "params": lambda: {
        "repo": 'reponame', "file": create("file") + ".txt",
        "size": random.randint(1,10000), "modified": time.time(), "flags": ""}},
    {"type": "PULL_COMPLETE", "params": lambda: {
        "repo": 'reponame', "file": use("file") + ".txt"}},
    {"type": "PULL_ERROR", "params": lambda: {
        "repo": 'reponame', "file": use("file") + ".txt", "error": "MESSAGE"}}
]

QUEUE = []

def menu():
    for i in range(len(ACTIONS)):
        print "%s: %s" % (i, ACTIONS[i]["type"])
    print "q. quit"

def make_action(action_template, action_id):
    ts = datetime.now()
    ts = ts.replace(tzinfo=TZ())
    action = {
        "type": action_template["type"], 
        "params": action_template["params"](),
        "id": action_id,
        "timestamp": ts.isoformat()
    }
    return action

if __name__ == '__main__':
    server = ThreadedHTTPServer(('localhost', 5115), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server = threading.Thread(target=server.serve_forever)
    server.daemon = True
    server.start()
    fd = sys.stdin.fileno()
    menu()
    acount = 1
    while 1:
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        if ch == "q": break
        try:
            action_template = ACTIONS[int(ch)]
        except:
            continue
        action = make_action(action_template, acount)
        print action
        QUEUE.append(action)
        acount += 1
        if acount % 20 == 0:
            menu()

        

