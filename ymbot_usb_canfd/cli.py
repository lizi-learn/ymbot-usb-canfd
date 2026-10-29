import argparse
import json
from pathlib import Path
from .hardware import inventory,version


def main(argv=None):
    p=argparse.ArgumentParser(description='CANable 2.0: inventory, firmware check, physical peer testing and pinned flashing')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('inventory',help='Read USB identities, no serial or CAN data I/O')
    v=sub.add_parser('version',help='Query selected adapter; leaves its CAN channel closed')
    v.add_argument('--serial',required=True)
    t=sub.add_parser('test',help='Send bounded test frames between two explicitly selected, physically wired adapters')
    t.add_argument('--tx',required=True,help='First adapter USB serial, not tty number')
    t.add_argument('--rx',required=True,help='Second adapter USB serial')
    t.add_argument('--mode',choices=['classic','fd'],default='fd')
    t.add_argument('--data-bps',type=int,choices=[2000000,5000000],default=5000000)
    t.add_argument('--duration',type=int,default=10)
    t.add_argument('--rate',type=int,default=500,help='Requested frames/sec in each enabled direction, not guaranteed achieved rate')
    t.add_argument('--direction',choices=['forward','reverse','both'],default='both')
    t.add_argument('--length',type=int,default=64)
    t.add_argument('--output',type=Path)
    f=sub.add_parser('flash',help='Back up and flash only the pinned binary; target must already be in ROM DFU')
    f.add_argument('--serial',required=True,help='ROM DFU serial from dfu-util -l')
    f.add_argument('--usb-path',required=True,help='Physical path, such as 5-1.3.5')
    f.add_argument('--image',required=True,type=Path)
    f.add_argument('--backup-dir',required=True,type=Path,help='New private directory; existing directories are refused')
    a=p.parse_args(argv)
    try:
        if a.command=='inventory':
            r={'devices':inventory(),'can_frames_sent':0}
        elif a.command=='version':
            r=version(a.serial)
        elif a.command=='flash':
            from .flash import flash
            r=flash(a.serial,a.usb_path,a.image,a.backup_dir)
        else:
            from .benchmark import run
            r=run(a.tx,a.rx,a.mode,a.data_bps,a.duration,a.rate,a.direction,a.length)
            if a.output:
                a.output.parent.mkdir(parents=True,exist_ok=True)
                a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(r,ensure_ascii=False,indent=2))
        return 1 if r.get('status')=='fail' else 0
    except Exception as exc:
        print(json.dumps({'status':'fail','error':str(exc)},ensure_ascii=False))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
