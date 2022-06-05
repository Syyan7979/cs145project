import socket # For the low-level network socket module, The socket module provides various objects, constants, functions and related exceptions for building full-fledged network applications including client and server programs.
import argparse # The module is required for parsing the terminal inputs required in the implementation.
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
    start = True # Set to true at the start but when it receives the first packet from the probing of the network this will be set to false.
    congestionAvoidance = False # CongestionAvoidance state starts when we already received the acknowledgement of the first packet we sent to probe the server and we've calculated the size of the packets to be sent out as well as the proccessing time of the server when it receives the first packet. Initially set to false and will be updated when firstSuccess variable is true.

    MSS = 1 # will indicate the number of characters to be sent out and will be updated accordingly as the progrma runs depending on the scenario.
    startPos = 0 # Starting position of the characters to be sent out in data stored in the full_payload variable.

    seqNum = 0 # Initially set to 0 and will be incremented by one for every successful packet received.
    ackNumber = -1 # Initially set to -1 and will be updated to the value of the recent acknowledgement sent by the server.

    # Timer calculation related variables
    timeout_interval = 95 # Timer interval is intially set to 95 which is the minimum requirement for the all the data payload to be transmitted by the transmitter to the server.

    while startPos < len(full_payload): # will continuously iterate until startpos variable value is greater than that of the length of the payload which entails that we have sent out as startPos is always updated by adding the current size of the packet sent out to it or simply startPos += MSS.
        clientSocket.settimeout(timeout_interval) # we specifiy the timeout of our socket when receiving packets as the sender can decide to not send anything when it drops a packet that was not in compliance to the requirements or dropped by the queue when it is already full using the settimeout function built in the socket module.

        z = 1 if startPos + MSS >= len(full_payload) else 0 # z gets 1 whenever the currentPosition + the size of the payload is greater than the length of the whole data.
        endpos = startPos + MSS # endPos indicates the position in the data stored in the full_payload variable that will be included in the packet that sender sends out to the server.
        if startPos + MSS >= len(full_payload): # will check if the startPos + MSS is greater or equal to the length of the data stored in the full_payload variable to ensure data read doesn't go out of index bounds.
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:]}".encode("ascii") # if the startPos + MSS is greater or equal to the length of the data stored in the full_payload then we send a formatted string that contains the format ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{data starting at the position stored in startPos and the up to the end of the data stored in the full_payload variable} which is encoded using ascii.
        else:
            dataPacket = f"ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{full_payload[startPos:endpos]}".encode("ascii") # else  we send a formatted string that contains the format ID{uniqueID}SN{seqNum:07d}TXN{transactionID:07d}LAST{z}{data starting at the position stored in startPos and the up to the position stored in endPos of the data stored in the full_payload variable} which is encoded using ascii.
        clientSocket.sendto(dataPacket, (IP_address, receiverPort)) # we then send the encoded message stored in the dataPacket variable to the server through the use of the sendto function built in the socket module.

        # we then initiate the try-except mechanism of our program since we don't want our program to stop when we encounter a socket.timeout error which will occur given that we've updated the value of the timeout of our socket from none to the value in timeout_interval in line 52.
        try:
            # we first try hearing a response from the server and if it doesn't respond in the alloted time then it must be the case that the packet we sent was wrong or got dropped by the queue.
            ackPacket = clientSocket.recvfrom(4096)[0].decode() # sender waits for the response from the server and if response occurs then we get only the value at index 0 since this is the message from the (byte, address) value pair that the recvfrom() function built in the socket module returns.
            ackNumber, checkSum = ParseAckMessage(ackPacket, compute_checksum(dataPacket.decode("ascii"))) # we then call the ParseAckMessage() function with input arguments ackPacket and the return value of the compute_checksum of the dataPacket, which just parses the message received from the server to get the ack number and checks if the checkSum sent by the receiver and the checkSum of the dataPacket you sent are the same.

            if ((start and ackNumber == seqNum and checkSum) or (congestionAvoidance and ackNumber == seqNum and checkSum)): # we then check for 2 cases to be true when (start and ackNumber == seqNum and checkSum) holds or (congestionAvoidance and ackNumber == seqNum and checkSum), since this implies that ackNumber is equal to seqNum and checkSum of received and sent dataPacket are the same for the 2 different states.
                startPos += MSS # we then update the position of the value stored in the startPos variable is we know that the
                seqNum += 1 # we also increase seqNum by 1 since successful send-receive of dataPacket and acknowledgement to and from the server.

            if (start): # emulation of probing the server with a packet that has a payload of only 1 character to get the processing time of that data.
                timeout_interval = time.time() - sendStart # we get the processing time for the packet processing which will be used in the calculation of the MSS
                MSS = int(len(full_payload)//(95/timeout_interval)) # note that according to ma'am Zabala there is no recalculation of values mid-transaction then we can assume that size is consistent all throughout which we can get a ball-park estimation using the formula len(full_payload)//(95/timeout_interval), which will ensure that within the 120 seconds time we can send the packets of size MSS consistently at a good time interval.
                timeout_interval += 0.125 # we increase the RTT by a bit since timeout_interval should be greater than RTT, which also ensures that calculation occurs within RTT and timeout will not prematurely occur.
                congestionAvoidance = True # we can now change the state to Congestion Avoidance by setting the congestionAvoidance variable to True since we are now done with the probing/start state.
                start = False # as mentioned in explanation in line 73 we change from probing/start state to the Congestion Avoidance state.
        except socket.timeout:
            # timeout occurs hence we need to resubmit a new packet that will be accepted by the server.
            if congestionAvoidance == True: # while in congestionAvoidance state we update MSS then retransmit with the new size of MSS.
                MSS = max(1, MSS-1) # MSS is updated by decreasing it by 1 since we made the wrong estimation earlier but it was still be close to the correct value, hence we only decrease it little by little so that efficiency is not compromised

def compute_checksum(packet):
    """
        Function compute_checksum takes in one input argument and returns the checksum of the input argument.
        It is getting the checksum of the dataPacket sent by the receiver to the server.
    """
    return hashlib.md5(packet.encode('utf-8')).hexdigest() # uses the md5() function built in the hashlib module on the data packet and the the returned value is returned by the compute_checksum function.

def ParseAckMessage(message, packetSent):
    """
        Function ParseAckMessage takes in two input arguments and returns two output arguments.
        It parses the message sent by the server to break it down into the ackNumber and the checkSum and then compares that checkSum to the checkSum of the sent dataPacket by the sender.
    """
    ackNumber = int(message[3:10]) # ackNumber is parsed using the characters located in position 3 to 9 in the ackMessage which is then casted using the int() function to get the integer version of it instead of a string.
    checkSum = True if packetSent == message[23:] else False # checkSum variable is set to True if characters located in position 23 to end of ackMessage is equal to the checkSum of the dataPacket sent by the sender to the server, otherwise it is set to False.
    return ackNumber, checkSum # ackNumber and checkSum are then returned.

def InputParsing():
    """
        Function InputParsing takes in no input argument(s) and returns no output argument(s).
        It parses the values entered in the terminal during the start of the program.
    """
    parser = argparse.ArgumentParser(description = 'sender.py program used for sending data packets to a server')
    parser.add_argument('-f', '--filePath', metavar='', nargs ='?', type=str, help = "denotes the filename of the payload (default value: 09cfd2c6.txt)", default = '09cfd2c6.txt')
    parser.add_argument('-a', '--ipAddress', metavar='', nargs ='?', type=str, help = "denotes the IP address of the receiver to be contacted (default value: 10.0.1.175; this is also the IP of the receiver that you will use when developing your project)", default = '10.0.1.175')
    parser.add_argument('-s', '--receiver_Port', metavar='', nargs ='?', type=int, help = "denotes the port used by the receiver (default value: 9000; this is also the port of the receiver that you will use when developing your project)", default = 9000)
    parser.add_argument('-c', '--sender_Port', metavar='', nargs ='?', type=int, help = "denotes the port used by the sender; this port is assigned per student, given at the same time as the unique ID (6707)", default = 6707)
    parser.add_argument('-i', '--unique_ID', metavar='', nargs ='?', type=str, help = "denotes the unique ID; this ID is assigned per student, given at the same time as the port assigned to the student (default value: 09cfd2c6)", default = '09cfd2c6')
    args = parser.parse_args()

    global file_path # global file_path is needed in the function as we need to update file_path in the function and this ensures that no localbound error occurs
    global IP_address # global IP_address is needed in the function as we need to update IP_address in the function and this ensures that no localbound error occurs
    global receiverPort # global receiverPort is needed in the function as we need to update receiverPort in the function and this ensures that no localbound error occurs
    global senderPort # global senderPort is needed in the function as we need to update senderPort in the function and this ensures that no localbound error occurs
    global uniqueID # global uniqueID is needed in the function as we need to update uniqueID in the function and this ensures that no localbound error occurs

    file_path = args.filePath
    IP_address = args.ipAddress
    receiverPort = args.receiver_Port
    senderPort = args.sender_Port
    uniqueID = args.unique_ID

    InitializeClientSocket(senderPort) # calling the InitializeClientSocket() function with senderPort as the input argument to intialize the clientSocket socket variable.
    InitializeData(file_path) # calling the InitializeData() function with file_path as the input argument to initialize the file_path variable.

def InitializeClientSocket(portNum):
    """
        Function InitializeClientSocket takes in one input argument and returns no output argument(s).
        It is responsible for intializing the socket that the sender will use when communicating with the server.
    """
    global clientSocket # global clientSocket is needed in the function as we need to update clientSocket in the function and this ensures that no localbound error occurs.
    clientSocket.bind(('', portNum)) # clientSocket is now bound to the address of the computer at the port specified in the portNum variable.

def InitializeData(pathName):
    """
        Function InitializeData takes in one input argument and returns no output argument(s).
        it opens the file stored in the pathName variable and stores the data in the file to a variable useable in the program.
    """
    global full_payload # global full_payload is needed in the function as we need to update full_payload in the function and this ensures that no localbound error occurs
    file = open(pathName, 'r') # open() function opens the file stored in the specified pathName, and returns it as a file object which is then stored in the variable file.
    full_payload = file.read() # read() method returns the specified number of bytes from the file and is then stored in the full_payload global variable.
    file.close() # close() method of a file object flushes any unwritten information and closes the file object, after which no more writing can be done.

if __name__ == "__main__":
    InputParsing()
    Protocol()
