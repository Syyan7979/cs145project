import socket # For the low-level network socket module, The socket module provides various objects, constants, functions and related exceptions for building full-fledged network applications including client and server programs.
import sys # The module is required for parsing the terminal inputs required in the implementation.
import time # The module is required to keep track of the time difference between sender sending the packet and sender receiving the server's acknowledgement packet
import hashlib # The module is required for the sender to check if the received acknowledgement's checksum is equivalent to the checksum of the packet it sent.

# Default values and can be updated
file_path = "09cfd2c6.txt" # Default value if in the case that user does not include '-f <file_path>' as an input parameter in the terminal
IP_address = "10.0.1.175" # Default value if in the case that user does not include '-a <address specified>' as an input parameter in the terminal
receiverPort = 9000 # Default value if in the case that user does not include '-s <receiver's port number>' as an input parameter in the terminal
senderPort = 6707 # Default value if in the case that user does not include '-c <sender's port number>' as an input parameter in the terminal
uniqueID = "09cfd2c6" # Default value if in the case that user does not include '-i <user's unique ID>' as an input parameter in the terminal

# initialization of sockets for client
clientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Initialization of the sender's socket using the socket function defined in the socket module which returns a socket object whose methods implement the various socket system calls. Input parameters socket.AF_INET and socket.SOCK_DGRAM are respectively used for telling the function that it will be taking in IPv4 address string and the UDP port since server and sender are built on top of UDP.

# Data value
full_payload = "" # Initialization of full_payload variable which will be updated later when file path of data payload is specified or will use the default file specified in the file_path variable.

def Protocol():
    """
        Function Protocol takes in no input argument and does not return anything.
        It is responsible for doing the process of sending and receiving of packets to and from the server.
    """

    # Sending Intent Message
    intentMessage = f"ID{uniqueID}".encode("ascii") # intent message gets formatted using the format IDXXXXXXXXX where XXXXXXXXX is default ID or the ID entered as an input argument, which will then be encoded into ascii.
    clientSocket.sendto(intentMessage, (IP_address, receiverPort)) # intent message is then sent to the default IP address and port or to the ip address entered as an input argument using the sendto function of the socket module.

    # Receiving Accept Message
    acceptMessage = clientSocket.recvfrom(1024)[0] # we wait for the respond from the server as we get the value of our transactionID from the server and we get only the value at index 0 since this is the message from the (byte, address) value pair that the recvfrom() function built in the socket module returns.
    transactionID = int(acceptMessage.decode()) # transactionID variable is now set to the decoded message we received earlier stored in the acceptMessage variable.
    print(f"Transaction ID: {transactionID}") # we print a formatted string that contains info stored in the transactionID variable so that we can keep track of it in the TGRS.
    sendStart = time.time() # we now initialize the send start time given that when transactionID is sent by the server this implies that timer is starting. This will also help us when calculating processing time of first sent packet.

    # States
    congestionAvoidance = False

    firstSuccess = False
    start = True

    prevMSS = 1
    MSS = 1
    startPos = 0

    seqNum = 0
    ackNumber = -1

    # Timer calculation related variables
    timeout_interval = 95

    while startPos < len(full_payload):
        clientSocket.settimeout(timeout_interval) # we specifiy the timeout of our socket when receiving packets as the sender can decide to not send anything when it drops a packet that was not in compliance to the requirements or dropped by the queue when it is already full using the settimeout function built in the socket module.

        z = 1 if startPos + MSS >= len(full_payload) else 0 # z gets 1 whenever the currentPosition + the size of the payload is greater than the lenght of the whole data
        endpos = startPos + MSS
        print(startPos, endpos)
        if startPos + MSS >= len(full_payload):
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:]}".encode("ascii")
        else:
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:endpos]}".encode("ascii")
        clientSocket.sendto(dataPacket, (IP_address, receiverPort))
        start = time.time()

        try:
            ackPacket = clientSocket.recvfrom(4096)[0].decode()
            end = time.time() # returns the time for when the
            ackNumber, checkSum = ParseAckMessage(ackPacket, compute_checksum(dataPacket.decode("ascii")))

            if ((start and ackNumber == seqNum and checkSum) or (congestionAvoidance and ackNumber == seqNum and checkSum)):
                startPos += MSS
                seqNum += 1

            if (firstSuccess == False):
                timeout_interval = time.time() - sendStart
                MSS = int(len(full_payload)//(95/timeout_interval))
                timeout_interval += 0.125
                congestionAvoidance = True
                firstSuccess = True
                start = False


        except socket.timeout:
            if congestionAvoidance == True:
                MSS = max(1, MSS-1)


def compute_checksum(packet):
    return hashlib.md5(packet.encode('utf-8')).hexdigest()

def ParseAckMessage(message, packetSent):
    ackNumber = int(message[3:10])
    checkSum = True if packetSent == message[23:] else False
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
    full_payload = file.readline().strip()
    file.close()

if __name__ == "__main__":
    InputParsing()
    Protocol()
