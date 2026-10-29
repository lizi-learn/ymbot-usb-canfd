import datetime
import os
import select
import time
from .hardware import open_port, query, holders
from .protocol import frame, decode


def run(tx,rx,mode='fd',data_bps=5000000,duration=10,rate=500,direction='both',length=64):
    if tx==rx:
        raise ValueError('Two different physical adapters are required')
    if not 1<=duration<=300 or not 1<=rate<=5000 or data_bps not in [2000000,5000000]:
        raise ValueError('Unsupported duration, rate or data bitrate')
    if mode not in ['classic','fd'] or direction not in ['forward','reverse','both']:
        raise ValueError('Unsupported mode or direction')
    if mode=='classic' and length!=8:
        raise ValueError('Classic integrity testing uses 8-byte payloads')
    # Validate length before changing hardware.
    frame(0,0,length,mode=='fd')
    ports=[]
    result={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'nominal_bps':1000000,'data_bps':data_bps if mode=='fd' else None,
            'mode':mode,'BRS':mode=='fd','payload_bytes':length,'requested_fps_each':rate,
            'duration_seconds':duration,'identities':[],'status':'running'}
    sources=[0,1] if direction=='both' else [0 if direction=='forward' else 1]
    flows={str(i):dict(sent=0,received=0,duplicate=0,out_of_order=0,payload_or_format_errors=0) for i in sources}
    result['flows']=flows
    try:
        for serial in [tx,rx]:
            s,d=open_port(serial)
            ports.append(s)
            query(s,b'C')
            d['version_reply']=query(s,b'V')
            if 'b158aa7' not in d['version_reply']:
                raise RuntimeError('Firmware version query failed')
            result['identities'].append(d)
            for c in [b'S8',b'Y5' if data_bps==5000000 else b'Y2',b'A1',b'O']:
                query(s,c,.04)
        for s in ports:
            s.reset_input_buffer()
            os.set_blocking(s.fileno(),False)
        seen={i:set() for i in sources}
        last={i:-1 for i in sources}
        pending={i:b'' for i in sources}
        buffers=[bytearray(),bytearray()]
        start=time.monotonic()
        finish=start+duration
        next_send={i:start for i in sources}
        last_ownership_check=start
        while time.monotonic()<finish+2:
            now=time.monotonic()
            if now-last_ownership_check>=1:
                for s in ports:
                    if holders(s.port):
                        raise RuntimeError('Another process opened a test port during the run')
                last_ownership_check=now
            for i in sources:
                f=flows[str(i)]
                if not pending[i] and now<finish and now>=next_send[i]:
                    pending[i]=frame(i,f['sent'],length,mode=='fd')
                if pending[i]:
                    try:
                        n=os.write(ports[i].fileno(),pending[i])
                        pending[i]=pending[i][n:]
                        if not pending[i]:
                            f['sent']+=1
                            next_send[i]=time.monotonic()+1/rate
                    except BlockingIOError:
                        pass
            ready,_,_=select.select([s.fileno() for s in ports],[],[],.0001)
            for dest,s in enumerate(ports):
                if s.fileno() not in ready:
                    continue
                try:
                    buffers[dest].extend(os.read(s.fileno(),16384))
                except BlockingIOError:
                    continue
                while b'\r' in buffers[dest]:
                    line,_,rem=buffers[dest].partition(b'\r');buffers[dest]=bytearray(rem)
                    try:
                        source,seq=decode(bytes(line),length,mode=='fd')
                        if source not in sources or source==dest or seq>=flows[str(source)]['sent']:
                            raise ValueError('Unexpected direction or sequence')
                        f=flows[str(source)]
                        if seq in seen[source]:
                            f['duplicate']+=1
                        else:
                            f['out_of_order']+=int(seq<last[source]);last[source]=seq
                            seen[source].add(seq);f['received']+=1
                    except (ValueError,UnicodeError):
                        result['malformed_or_unexpected']=result.get('malformed_or_unexpected',0)+1
            if now>=finish and all(not pending[i] for i in sources) and all(f['sent']==f['received'] for f in flows.values()):
                break
        result['elapsed_with_drain_seconds']=round(time.monotonic()-start,4)
        result['leftover_ascii_bytes']=[len(b) for b in buffers]
        for f in flows.values():
            f.update(missing=f['sent']-f['received'],actual_fps=round(f['received']/duration,2),
                     useful_payload_mbps=round(f['received']*length*8/duration/1e6,4))
        result['firmware_error_registers']=[query(s,b'E') for s in ports]
        result['status']='pass' if all(f['sent']>0 and not any(f[k] for k in ['missing','duplicate','out_of_order']) for f in flows.values()) and not result.get('malformed_or_unexpected') and not any(buffers) and all(e=='CANable Error Register: 0' for e in result['firmware_error_registers']) else 'fail'
    except Exception as exc:
        result.update(status='fail',error=str(exc))
    finally:
        for s in ports:
            try:
                query(s,b'C')
            except Exception as exc:
                result.setdefault('cleanup_errors',[]).append(str(exc))
            finally:
                s.close()
        result['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return result
