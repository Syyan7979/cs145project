import socket # For the low-level network socket module
import sys # For parsing the comand line input
import os
import time

# Default values and can be updated
file_path = "09cfd2c6.txt"
IP_address = "10.0.1.175"
receiverPort = 9000
senderPort = 6707
uniqueID = "09cfd2c6"

# initialization of sockets for server and client
    # client
clientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# Data value
full_payload = ""

def Protocol():

    # Sending Intent Message
    intentMessage = f"ID{uniqueID}".encode("ascii")
    clientSocket.sendto(intentMessage, (IP_address, receiverPort))

    # Receiving Accept Message
    acceptMessage = clientSocket.recvfrom(1024)[0]
    transactionID = int(acceptMessage.decode())
    print(transactionID)
    sendStart = time.time()

    # States
    slowStart = True
    congestionAvoidance = False
    stasis = False

    prevMSS = 1
    MSS = 1
    startPos = 0

    seqNum = 0

    # Timer calculation related variables
    estimate_time = 5 # intializing estimated RTT to 3, which will be updated accordingly once we get a sample RTT
    DevRTT = estimate_time/2 # initializing DevRTT to initial estimated RTT divided by 2, which will be updated accordingly once we get a sample RTT
    timeout_interval = 5
    alpha = 0.125
    beta = 0.25

    while startPos < len(full_payload):
        # Responsible for setting the timeout value of our socket
        clientSocket.settimeout(timeout_interval)
        print(seqNum)

        # z gets 1 whenever the currentPosition + the size of the payload is greater than the lenght of the whole data
        z = 1 if startPos + MSS >= len(full_payload) else 0
        endpos = startPos + MSS
        if startPos + MSS >= len(full_payload):
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:]}".encode("ascii")
        else:
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:endpos]}".encode("ascii")
        print(f"startPos: {startPos}, endpos: {endpos}")
        clientSocket.sendto(dataPacket, (IP_address, receiverPort))
        start = time.time()

        try:
            ackPacket = clientSocket.recvfrom(4096)[0].decode()
            end = time.time() # returns the time for when the
            ackNumber, checkSum = ParseAckMessage(ackPacket)

            if (slowStart and ackNumber == seqNum):
                prevMSS = MSS
                startPos += MSS
                MSS *= 2
                seqNum += 1
            elif (congestionAvoidance and ackNumber == seqNum):
                prevMSS = MSS
                startPos += MSS
                MSS += 1
                seqNum += 1
            else:
                startPos += MSS
                seqNum += 1

            SampleRTT = end - start
            DevRTT = ((1-beta) * DevRTT) + (beta*abs(SampleRTT-estimate_time))
            estimate_time = ((1-alpha) * estimate_time) + (alpha * SampleRTT)
            timeout_interval = estimate_time + (4*DevRTT)
        except socket.timeout:
            if ((slowStart == True) and (congestionAvoidance == False) and (stasis == False)):
                MSS = prevMSS
                slowStart = False
                congestionAvoidance = True
            elif ((slowStart == False) and (congestionAvoidance == True) and (stasis == False)):
                MSS = prevMSS
                congestionAvoidance = False
                stasis = True
        print(f"elapsed time: {time.time()-sendStart}")

def ParseAckMessage(message):
    ackNumber = int(message[3:10])
    checkSum = message[23:]
    return ackNumber, checkSum

def InputParsing():
    args = sys.argv[1:]

    global file_path
    global IP_address
    global receiverPort
    global senderPort
    global uniqueID

    for i in range(0, len(args), 2):
        if (args[i] == "-f"):
            file_path = args[i+1]
        if (args[i] == "-a"):
            IP_address = args[i+1]
        if (args[i] == "-s"):
            receiverPort = int(args[i+1])
        if (args[i] == "-c"):
            senderPort = int(args[i+1])
        if (args[i] == "-i"):
            uniqueID = args[i+1]

    InitializeClientSocket(senderPort)
    InitializeData(file_path)

def InitializeClientSocket(portNum):
    global clientSocket
    clientSocket.bind(('', portNum))

def InitializeData(pathName):
    global full_payload
    file = open(pathName, 'r')
    full_payload = file.read()
    file.close()

if __name__ == "__main__":
    InputParsing()
    Protocol()
