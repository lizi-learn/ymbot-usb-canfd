"""CANable 2.0 upstream SLCAN FD extension, not generic LAWICEL FD."""
import struct

LENGTHS=list(range(9))+[12,16,20,24,32,48,64]


def payload(source, seq, length):
    if length not in LENGTHS or length<8:
        raise ValueError('Integrity streams require a supported payload length >= 8')
    return struct.pack('>II',source,seq)+bytes((source*71+seq*17+j*29)&255 for j in range(length-8))


def frame(source, seq, length, fd=True):
    if source not in [0,1] or not 0<=seq<2**32:
        raise ValueError('Invalid stream source or sequence')
    if not fd and length>8:
        raise ValueError('Classic CAN cannot carry more than 8 bytes')
    code=LENGTHS.index(length)
    return (('b' if fd else 't')+f'{0x500+source:03X}{code:X}'+payload(source,seq,length).hex().upper()+'\r').encode()


def decode(line, length, fd=True):
    if len(line)!=5+length*2 or line[:1]!=(b'b' if fd else b't'):
        raise ValueError('Frame type or length mismatch')
    if int(line[4:5],16)!=LENGTHS.index(length):
        raise ValueError('DLC mismatch')
    source=int(line[1:4],16)-0x500
    if source not in [0,1]:
        raise ValueError('Unexpected CAN ID')
    data=bytes.fromhex(line[5:].decode('ascii'))
    actual_source,seq=struct.unpack('>II',data[:8])
    if actual_source!=source or data!=payload(source,seq,length):
        raise ValueError('Payload mismatch')
    return source,seq
