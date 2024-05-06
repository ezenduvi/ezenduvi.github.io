import socket
import json
import sys
import uuid
import random
import time
import hashlib

gossipTimeout = 60
consensusTimeout = 180
statTimeout = 10
validateTimeout = 30
DIFFICULTY = 8

# Round-robin index for load balancing
rr_index = 0

# Load balancing using round-robin
def get_peer(peer_list):
    global rr_index
    peer = peer_list[rr_index]
    rr_index = (rr_index + 1) % len(peer_list)
    return peer 

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <hostname> <port>")
        return

    wellKnownHostName = sys.argv[1]
    wellKnownPort = int(sys.argv[2])
    
    #instantiate variables for tracking events
    ids = [] #store list of message ids seen before
    peers = []
    statReplys = []
    myChain = [] 
    missingBlocks = [] #used to track the blocks we have not received after get block requests are sent out
    mostCommonReply = [] #used to track which peers share the same height/hash combination
    invalidBlocks = [] #used to track if our peer has an invalid chain, track this so we dont rechoose peers that host this chain
    
    chainHeight = 0
    #boolean to track state
    invalid = False
    startedGetBlocks = False
    doingConsensus = False

    print("Creating a UDP socket")
    # Create a UDP socket for server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 8150))
    
    
    myHostName = socket.gethostname()
    ip = socket.gethostbyname(myHostName)
    myPort = 8150
    print(f"My a3Server is listening on {myHostName}:{myPort}")

    messageId = str(uuid.uuid4())
    ids.append(messageId)       
    # Define the JSON message
    message = {
        "type": "GOSSIP",
        "host": ip,
        "port": myPort,
        "id": messageId,
        "name": "Tester3000"
    }

    # Convert the message to JSON format
    json_message = json.dumps(message)

    # Send the JSON-formatted gossip to the well known host
    try:
        server_socket.sendto(json_message.encode("utf-8"), (wellKnownHostName, wellKnownPort))
    except Exception as e:
        print(f"An error occurred sending gossip to well-Known host: {e}")
    
    print("sent")
    
    #set re-Gossip time
    reGossipTime = time.time() + gossipTimeout
    
    #set consensus time to do the first consensus after 40 seconds
    consensusTime = time.time() + 40
    
    #set statReplyTime
    statReplyTime = statTimeout
    
    #set checkAllblocksreceived time
    blocksTime = validateTimeout

    while True:
        try:
            #reGossip every reGossipTime seconds
            if time.time() >= reGossipTime:
                #if you haven't received a gossip from a peer in more than 2 minutes, remove it from the list
                for i in peers:
                    if(((i["lastTime"]) + 120) <= (time.time())):
                        peers.remove(i)
                     
                messageId = str(uuid.uuid4())
                ids.append(messageId)       
                # Define the JSON message
                message = {
                    "type": "GOSSIP",
                    "host": ip,
                    "port": myPort,
                    "id": messageId,
                    "name": "Tester3000"
                }
                
                try:
                    # Convert the message to JSON format
                    json_message = json.dumps(message)
                    
                    #repeat gossip message to 3 of my known peers and send to fewer is we dont have 3 peers
                    if len(peers) >=3:
                        randomThree = random.sample(peers, 3)
                        for item in randomThree:
                            #print(f"sending reGOSSIP message to {item['host']}:{item['port']}")
                            server_socket.sendto(json_message.encode("utf-8"), (item['host'], item['port']))
                    else:
                        for item in peers:
                            #print(f"sending reGOSSIP message to {item['host']}:{item['port']}")
                            server_socket.sendto(json_message.encode("utf-8"), (item['host'], item['port']))
                    
                    reGossipTime = time.time() + gossipTimeout
                except Exception as e:
                    print(f"An error occurred sending re-gossip to peers in our peer list: {e}")
                
            #start consensus
            if time.time() >= consensusTime:
                if not doingConsensus:
                    print("STARTING CONSENSUS\n")
                    if len(peers) > 0:
                        #reset all our state because we are starting consensus again
                        global rr_index
                        myChain = []
                        sortedChain = [] #myChain[] but sorted by height to make hash validation easier
                        mostCommonReply = []
                        chainHeight = 0
                        doingConsensus = True
                        invalid = False
                        rr_index = 0
                        
                        #build stat message
                        statMessage = {
                            "type": "STATS"
                        }
                        
                        try:
                            statMessage = json.dumps(statMessage)
                            #send 
                            for item in peers:
                                print(f"sending STAT message to {item['host']}:{item['port']}")
                                server_socket.sendto(statMessage.encode("utf-8"), (item['host'], item['port']))
                            
                            consensusTime = time.time() + consensusTimeout
                            statReplyTime = time.time() + statTimeout
                        except Exception as e:
                            print(f"An error occurred sending stat message to all peers in peer list: {e}")
            
            #use the current stat replys we have gotten to do consensus after statReplyTime has passed
            if time.time() >= statReplyTime:
                if len(statReplys) > 0:
                    #incase there is a peer with an invalid chain, create a new list withouth that peer so we dont keep getting the same invalid chain
                    new_statReplys = []
                    added = False #use this to check if the new list is not empty
                
                    for i in invalidBlocks:
                        for reply in statReplys:
                            if i != reply["hash"]:
                                added = True
                                new_statReplys.append(reply)

                    #if new_statReply list is not empty then replace our old statreply list with the new one
                    if added:
                        statReplys = new_statReplys
                    
                    #find max height in statreplys list
                    maxHeight = max(int(reply["height"]) for reply in statReplys)
                    
                    #get list of statreplys with max height
                    maxHeightReplys = [reply for reply in statReplys if reply["height"] == maxHeight]  
                    
                    #Initializes an empty dictionary occurrences to count occurrences of combinations of "height" and "hash".
                    occurrences = {}
                    for reply in maxHeightReplys:
                        key = (reply["height"], reply["hash"])
                        occurrences[key] = occurrences.get(key, 0) + 1
                        
                    #find the combination of maxheight and hash with the most occurrences
                    mostCommonCombination = max(occurrences, key=occurrences.get)
                    
                    #find the statReply with most occurrences in maxHeightReplys
                    mostCommonReply = [reply for reply in maxHeightReplys if (reply["height"], reply["hash"]) == mostCommonCombination]
                    print(f"THIS IS THE LIST OF PEERS WE WILL BE DISTRIBUTING GETBLOCK REQUESTS TO: {mostCommonReply}")
                    
                    print("sending GET_BLOCK requests")
                    try:
                        #send get_block requests distributedly to peers in mostCommonReply list
                        for i in range(maxHeight):
                            getBlockReq = {
                                "type": "GET_BLOCK",
                                "height": i
                            }
                            
                            #add id for each block we have so that we can remove these ids later on and know which blocks we need to rerequest
                            missingBlocks.append(i)
                            
                            #use get_peer to load balance which peer to send requests to                    
                            chosenOne = get_peer(mostCommonReply)
                            
                            newGetBlockReq = json.dumps(getBlockReq)
                            server_socket.sendto(newGetBlockReq.encode("utf-8"), (chosenOne["host"], chosenOne["port"]))
                    except Exception as e:
                        print(f"An error occurred sending get_block requests to peers: {e}")
            
                    startedGetBlocks = True
                    statReplys = [] #clear statReplys list because we are done with the current consensus
                    statReplyTime = time.time() + statTimeout 
                    blocksTime = time.time() + validateTimeout
                    
            
            #check if we have gotten all blocks
            if time.time() >= blocksTime:
                if startedGetBlocks:
                    #check if we have gotten all blocks         
                    if len(missingBlocks) > 0:
                        #we haven't received all blocks so resend getBlock for blocks we dont have
                        print("\nWE DID NOT RECEIVE ALL BLOCKS SO REREQUEST\n")
                        
                        for i in missingBlocks:
                            getBlockReq = {
                                "type": "GET_BLOCK",
                                "height": i
                            }
                            
                            try:
                                #use get_peer to load balance which peer to send requests to
                                chosenOne = get_peer(mostCommonReply)
                            
                                newGetBlockReq = json.dumps(getBlockReq)
                                server_socket.sendto(newGetBlockReq.encode("utf-8"), (chosenOne["host"], chosenOne["port"]))
                            except Exception as e:
                                print(f"An error occurred trying to re-request lost get-block request: {e}")

                        print(f"WE CURRENTLY HAVE {len(myChain)} BLOCKS. REREQUESTING REMAINING BLOCKS...")
                            
                    else:
                        #we have received all blocks
                        print("\nWE RECEIVED ALL BLOCKS. VALIDATING...\n")

                        #sort chain
                        sortedChain = sorted(myChain, key=lambda x: x['height'])
                        
                        #now assign mychain to sorted chain
                        myChain = sortedChain
                        chainHeight = len(myChain)
                    
                        #try to validate block 0 and block 1
                        for i in range(len(sortedChain)):
                            blockObj = sortedChain[i]
                            m = hashlib.sha256()
                            
                            if i != 0:
                                prevBlock = sortedChain[i-1]
                                m.update(prevBlock["hash"].encode())
                                
                            m.update(blockObj["minedBy"].encode())
                            for item in blockObj["messages"]:
                                #validate length of each message
                                if len(item) <= 20:
                                    None
                                else:
                                    print("MESSAGE HAS AN INVALID LENGTH\n")
                                    invalid = True
                                    #store hash of most recent block, so we can remove all peers of the same hash from statreply list because those peers have an invalid chain
                                    blockObj = sortedChain[len(sortedChain)-1]
                                    invalidBlocks.append(blockObj["hash"])
                                    break
                                m.update(item.encode())
                            if(invalid):
                                break
                            timestamp = int(blockObj["timestamp"])
                            m.update(timestamp.to_bytes(8, 'big')) # when
                            m.update(blockObj["nonce"].encode()) # nonce

                            #validate length of messages list
                            if len(blockObj["messages"]) >= 1 and len(blockObj["messages"]) <= 10:
                                None
                            else:
                                print("BLOCK IS MESSAGES INVALID\n")
                                invalid = True
                                #store hash of most recent block, so we can remove all peers of the same hash from statreply list because those peers have an invalid chain
                                blockObj = sortedChain[len(sortedChain)-1]
                                invalidBlocks.append(blockObj["hash"])
                                break   
                            
                            #validate length of each nonce       
                            if len(blockObj["nonce"]) <= 40:
                                None
                            else:
                                print("NONCE IS LENGTH INVALID\n")
                                invalid = True
                                #store hash of most recent block, so we can remove all peers of the same hash from statreply list because those peers have an invalid chain
                                blockObj = sortedChain[len(sortedChain)-1]
                                invalidBlocks.append(blockObj["hash"])
                                break 
                            
                            #validate hash
                            hash = m.hexdigest()
                            if hash == blockObj["hash"]:
                                None
                            else:
                                print("BLOCK IS HASH INVALID\n")
            
                                #invalid block
                                invalid = True
                                #store hash of most recent block, so we can remove all peers of the same hash from statreply list because those peers have an invalid chain
                                blockObj = sortedChain[len(sortedChain)-1]
                                invalidBlocks.append(blockObj["hash"])
                                break
                            
                            #validate difficulty
                            if hash[-1 * DIFFICULTY:] != '0' * DIFFICULTY:
                                invalid = True
                                
                                #store hash of most recent block, so we can remove all peers of the same hash from statreply list because those peers have an invalid chain
                                blockObj = sortedChain[len(sortedChain)-1]
                                invalidBlocks.append(blockObj["hash"])
                                
                                print("Block was not difficult enough: {}".format(hash))
                                break
                                                            
                        if(invalid):
                            #go back to statReplys to find next longest chain
                            print("RESTARTING CONSENSUS\n")
                            startedGetBlocks = False
                            consensusTime = time.time()
                            doingConsensus = False
                        else:
                            #we are ready to serve STATREPLY and serve GETBLOCK replys
                            doingConsensus = False #we are done with consensus until we are forced to do it or timer runs out
                            startedGetBlocks = False #don't keep validating if we have a valid chain already
                            consensusTime = time.time() + consensusTimeout #once done with consensus, give 3 minutes so we can query chain
                            print("WE ARE DONE WITH CONSENSUS\n")
                
                blocksTime = time.time() + validateTimeout    
            
            try:            
                #start receiving messages
                data, addr = server_socket.recvfrom(4096)
                
                response = data.decode("utf-8")
                json_message = json.loads(response)
                
                #print(f"Received {json_message.get('type')} data from {addr}")
                
                if json_message.get("type") == "GOSSIP":
                    #check if i have seen id before
                    if json_message.get("id") in ids:
                        #do nothing if you have already gossiped this message before
                        None
                    else:
                        #select 3 peers you are tracking and repeat to them to originator and not sender
                        if len(peers) >=3:
                            randomThree = random.sample(peers, 3)
                            for item in randomThree:
                                #print(f"sending GOSSIP message to {item['host']}:{item['port']}")
                                server_socket.sendto(json.dumps(json_message).encode("utf-8"), (item['host'], item['port']))
                                #print("sent successfully")
                        else:
                            for item in peers:
                                #print(f"sending GOSSIP message to {item['host']}:{item['port']}")
                                server_socket.sendto(json.dumps(json_message).encode("utf-8"), (item['host'], item['port']))
                                #print("sent successfully")
                
                    #send gossip reply back to who you received a gossip from
                    reply = {
                        "type": "GOSSIP_REPLY",
                        "host": ip,
                        "port": myPort,
                        "name": "Tester3000"
                    }
                    # Convert the message to JSON format
                    json_message = json.dumps(reply)
                    server_socket.sendto(json_message.encode("utf-8"), (addr[0], addr[1]))
                    
                    #i just received a gossip from a peer, so add/(update time) peer to peer list
                    found = False
                    
                    #iterate through and if peer already in our list of peers then just update time we last received a gossip from peer
                    for i in peers:
                        if((addr[0] == i["host"]) and (addr[1] == i["port"])):
                            i["lastTime"] = time.time()
                            found = True
                            
                    peer = {
                    "host": addr[0],
                    "port": addr[1],
                    "lastTime": time.time()
                    }
                    
                    #if peer has not sent us a message before, then add it to the list of peers
                    if not found:
                        peers.append(peer)
                    
                elif json_message.get("type") == "GOSSIP_REPLY":
                    #add peer to list or update time
                    found = False
                    for i in peers:
                        if((json_message.get("host") == i["host"]) and (json_message.get("port") == i["port"])):
                            i["lastTime"] = time.time()
                            found = True
                            
                    peer = {
                    "host": json_message.get("host"),
                    "port": json_message.get("port"),
                    "lastTime": time.time()
                    }
                    
                    if not found:
                        peers.append(peer)
                
                elif json_message.get("type") == "STATS_REPLY":
                    if (json_message.get("height") == None) or (json_message.get("hash") == None):
                        None
                    else:
                        statReply = {
                            "host": addr[0],
                            "port": addr[1],
                            "height": json_message.get("height"),
                            "hash": json_message.get("hash")
                        }
                        statReplys.append(statReply)
                
                elif json_message.get("type") == "GET_BLOCK_REPLY":
                    if (json_message.get("height") == None) or (json_message.get("nonce") == None) or (json_message.get("minedBy") == None):
                        None
                    else:
                        myChain.append(json_message)
                        
                        #once a block has been added, remove its index from the missingBlocks array so that we are left with the indexes of blocks we did not receive in the list
                        # Check if the height exists in missingBlocks before removal
                        height = json_message.get("height")
                        if height in missingBlocks:
                            missingBlocks.remove(height)
                        else:
                            print(f"Height {height} not found in missingBlocks list.")
                    
                elif json_message.get("type") == "GET_BLOCK":
                    block_value = {   
                            'type': 'GET_BLOCK_REPLY',
                            'hash': None,
                            'height': None,
                            'messages': None,
                            'minedBy': None,
                            'nonce': None,
                            'timestamp': None
                        }
                    
                    if json_message.get("height") < chainHeight:
                        #get block at height position
                        block_value = myChain[json_message.get("height")]
                        
                    new_block_reply = json.dumps(block_value)
                    
                    server_socket.sendto(new_block_reply.encode("utf-8"), (addr[0], addr[1]))
                
                elif json_message.get("type") == "STATS": 
                    if chainHeight > 0:
                        #get block at height position
                        block_value = myChain[len(myChain) - 1]
                        
                        stats_reply = {
                            "type": "STATS_REPLY",
                            "height": len(myChain),
                            "hash": block_value["hash"]
                        }
                        
                        new_stats_reply = json.dumps(stats_reply)
                    
                        server_socket.sendto(new_stats_reply.encode("utf-8"), (addr[0], addr[1]))
                    else:
                        print("CANNOT PROVIDE STATS REPLY BECAUSE WE ARE NOT DONE WITH CONSENSUS")
                
                elif json_message.get("type") == "CONSENSUS": 
                    print("Type is CONSENSUS")
                    
                    if doingConsensus:
                        print("WE ARE ALREADY DOING A CONSENSUS")
                    else:
                        consensusTime = time.time()
                        
                elif json_message.get("type") == "ANNOUNCE":
                    if (not doingConsensus) and (chainHeight > 0):
                        try:
                            block_value = {   
                                'type': 'GET_BLOCK_REPLY',
                                'hash': json_message.get("hash"),
                                'height': json_message.get("height"),
                                'messages': json_message.get("messages"),
                                'minedBy': json_message.get("minedBy"),
                                'nonce': json_message.get("nonce"),
                                'timestamp': None
                            }
                            blockValid = True
                            m = hashlib.sha256()
                            #get previous block to add to hash (m)
                            if block_value["height"] != 0:
                                prevBlock = sortedChain[chainHeight-1]
                                m.update(prevBlock["hash"].encode())
                            
                            m.update(block_value["minedBy"].encode())
                            for item in block_value["messages"]:
                                #validate length of each message
                                if len(item) <= 20:
                                    None
                                else:
                                    print("MESSAGE HAS AN INVALID LENGTH\n")
                                    blockValid = False
                                m.update(item.encode())
                            m.update(block_value["nonce"].encode()) # nonce
                            
                            #validate length of messages list
                            if len(block_value["messages"]) >= 1 and len(block_value["messages"]) <= 10:
                                None
                            else:
                                print("BLOCK IS MESSAGES INVALID\n")
                                blockValid = False   
                            
                            #validate length of each nonce       
                            if len(block_value["nonce"]) <= 40:
                                None
                            else:
                                print("NONCE IS LENGTH INVALID\n")
                                blockValid = False
                    
                            #validate difficulty
                            hash = m.hexdigest()
                            if hash[-1 * DIFFICULTY:] != '0' * DIFFICULTY:
                                blockValid = False
                                print("Block was not difficult enough: {}".format(hash))
                            
                            if blockValid:
                                if hash == block_value["hash"]:
                                    #block is valid and should be added to the top of the chain else discard it
                                    
                                    #get hashbase but with the addition of timestamp because Announce didn't come with a timestamp
                                    m = hashlib.sha256()
                                    if block_value["height"] != 0:
                                        prevBlock = sortedChain[chainHeight-1]
                                        m.update(prevBlock["hash"].encode())
                                        
                                    m.update(block_value["minedBy"].encode())
                                    for item in block_value["messages"]:
                                        m.update(item.encode())
                                    block_value["timestamp"] = time.time()
                                    m.update(block_value["timestamp"].to_bytes(8, 'big')) # when
                                    m.update(block_value["nonce"].encode()) # nonce
                                    hash = m.hexdigest()
                                    block_value["hash"] = hash
                                    
                                    #add block to chain
                                    sortedChain.append(block_value)
                                    print("WE SUCCESSFULLY ADDED A BLOCK TO THE CHAIN\n")
                            
                        except Exception as e:
                            print(f"something went wrong announcing blocks: {e}")
                                          
            except ValueError as ve:
                print(f"message received is not proper JSON format: {ve}")
            
            except socket.error as se:
                print(f"Socket error: {se}")
            
            except Exception as e:
                print(f"some other error occurred while receiving messages: {e}")
                
        except Exception as e:
            print(f"some other error occurred throughout our while block: {e}")
         
            
if __name__ == "__main__":
    main()
