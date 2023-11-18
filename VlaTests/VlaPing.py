
from scapy.all import sr1, srp1, srp, Raw
import sys
from IPv6ExtHdrVLA import IPv6ExtHdrVLA
from scapy.all import get_if_addr6, get_if_hwaddr, get_if_list
from scapy.layers.inet6 import UDP, IPv6
from scapy.layers.l2 import Ether
from Utils import createVlaPacket, getMacAddress
import time
from scapy.all import conf
from NRUtils import resolveHostVlaAddress, getCurrentHostVlaAddress, getDefaultMacAddress, getDefaultInterface

def test():

    ifacelist = get_if_list()
    print(ifacelist)
    ip = get_if_addr6(ifacelist[1])
    print(ip)
    mac = get_if_hwaddr(ifacelist[1])
    print(mac)
    print(conf.route)
    #print(conf.ifaces)

def getCommandLineArguments():
    try:
        targetHost = sys.argv[1]
        return targetHost
    except Exception():
        raise Exception("Pass Comandline Arguments Properly") 

def ping(targetHostId):
    # Create an VLA IP packet with an UDP Ping
    replyMessage = ""
    ifaceStatus, defaultInterface = getDefaultInterface()
    if(not ifaceStatus):
        replyMessage = "No network interfaces found for device"
        return (False, replyMessage, None)
    ethSrcStatus, ethSrc= getDefaultMacAddress()
    if(not ethSrcStatus):
        replyMessage = "mac address not found for current device"
        return (False, replyMessage, None)
    hostVlaStatus, hostVlaAddress, gatewayMac, message = getCurrentHostVlaAddress()
    if(not hostVlaStatus):
        replyMessage = "vla address for current Device Not found"
        return (False, replyMessage, None)

    targetVlaStatus, targetVlaAddress, gatewayMac, message = resolveHostVlaAddress(targetHostId)
    if(not hostVlaStatus):
        replyMessage = "vla address for target device %s not found".format(targetHostId)
        return (False, replyMessage, None)
    
    ethDst=gatewayMac
    vlaSrcList = hostVlaAddress
    vlaDstList = targetVlaAddress
    vlaCurrentLevel = len(hostVlaAddress) - 1
    dataPayload = "Ping Request"

    packet = createVlaPacket(ethDst, ethSrc, vlaSrcList, vlaDstList, vlaCurrentLevel, dataPayload)

    # Send the packet and wait for a response
    start_time = time.time()

    reply = srp1(packet,iface=defaultInterface)
    
    end_time = time.time()


    rtt = 0

    # Check if a response was received
   
    if reply:
        if(Ether in reply and IPv6 in reply):
            if reply[IPv6].nh == 48:
                #print("reply packet is ", reply)
                ipPayload = IPv6ExtHdrVLA(reply[IPv6].payload)
                if ipPayload[UDP] and ipPayload[UDP].sport == 50001:
                    replyMessage = "Ping  successful! " + ipPayload[Raw].load
                    rtt = end_time - start_time
                    return (True,replyMessage, rtt)
                else:
                    replyMessage = "Ping Failed UDP not found or UDP src port does not match "
            else:
                replyMessage =  "Vla not detected in reply"
        else:
            replyMessage = "Ping to failed. Unexpected response type."
    else:
        replyMessage = "No response from ping."
        return (False, replyMessage, rtt)

# Example usage
def main():
    targetHost = "00:aa:00:00:00:02"
    try:
        targetHost = getCommandLineArguments()
    except Exception as e:
            print("ping target not found as command line argument using default target : " +  e)
    (pingStatus,replyMessage, rtt) = ping()
    print(replyMessage)
    print("Round Trip Time is  {:.3f} ".format(rtt*1000))

if __name__ == "__main__":
    main()