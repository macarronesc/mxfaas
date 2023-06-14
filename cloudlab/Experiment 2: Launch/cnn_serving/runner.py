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
results = []
results_lock = threading.Lock()

def sendResponse(clientSocket_, message):
    msg = json.dumps(message)

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
        clientSocket_.close()
    except:
        clientSocket_.close()


def myFunction(t1):
    global actionModule

    # Set the main function
    result = actionModule.lambda_handler()
    result["time"] = time.time() - t1

    with results_lock:
        results.append(result)

def performIO(clientSocket_):
    global numCores
    global checkTable
    global mapPIDtoIO
    global valueTable
    global checkTableShadow
    global mapPIDtoLeader

    data_ = b''
    data_ += clientSocket_.recv(1024)
    dataStr = data_.decode('UTF-8')

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

    my_id = threading.get_native_id()

    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)

    if operation == "get":
        with lockCache:
            if blobName in checkTable:
                myLeader = mapPIDtoLeader[blobName]
                myEvent = threading.Event()
                mapPIDtoIO[my_id] = myEvent
                checkTable[blobName].append(my_id)
                checkTableShadow[myLeader].append(my_id)
                myEvent.wait()
                blob_val = valueTable[myLeader]
                mapPIDtoIO.pop(my_id)
                checkTableShadow[myLeader].remove(my_id)
                if len(checkTableShadow[myLeader]) == 0:
                    checkTableShadow.pop(myLeader)
                    valueTable.pop(myLeader)
            else:
                mapPIDtoLeader[blobName] = my_id
                checkTable[blobName] = []
                checkTableShadow[my_id] = []
                checkTable[blobName].append(my_id)
                blob_val = (blob_client.download_blob()).readall()
                valueTable[my_id] = blob_val
                checkTable[blobName].remove(my_id)
                for elem in checkTable[blobName]:
                    mapPIDtoIO[elem].set()
                checkTable.pop(blobName)
            
        full_blob_name = blobName.split(".")
        proc_blob_name = full_blob_name[0] + "_" + str(blockedID) + "." + full_blob_name[1]
        with open(proc_blob_name, "wb") as my_blob:
            my_blob.write(blob_val)
    else:
        fReadname = message["value"]
        fRead = open(fReadname,"rb")
        value = fRead.read()
        blob_client.upload_blob(value, overwrite=True)
        blob_val = "none"
    
    messageToRet = json.dumps({"value":"OK"})

    clientSocket_.send(messageToRet.encode(encoding="utf-8"))
    ####### TEST IF IMPROVE THE SPEED #######
    # clientSocket_.close()

def IOThread():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        threading.Thread(target=performIO, args=(clientSocket,)).start()

def run():
    # serverSocket: socket 
    # actionModule:  the module to execute
    global actionModule
    global numCores
    global results
    # Set the core of mxcontainer
    numCores = 16
    affinity_mask = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
    os.sched_setaffinity(0, affinity_mask)
    numFunctions = 1

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
            if "numCores" in message:
                numCores = int(message["numCores"])

                result = {"Response": "Ok"}
                if "affinity_mask" in message:
                    affinity_mask = message["affinity_mask"]
                    os.sched_setaffinity(0, affinity_mask)
                msg = json.dumps(result)
                responseFlag = True

            # Node Controller: Test
            if "printInfo" in message:
                result["affinity_mask"] = list(affinity_mask)
                result["numCores"] = numCores
                msg = json.dumps(result)
                responseFlag = True

            if "numFunctions" in message:
                numFunctions = int(message["numFunctions"])
                
        if responseFlag == True:
            sendResponse(clientSocket,  result)
            continue

        results = []
        threads = []
        
        for i in range(numFunctions, 0, -1):
            t1 = time.time()
            """while(threading.active_count() > numCores):
                print("ACTIVE THREAD")
                pass"""

            threadToAdd = threading.Thread(target=myFunction, args=(t1, ))
            threads.append(threadToAdd)
            threadToAdd.start()

        for thread in threads:
            thread.join()

        sendResponse(clientSocket, results)

if __name__ == "__main__":
    # main program
    run()
