"""Read RGB PNG swatches using only Python's standard library.
Run from the Mascot project root: python3 tools/extract_palette.py
"""
from pathlib import Path
import json, struct, zlib, statistics, unicodedata, hashlib

def read_png(path):
    data=path.read_bytes(); offset=8; compressed=[]
    while offset<len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0]
        kind=data[offset+4:offset+8]; payload=data[offset+8:offset+8+length]; offset+=12+length
        if kind==b'IHDR': w,h,depth,ctype,_,_,interlace=struct.unpack('>IIBBBBB',payload)
        if kind==b'IDAT': compressed.append(payload)
    assert (depth,ctype,interlace)==(8,2,0)
    raw=zlib.decompress(b''.join(compressed)); stride=w*3; rows=[]; previous=bytearray(stride)
    for y in range(h):
        start=y*(stride+1); filter_type=raw[start]; row=bytearray(raw[start+1:start+1+stride])
        for i in range(stride):
            a=row[i-3] if i>=3 else 0; b=previous[i]; c=previous[i-3] if i>=3 else 0
            if filter_type==0: predictor=0
            elif filter_type==1: predictor=a
            elif filter_type==2: predictor=b
            elif filter_type==3: predictor=(a+b)//2
            elif filter_type==4:
                p=a+b-c; pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                predictor=a if pa<=pb and pa<=pc else b if pb<=pc else c
            else: raise ValueError(filter_type)
            row[i]=(row[i]+predictor)&255
        rows.append(row); previous=row
    return w,h,rows

result={}
for path in Path('character').glob('*.png'):
    name=unicodedata.normalize('NFC',path.name)
    daekimi='대키미' in name
    points=[('body',523,489),('inner_ear',608,485),('eyes',672,485),('highlights',736,485)] if daekimi else [('body',623,504),('muzzle_and_inner_ear',533,578),('eyes',623,587),('highlights',717,577)]
    w,h,rows=read_png(path); values={}
    for role,x,y in points:
        samples=[tuple(rows[j][i*3:i*3+3]) for j in range(y-4,y+5) for i in range(x-4,x+5)]
        rgb=tuple(round(statistics.median(p[channel] for p in samples)) for channel in range(3))
        values[role]={'hex':'#%02X%02X%02X'%rgb,'rgb':rgb,'center_xy':[x,y],'sample_size':[9,9],'method':'per-channel median of swatch pixels'}
    result['daekimi' if daekimi else 'oejimong']={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':[w,h],'swatch_samples':values,'body_hex_printed_on_board':'#6DCFF5' if daekimi else '#008C3A'}
Path('specs/color_samples.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for character,item in result.items():
    print(character, json.dumps(item['swatch_samples'],ensure_ascii=False))
