#!/usr/bin/env python3
"""Check actual PNG dimensions, no editing and no generation."""
import argparse,json,struct,sys
from pathlib import Path

def inspect(path):
    p=Path(path)
    with p.open('rb') as f: header=f.read(24)
    if len(header)!=24 or header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR':
        raise ValueError('Expected PNG; read other formats using platform metadata')
    w,h=struct.unpack('>II',header[16:24])
    return {'file':str(p.resolve()),'width':w,'height':h,'exact_16_9':w>0 and h>0 and w*9==h*16}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images',nargs='+',type=Path)
    args=parser.parse_args();results=[]
    for path in args.images:
        try: results.append(inspect(path))
        except (OSError,ValueError) as error: results.append({'file':str(path),'exact_16_9':False,'error':str(error)})
    print(json.dumps(results,ensure_ascii=False,indent=2))
    sys.exit(0 if all(r['exact_16_9'] for r in results) else 1)
