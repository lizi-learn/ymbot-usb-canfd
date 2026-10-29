"""Identity-pinned DFU main-flash operations, with original backup and readback."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from .hardware import select_device

IMAGE_SHA256='a24290eea6050cf6245ade91353e2f47732f9e570baf21b2a05f0f2a2c8c08f8'
IMAGE_BYTES=26468


def flash(serial,usb_path,image,backup_dir):
    if os.geteuid()!=0:
        raise RuntimeError('DFU hardware operations require root')
    if not re.fullmatch(r'[0-9]+-[0-9]+(?:\.[0-9]+)*',usb_path):
        raise ValueError('Invalid physical USB path')
    image=Path(image).resolve()
    b=image.read_bytes()
    if len(b)!=IMAGE_BYTES or hashlib.sha256(b).hexdigest()!=IMAGE_SHA256:
        raise ValueError('Image is not the pinned, verified b158aa7 binary')
    directory=Path(backup_dir).resolve()
    os.umask(0o077)
    directory.mkdir(parents=True,exist_ok=False)
    backup=directory/'original-flash-128KiB.bin'
    readback=directory/'program-readback.bin'
    base=['dfu-util','-d','0483:df11','-S',serial,'-p',usb_path,'-a','0']

    def call(step,extra):
        d=select_device(serial,'rom_dfu')
        if d['usb_path']!=usb_path:
            raise RuntimeError('ROM serial and physical USB path do not match')
        args=base+extra
        p=subprocess.run(args,capture_output=True,text=True,timeout=60)
        record={'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        (directory/(step+'.json')).write_text(json.dumps(record,indent=2)+'\n')
        if p.returncode:
            raise RuntimeError(f'DFU {step} failed; operation log and any backup retained')
        return p.stdout

    listing=call('identity',['-l'])
    if '@Internal Flash' not in listing or '64*02Kg' not in listing:
        raise RuntimeError('Unexpected flash layout; no flash write attempted')
    call('backup',['-s','0x08000000:131072','-U',str(backup)])
    original=backup.read_bytes()
    if len(original)!=131072:
        raise RuntimeError('Original backup incomplete; no flash write attempted')
    summary={'serial':serial,'usb_path':usb_path,'original_bytes':len(original),
             'original_sha256':hashlib.sha256(original).hexdigest(),'image_sha256':IMAGE_SHA256}
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Do not leave DFU until readback is complete. No RDP/BOOT0/option-byte command.
    call('program',['-s','0x08000000','-D',str(image)])
    call('readback',['-s',f'0x08000000:{IMAGE_BYTES}','-U',str(readback)])
    if readback.read_bytes()!=b:
        raise RuntimeError('Readback differs from image; original backup retained')
    summary.update(readback_match=True,status='flash_pass_runtime_pending',
                   next_step='Remove BOOT short and reset; use version command to verify startup',
                   upstream_startup_note='May program BOR level 4 (~2.8V). Option bytes are not backed up by this main-flash backup.')
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary
