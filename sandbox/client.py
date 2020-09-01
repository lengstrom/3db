import zmq
from uuid import uuid4
import sys
import time

port = "5555"
if len(sys.argv) > 1:
    port =  sys.argv[1]
    int(port)

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect ("tcp://localhost:%s" % port)

worker_id = str(uuid4())

def query(kind, **args):
    socket.send_pyobj({
        'kind': kind,
        'worker_id': worker_id,
        **args
    })
    return socket.recv_pyobj()

assignment = query('connect')

print(assignment)

assert assignment['kind'] == 'assignment'
env = assignment['environment']
model = assignment['model']

while True:
    print("starting to pull")
    job_description = query('pull', batch_size=120)
    print("pull done")
    paramters = job_description['params_to_render']
    if len(paramters) == 0:
        print("Nothing to do!", 'sleeping')
        time.sleep(1)
    print(job_description)

print(env, model)



