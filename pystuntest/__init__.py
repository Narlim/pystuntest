from .stun_protocol import message
from .stun_protocol.attribute import ChangeRequestAttribute


import socket
import binascii
import logging
import netifaces

__version__ = '0.0.1'

log = logging.getLogger("pystuntest")


STUN_SERVERS = 'stun.miwifi.com'

DEFAULTS = {
    'stun_port': 3478,
    'source_ip': '0.0.0.0',
    'source_port': 54320
}


def b2a_hexstr(abytes):
    return binascii.b2a_hex(abytes).decode("ascii")


def get_local_address():
    ifaddresses = []
    interfaces = netifaces.interfaces()
    ifaddr_list = [netifaces.ifaddresses(i) for i in interfaces]
    for addrs in ifaddr_list:
        try:
            addr_info = addrs[netifaces.AF_INET]
            ifaddresses.append(addr_info[0]['addr'])
        except Exception:
            pass
    return ifaddresses


def stun_test(sock, host, port, message):
    retVal = {
        'Resp': False,
        'MappedAddress': None,
        'MappedPort': None,
        'ResponseOriginAddress': None,
        'ResponseOriginPort': None,
        'OtherAddress': None,
        'OtherPort': None,
        'XorMappedAddress': None,
        'XorMappedPort': None
    }
    # m = message.Message(message.MessageClass.REQUEST, message.MessageMethod.BINDING)
    trans_id = message.transaction_id
    data = message.pack()
    try:
        sock.sendto(data, (host, port))
    except socket.gaierror:
        retVal['Resp'] = False
        return retVal
    try:
        buf, _ = sock.recvfrom(2048)
        magic_cookie = buf[4:8]
        xor_port = buf[62:64]
        xor_address = buf[64:]
    except Exception:
        retVal['Resp'] = False
        return retVal
    if trans_id == buf[8:20]:
        xord_mapped_port = int(b2a_hexstr(bytes(m ^ x for m, x in zip(magic_cookie[:2], xor_port))), 16)
        xord_mapped_address_bytes = bytes(m ^ x for m, x in zip(magic_cookie, xor_address)) 
        xord_mapped_address = '.'.join([str(xord_mapped_address_bytes[0]),
                                        str(xord_mapped_address_bytes[1]),
                                        str(xord_mapped_address_bytes[2]),
                                        str(xord_mapped_address_bytes[3])])
        retVal['Resp'] = True
        retVal['MappedPort'] = int(b2a_hexstr(buf[26:28]), 16)
        retVal['MappedAddress'] = '.'.join([str(buf[28]), str(buf[29]), str(buf[30]), str(buf[31])])
        retVal['ResponseOriginPort'] = int(b2a_hexstr(buf[38:40]), 16)
        retVal['ResponseOriginAddress'] = '.'.join([str(buf[40]), str(buf[41]), str(buf[42]), str(buf[43])])
        retVal['OtherPort'] = int(b2a_hexstr(buf[50:52]), 16)
        retVal['OtherAddress'] = '.'.join([str(buf[52]), str(buf[53]), str(buf[54]), str(buf[55])])
        retVal['XorMappedPort'] = xord_mapped_port
        retVal['XorMappedAddress'] = xord_mapped_address
    
    return retVal
        

def get_nat_mapping(sock, host, port) -> (str, dict):
    log.debug('Do Mapping Test1')
    m = message.Message(message.MessageClass.REQUEST, message.MessageMethod.BINDING)
    ret_test1 = stun_test(sock, host, port, m)
    resp = ret_test1['Resp']
    log.debug(f"Mapping Test1 result: {ret_test1}")
    if resp:
        if ret_test1['OtherAddress'] is None:
            return 'Test Not Support', None
        else:
            local_addresses = get_local_address()
            XorMappedAddress = ret_test1['XorMappedAddress']
            XorMappedPort = ret_test1['XorMappedPort']
            if XorMappedAddress in local_addresses and XorMappedPort == 54320:
                return 'Endpoint-Independent Mapping', ret_test1
            else:
                log.debug('Do Mapping Test2')
                ret_test2 = stun_test(sock, ret_test1['OtherAddress'], 3478, m)
                log.debug(f"Mapping Test2 result: {ret_test2}")
                if ret_test2['XorMappedAddress'] == ret_test1['XorMappedAddress']:
                    return 'Endpoint-Independent Mapping', ret_test2
                else:
                    log.debug('Do Test3')
                    ret_test3 = stun_test(sock, ret_test1['OtherAddress'], ret_test1['OtherPort'], m)
                    log.debug(f"Mapping Test3 result: {ret_test3}")
                    if ret_test3['XorMappedAddress'] == ret_test2['XorMappedAddress']:
                        return 'Address-Dependent Mapping', ret_test3
                    else:
                        return 'AddressAndPort-Dependent Mapping', ret_test3
    else:
        return 'UDP Blocked', None
    

def get_nat_filtering(sock, host, port) -> (str, dict):
    log.debug('Do Test1')
    m = message.Message(message.MessageClass.REQUEST, message.MessageMethod.BINDING)
    ret_test1 = stun_test(sock, host, port, m)
    log.debug(f"Filtering Test1 result: {ret_test1}")
    if ret_test1['OtherAddress'] is None:
        return 'Test Not Support', None
    else:
        log.debug('Do Test2')
        m = message.Message(message.MessageClass.REQUEST, message.MessageMethod.BINDING)
        # set change ip and change port flag
        # 00000000 00000000 00000000 00000110
        m.add_attribute(ChangeRequestAttribute(b'\x00\x00\x00\x06'))
        ret_test2 = stun_test(sock, host, port, m)
        log.debug(f"Filtering Test2 result: {ret_test2}")
        if ret_test2['Resp']:
            return 'Endpoint-Independent Filtering', ret_test2
        else:
            log.debug('Do Test3')
            m = message.Message(message.MessageClass.REQUEST, message.MessageMethod.BINDING)
            # only set change port flag
            # 00000000 00000000 00000000 00000010
            m.add_attribute(ChangeRequestAttribute(b'\x00\x00\x00\x02'))
            ret_test3 = stun_test(sock, host, port, m)
            log.debug(f"Filtering Test3 result: {ret_test3}")
            if ret_test3['Resp']:
                return 'Address-Dependent Filtering', ret_test3
            else:
                return 'Address and Port-Dependent Filtering', ret_test3
            


def get_nat_test(source_ip='0.0.0.0', source_port='54320', stun_host=None, stun_port=3478):

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((source_ip, source_port))

    mapping_type, result_dict = get_nat_mapping(s, stun_host, stun_port)
    filtering_type, _ =  get_nat_filtering(s, stun_host, stun_port)
    external_ip = result_dict['MappedAddress']
    external_port = result_dict['MappedPort']
    return (mapping_type, filtering_type, external_ip, external_port)