"""Linux USB identity and port ownership checks. No network or CAN I/O on import."""
import fcntl
import os
from pathlib import Path
import termios
import time

USB_ROOT = Path('/sys/bus/usb/devices')
TTY_ROOT = Path('/sys/class/tty')


def inventory():
    found = []
    for p in sorted(USB_ROOT.iterdir()):
        def value(name):
            try:
                return (p/name).read_text().strip()
            except OSError:
                return ''
        pair = (value('idVendor'), value('idProduct'))
        if pair not in [('16d0','117e'),('1d50','606f'),('0483','df11')]:
            continue
        row = dict(usb_path=p.name, vendor=pair[0], product_id=pair[1],
                   serial=value('serial'), product=value('product'))
        row['ports'] = ['/dev/'+t.name for t in TTY_ROOT.glob('ttyACM*')
                        if '/'+p.name+'/' in str(t.resolve())]
        row['kind'] = {('16d0','117e'):'slcan_fd',('1d50','606f'):'gs_usb',
                       ('0483','df11'):'rom_dfu'}[pair]
        found.append(row)
    return found


def select_device(serial, kind):
    rows = [d for d in inventory() if d['serial']==serial and d['kind']==kind]
    if len(rows)!=1:
        raise RuntimeError(f'Expected exactly one {kind} device with the selected serial, got {len(rows)}')
    return rows[0]


def holders(port):
    """Root is required to rule out existing root readers, including battery scans."""
    if os.geteuid()!=0:
        raise RuntimeError('Run hardware operations as root so all existing tty readers can be checked')
    found=[]
    for proc in Path('/proc').glob('[0-9]*'):
        if int(proc.name)==os.getpid():
            continue
        try:
            for fd in (proc/'fd').iterdir():
                try:
                    target=os.readlink(fd)
                except FileNotFoundError:
                    continue
                if target==port:
                    found.append({'pid':int(proc.name),'process':(proc/'comm').read_text().strip()})
                    break
        except FileNotFoundError:
            continue
        except PermissionError as exc:
            raise RuntimeError('Cannot verify port ownership in this process namespace') from exc
    return found


def open_port(serial_number):
    import serial
    d=select_device(serial_number,'slcan_fd')
    if not d['product'].startswith('CANable2 b158aa7 ') or len(d['ports'])!=1:
        raise RuntimeError('Unsupported firmware descriptor or ambiguous tty mapping')
    readers=holders(d['ports'][0])
    if readers:
        raise RuntimeError('Port has another reader; fix its device selection first: '+str(readers))
    s=serial.Serial(d['ports'][0],115200,timeout=.01,write_timeout=2,exclusive=True)
    try:
        fcntl.ioctl(s.fileno(),termios.TIOCEXCL)
        readers=holders(s.port)
        if readers:
            raise RuntimeError('Reader appeared while opening the port: '+str(readers))
        time.sleep(.1)
        s.reset_input_buffer()
        return s,d
    except BaseException:
        s.close()
        raise


def query(s, command, seconds=.15):
    s.write(command+b'\r')
    s.flush()
    out=bytearray()
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        out.extend(s.read(max(1,s.in_waiting)))
    return bytes(out).decode(errors='replace')


def version(serial):
    s,d=open_port(serial)
    try:
        query(s,b'C')
        d.update(version=query(s,b'V'),error_register=query(s,b'E'),can_frames_sent=0)
        if 'b158aa7' not in d['version']:
            raise RuntimeError('Unexpected or missing firmware version reply')
        return d
    finally:
        try:
            query(s,b'C')
        finally:
            s.close()
