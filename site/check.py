#!/usr/bin/env python3
"""Validate local destinations, board boundaries, artifact hashes and public data."""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

OUT=Path(__file__).resolve().parent/'dist'
class Document(HTMLParser):
    def __init__(self,path):
        super().__init__();self.ids=set();self.links=[];self.h1=0;self.feed(path.read_text())
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids,'Duplicate ID';self.ids.add(a['id'])
        if tag=='h1':self.h1+=1
        for key in ['href','src']:
            if key in a:self.links.append(a[key])

pages={p.relative_to(OUT).as_posix():Document(p) for p in OUT.rglob('*.html')}
assert len(pages)==5
checked=0
for name,doc in pages.items():
    assert doc.h1==1,(name,doc.h1)
    for link in doc.links:
        u=urlsplit(link)
        if u.scheme or u.netloc:continue
        target=unquote(u.path).lstrip('/') if u.path else name
        if not target or target.endswith('/'):target+='index.html'
        assert (OUT/target).is_file(),(name,link)
        if u.fragment and target in pages:assert unquote(u.fragment) in pages[target].ids,(name,link)
        checked+=1
info=json.loads((OUT/'build-info.json').read_text())
for name,sha in info['artifacts_sha256'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha
corpus='\n'.join(p.read_text() for p in OUT.rglob('*') if p.is_file() and p.suffix in ['.html','.js','.css','.json','.txt','.xml'])
for label,pattern in {
 'private IP':r'\b(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b',
 'old credential':r'\b(?:temppwd|ymzz2021)\b',
 'private key':r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
 'token value':r'(?:oauth_token|refresh_token|dns_cloudflare_api_key)\s*[=:]\s*[\"\x27]?[\w-]{16,}'
}.items():assert not re.search(pattern,corpus),label
usb=(OUT/'usb-canfd/index.html').read_text();five=(OUT/'5io/index.html').read_text()
assert all(x in usb for x in ['143,076','60 秒','CAN2 收发待测','尚未接线','SLCAN FD','0.85 Mb/s'])
assert all(x in five for x in ['12,386,944','12,326,944','60,000','1,830 秒','严格验收未通过','每口 +6'])
assert '12,386,944' not in usb and '143,076' not in five
assert (OUT/'downloads/CAN0-CAN1-FD5M-20261030.pdf').read_bytes().startswith(b'%PDF-')
print(f'PASS: {len(pages)} HTML files, {checked} local links, evidence boundaries, artifact hashes and public-data scan')
