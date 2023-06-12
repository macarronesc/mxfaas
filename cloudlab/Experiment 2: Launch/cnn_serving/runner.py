import json
import os
import sys
import signal
import threading
import socket
import time
import signal
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"


class PrintHook:
    def __init__(self,out=1):
        self.func = None
        self.origOut = None
        self.out = out

    def Start(self,func=None):
        if self.out:
            sys.stdout = self
            self.origOut = sys.__stdout__
        else:
            sys.stderr= self
            self.origOut = sys.__stderr__
            
        if func:
            self.func = func
        else:
            self.func = self.TestHook

    def Stop(self):
        self.origOut.flush()
        if self.out:
            sys.stdout = sys.__stdout__
        else:
            sys.stderr = sys.__stderr__
        self.func = None

    def flush(self):
        self.origOut.flush()
    
    def write(self,text):
        proceed = 1
        lineNo = 0
        addText = ''
        if self.func != None:
            proceed,lineNo,newText = self.func(text)
        if proceed:
            if text.split() == []:
                self.origOut.write(text)
            else:
                if self.out:
                    if lineNo:
                        try:
                            raise "Dummy"
                        except:
                            codeObject = sys.exc_info()[2].tb_frame.f_back.f_code
                            fileName = codeObject.co_filename
                            funcName = codeObject.co_name     
                self.origOut.write(newText)

def MyHookOut(text):
    return 1,1,' -- pid -- '+ str(os.getpid()) + ' ' + text

# Global variables
actionModule = None # action module

checkTable = {}
mapPIDtoLeader = {}
checkTableShadow = {}
valueTable = {}
mapPIDtoIO = {}
lockCache = threading.Lock()

lockPIDMap = threading.Lock()
requestQueue = [] # queue of child processes
mapPIDtoStatus = {} # map from pid to status (running, waiting)

def myFunction(clientSocket_):
    global actionModule

    # Set the main function
    result = actionModule.lambda_handler()

    # Send the result (Test Pid)
    result["myPID"] = os.getpid()
    msg = json.dumps(result)

        
    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(msg),
        'Connection': 'close',
    }

    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK' # this can be random

    # sending all this stuff
    r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)
    try:
        clientSocket_.send(r.encode(encoding="utf-8"))
        clientSocket_.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket_.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
        clientSocket_.send(msg.encode(encoding="utf-8"))
    except:
        clientSocket_.close()
    clientSocket_.close()


def performIO(clientSocket_):
    global mapPIDtoStatus
    global numCores
    global checkTable
    global mapPIDtoIO
    global valueTable
    global checkTableShadow
    global mapPIDtoLeader

    data_ = b''
    data_ += clientSocket_.recv(1024)
    dataStr = data_.decode('UTF-8')

    print("PETICION")

    while True:
        dataStrList = dataStr.splitlines()
        
        message = None   
        try:
            message = json.loads(dataStrList[-1])
            break
        except:
            data_ += clientSocket_.recv(1024)
            dataStr = data_.decode('UTF-8')
    
    operation = message["operation"]
    blobName = message["blobName"]
    blockedID = message["pid"]

    print(operation)

    my_id = threading.get_native_id()

    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)

    print("TEST5.-1")

    # lockPIDMap.acquire()
    print("TEST5.0")
    mapPIDtoStatus[blockedID] = "blocked"
    print("TEST5.1")
    for child in mapPIDtoStatus.copy():
        print("TEST5.2")

        if child in mapPIDtoStatus:
            print("TEST5.3")

            if mapPIDtoStatus[child] == "waiting":
                mapPIDtoStatus[child] = "running"
                print("TEST5.4")

                try:
                    print("TEST5.5")

                    os.kill(child, signal.SIGCONT)
                    print("TEST5.6")

                    break
                except:
                    pass
    print("TEST5.7")
    
    # lockPIDMap.release()

    print("TEST6")
    
    if operation == "get":
        lockCache.acquire()
        print("TEST7")
        if blobName in checkTable:
            print("TEST8")
            myLeader = mapPIDtoLeader[blobName]
            myEvent = threading.Event()
            mapPIDtoIO[my_id] = myEvent
            checkTable[blobName].append(my_id)
            checkTableShadow[myLeader].append(my_id)
            lockCache.release()
            myEvent.wait()
            print("TEST9")
            lockCache.acquire()
            blob_val = valueTable[myLeader]
            mapPIDtoIO.pop(my_id)
            checkTableShadow[myLeader].remove(my_id)
            if len(checkTableShadow[myLeader]) == 0:
                checkTableShadow.pop(myLeader)
                valueTable.pop(myLeader)
            lockCache.release()
        else:
            print("TEST10")
            mapPIDtoLeader[blobName] = my_id
            checkTable[blobName] = []
            checkTableShadow[my_id] = []
            checkTable[blobName].append(my_id)
            lockCache.release()
            blob_val = (blob_client.download_blob()).readall()
            lockCache.acquire()
            print("TEST11")
            valueTable[my_id] = blob_val
            checkTable[blobName].remove(my_id)
            for elem in checkTable[blobName]:
                mapPIDtoIO[elem].set()
            checkTable.pop(blobName)
            lockCache.release()

        print("TEST12")
        full_blob_name = blobName.split(".")
        proc_blob_name = full_blob_name[0] + "_" + str(blockedID) + "." + full_blob_name[1]
        with open(proc_blob_name, "wb") as my_blob:
            my_blob.write(blob_val)
    else:
        print("TEST13")
        fReadname = message["value"]
        fRead = open(fReadname,"rb")
        value = fRead.read()
        blob_client.upload_blob(value, overwrite=True)
        blob_val = "none"

    # lockPIDMap.acquire()
    numRunning = 0 # number of running processes

    print("TEST")

    ###### CHECK THIS
    for child in mapPIDtoStatus.copy():
        if mapPIDtoStatus[child] == "running":
            numRunning += 1
    if numRunning < numCores:
        mapPIDtoStatus[blockedID] = "running"
        os.kill(blockedID, signal.SIGCONT)
    else:
        mapPIDtoStatus[blockedID] = "waiting"
        os.kill(blockedID, signal.SIGSTOP)
    # lockPIDMap.release()

    print("TEST2")

    messageToRet = json.dumps({"value":"OK"})
    try:
        os.kill(blockedID, signal.SIGCONT)
    except:
        pass

    print("TEST3")
    clientSocket_.send(messageToRet.encode(encoding="utf-8"))
    try:
        os.kill(blockedID, signal.SIGCONT)
    except:
        pass

    print("TEST4")
    # clientSocket_.close()

def IOThread():
    print("IOTHREAD")
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        print("PETICION")
        threading.Thread(target=performIO, args=(clientSocket,)).start()

def run():
    # serverSocket: socket 
    # actionModule:  the module to execute
    # requestQueue: 
    # mapPIDtoStatus: store status for each process (waiting / running)
    global actionModule
    global requestQueue
    global mapPIDtoStatus
    global numCores
    # Set the core of mxcontainer
    numCores = 16
    affinity_mask = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
    os.sched_setaffinity(0, affinity_mask)

    print("Welcome... ", numCores)

    # Set the address and port, the port can be acquired from environment variable
    myHost = '0.0.0.0'
    myPort = int(os.environ.get('PORT', 9999))

    # Bind the address and port
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # Set actionModule
    import app
    actionModule = app

    # Redirect the stdOut and stdErr
    phOut = PrintHook()
    phOut.Start(MyHookOut)

    # Monitor I/O Block
    threadIntercept = threading.Thread(target=IOThread)
    threadIntercept.start()

    # If a request come, then fork.
    while(True):
        
        (clientSocket, address) = serverSocket.accept()
        print("Accept a new connection from %s" % str(address), flush=True)
        
        data_ = b''

        data_ += clientSocket.recv(1024)

        dataStr = data_.decode('UTF-8')

        if 'Host' not in dataStr:
            msg = 'OK'
            response_headers = {
                'Content-Type': 'text/html; encoding=utf8',
                'Content-Length': len(msg),
                'Connection': 'close',
            }
            response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

            response_proto = 'HTTP/1.1'
            response_status = '200'
            response_status_text = 'OK' # this can be random

            # sending all this stuff
            r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)
            try:
                clientSocket.send(r.encode(encoding="utf-8"))
                clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
                clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
                clientSocket.send(msg.encode(encoding="utf-8"))
                clientSocket.close()
                continue
            except:
                clientSocket.close()
                continue

        while True:
            dataStrList = dataStr.splitlines()
            
            message = None   
            try:
                message = json.loads(dataStrList[-1])
                break
            except:
                data_ += clientSocket.recv(1024)
                dataStr = data_.decode('UTF-8')
        
        responseFlag = False
        if message != None:
            print("Message: ")
            print(message)

            if "numCores" in message:
                numCores = int(message["numCores"])

                print("NumCores: " + str(numCores))

                result = {"Response": "Ok"}
                if "affinity_mask" in message:
                    affinity_mask = message["affinity_mask"]
                    os.sched_setaffinity(0, affinity_mask)
                msg = json.dumps(result)
                responseFlag = True

            # Node Controller: Test
            if "printInfo" in message:
                print("Q in message")

                result["affinity_mask"] = list(affinity_mask)
                result["numCores"] = numCores
                msg = json.dumps(result)
                responseFlag = True
                
        if responseFlag == True:
            response_headers = {
                'Content-Type': 'text/html; encoding=utf8',
                'Content-Length': len(msg),
                'Connection': 'close',
            }
            response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

            response_proto = 'HTTP/1.1'
            response_status = '200'
            response_status_text = 'OK' # this can be random

            # sending all this stuff
            r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

            clientSocket.send(r.encode(encoding="utf-8"))
            clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
            clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
            clientSocket.send(msg.encode(encoding="utf-8"))
            clientSocket.close()
            continue

        # a status mark of whether the process can run based on the free resources
        waitForRunning = False

        # The processes are running
        numIsRunning = 0

        for child in mapPIDtoStatus.copy():
            if mapPIDtoStatus[child] == "running":
                numIsRunning += 1

        print("NUM IS RUNNING:")
        print(numIsRunning)

        #### CHECK
        if numIsRunning >= numCores:
            waitForRunning = True # The process need to wait for resources

        threads = []
        numFunctions = 1

        if "numFunctions" in message:
            numFunctions = int(message["numFunctions"])
            
        print("NUM FUNCTIONS:")
        print(numFunctions)

        # Instead of having wait_termination and update_threads and maybe we can have:
        # An algorithm that checks if the number of functions to execute is greater than the number of threads
        # And if it is, then execute x functions, wait and then execute the rest
        t1 = time.time()
        for i in range(numFunctions, 0, -1):
            print("NUEVO THREAD")
            threadToAdd = threading.Thread(target=myFunction, args=(clientSocket, ))
            threads.append(threadToAdd)
            threadToAdd.start()
            time.sleep(1)

        for thread in threads:
            print("THREAD JOIN")
            thread.join()
        t2 = time.time()

        elapsed_time = t2 - t1
        print(elapsed_time)

if __name__ == "__main__":
    # main program
    run()
