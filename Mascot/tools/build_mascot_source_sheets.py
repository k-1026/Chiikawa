"""Reproduce source-only mascot measurement sheets.
Run from the Mascot root with Python providing Pillow, numpy and reportlab.
No generative image model is used. Automatic contours and manual landmarks
are separately labeled. Original PNGs are never changed.
"""
from pathlib import Path
from PIL import Image
import numpy as np
from collections import deque,defaultdict
import json,unicodedata,hashlib,math
ROOT=Path.cwd();OUT=ROOT/'output/mascot_source_sheets'
CONFIG={
'daekimi':{'name':'대키미','height_cm':103,'views':{'front':[44,630,241,858],'three_quarter':[239,630,411,858],'side':[419,630,576,858],'back':[585,630,756,858]},'eyes':{'left':[66,712,121,766],'right':[143,711,197,766]},'body_stations':[[790,104,157],[798,100,161],[806,97,164],[814,95,165],[822,94,164],[830,98,162]],'head_front_points':[[130,682],[155,683],[176,690],[191,705],[200,720],[202,740],[197,759],[184,775],[158,785],[130,788],[102,785],[77,775],[63,759],[58,740],[60,720],[72,705],[85,692],[106,684]],'ear_points':{'left':[[62,666],[59,668],[57,682],[56,698],[60,714],[73,707],[87,695],[102,687],[82,675]],'right':[[197,666],[201,669],[203,685],[203,701],[199,713],[186,705],[173,695],[157,687],[177,674]]},'thumb':{'view':'hero raised hand','roi':[435,240,525,322],'palm_bbox':[444,253,473,287],'thumb_lobe_bbox':[467,246,489,276],'notch_xy':[470,269],'points':{'thumb_tip':[477,247],'thumb_outer':[488,262],'thumb_notch':[470,269],'palm_outer':[445,268],'palm_bottom':[458,286]},'basis':'manual reading of visible two-lobe hand; partial overlap, not anatomical mesh'},'part_boxes':{'head_body':[58,682,203,788],'torso_approx':[94,786,166,835],'nose':[127,750,135,755],'open_mouth':[124,755,138,768],'left_arm':[79,790,101,824],'right_arm':[160,790,178,824],'left_leg_foot':[96,828,126,852],'right_leg_foot':[131,828,162,852]},'patches':[('neck',128,790),('belly_center',128,807),('belly_low_mid',128,825),('belly_lower',128,834),('left_inner_leg',119,838),('right_inner_leg',136,840),('leg_gap',128,840),('ground_contact',128,852),('ground_background',128,858)]},
'oejimong':{'name':'외지몽','height_cm':105,'views':{'front':[20,695,214,927],'three_quarter':[214,695,406,927],'side':[410,695,580,927],'back':[580,695,777,927]},'eyes':{'left':[60,771,108,824],'right':[132,774,181,825]},'body_stations':[[848,97,146],[856,92,152],[864,88,157],[872,86,159],[880,86,158],[888,92,155]],'head_front_points':[[121,743],[145,747],[164,759],[177,777],[181,799],[175,820],[163,835],[145,844],[120,848],[94,844],[77,835],[65,818],[61,796],[66,776],[79,759],[99,748]],'ear_points':{'left':[[74,758],[59,771],[44,791],[33,808],[31,820],[36,830],[47,834],[60,831],[65,819],[62,798],[66,777]],'right':[[160,760],[177,772],[193,790],[208,809],[212,823],[205,836],[191,837],[181,829],[178,811],[174,786]]},'thumb':{'view':'retry raised hand','roi':[425,1305,480,1367],'palm_bbox':[442,1318,464,1345],'thumb_lobe_bbox':[433,1314,448,1336],'notch_xy':[447,1321],'points':{'thumb_tip':[439,1315],'thumb_outer':[433,1324],'thumb_notch':[447,1321],'palm_outer':[463,1332],'palm_bottom':[451,1344]},'basis':'manual reading of visible two-lobe hand in retry panel; partly joined to forearm'},'part_boxes':{'head_body':[60,744,180,848],'torso_approx':[86,844,159,899],'muzzle':[97,800,142,840],'nose':[113,805,125,814],'open_mouth':[110,814,130,832],'left_arm':[73,849,93,883],'right_arm':[148,850,166,886],'left_leg_foot':[87,889,119,915],'right_leg_foot':[125,889,157,915]},'patches':[('neck',120,849),('belly_center',120,870),('belly_low_mid',120,885),('belly_lower',120,893),('left_inner_leg',111,899),('right_inner_leg',129,899),('leg_gap',121,905),('ground_contact',121,915),('ground_background',121,922)]}}

def largest(mask):
 mask=mask.copy();best=[]
 for yy,xx in zip(*np.nonzero(mask)):
  if not mask[yy,xx]:continue
  mask[yy,xx]=False;todo=deque([(int(xx),int(yy))]);pts=[]
  while todo:
   x,y=todo.popleft();pts.append((x,y))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    a,b=x+dx,y+dy
    if 0<=b<mask.shape[0] and 0<=a<mask.shape[1] and mask[b,a]:mask[b,a]=False;todo.append((a,b))
  if len(pts)>len(best):best=pts
 result=np.zeros(mask.shape,dtype=bool)
 if best:
  xs,ys=zip(*best);result[list(ys),list(xs)]=True
 return result

def fillholes(mask):
 inv=~mask;outside=np.zeros(mask.shape,bool);q=deque()
 for x in range(mask.shape[1]):
  for y in [0,mask.shape[0]-1]:
   if inv[y,x] and not outside[y,x]:outside[y,x]=True;q.append((x,y))
 for y in range(mask.shape[0]):
  for x in [0,mask.shape[1]-1]:
   if inv[y,x] and not outside[y,x]:outside[y,x]=True;q.append((x,y))
 while q:
  x,y=q.popleft()
  for a,b in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=b<mask.shape[0] and 0<=a<mask.shape[1] and inv[b,a] and not outside[b,a]:outside[b,a]=True;q.append((a,b))
 return ~outside

def boundary(mask,offset):
 edges=[];H,W=mask.shape
 for y,x in zip(*np.nonzero(mask)):
  x=int(x);y=int(y)
  if y==0 or not mask[y-1,x]:edges.append(((x,y),(x+1,y)))
  if x==W-1 or not mask[y,x+1]:edges.append(((x+1,y),(x+1,y+1)))
  if y==H-1 or not mask[y+1,x]:edges.append(((x+1,y+1),(x,y+1)))
  if x==0 or not mask[y,x-1]:edges.append(((x,y+1),(x,y)))
 nxt=defaultdict(list)
 for a,b in edges:nxt[a].append(b)
 loops=[]
 while nxt:
  start=next(iter(nxt));prev=None;cur=start;pts=[cur]
  while True:
   choices=nxt.get(cur,[])
   if not choices:break
   # Ambiguous diagonal vertices prefer the clockwise/right turn.
   if prev is not None and len(choices)>1:
    vx,vy=cur[0]-prev[0],cur[1]-prev[1]
    choices.sort(key=lambda p:((vx*(p[1]-cur[1])-vy*(p[0]-cur[0])),vx*(p[0]-cur[0])+vy*(p[1]-cur[1])),reverse=True)
   dest=choices.pop(0)
   if not choices:del nxt[cur]
   prev,cur=cur,dest;pts.append(cur)
   if cur==start:break
  loops.append(pts)
 loops.sort(key=lambda ps:abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ps,ps[1:]))),reverse=True)
 return [[[int(x+offset[0]),int(y+offset[1])] for x,y in loop] for loop in loops]

def scan(mask,offset):
 result=[]
 for y in range(mask.shape[0]):
  xs=np.flatnonzero(mask[y]);runs=[]
  for x in xs:
   x=int(x)
   if not runs or x>runs[-1][1]:runs.append([x,x+1])
   else:runs[-1][1]=x+1
  if runs:result.append({'y':y+offset[1],'runs_x_exclusive':[[a+offset[0],b+offset[0]] for a,b in runs],'outer_left':int(xs[0]+offset[0]),'outer_right_exclusive':int(xs[-1]+1+offset[0]),'outer_width_px':int(xs[-1]-xs[0]+1),'occupied_width_px':int(len(xs))})
 return result

def rect(mask,offset):
 yy,xx=np.nonzero(mask);return [int(xx.min()+offset[0]),int(yy.min()+offset[1]),int(xx.max()+offset[0]+1),int(yy.max()+offset[1]+1)]

def patch(arr,label,x,y):
 a=arr[y-2:y+3,x-2:x+3];rgb=np.median(a.reshape(-1,3),axis=0).round().astype(int).tolist();v=np.array(rgb)/255;lin=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4);Y=float(lin@np.array([.2126,.7152,.0722]));return {'label':label,'xy':[x,y],'size':5,'rgb':rgb,'hex':'#%02X%02X%02X'%tuple(rgb),'linear_srgb_Y':Y}

for key,c in CONFIG.items():
 path=next(p for p in (ROOT/'character').glob('*.png') if c['name'] in unicodedata.normalize('NFC',p.name));arr=np.array(Image.open(path).convert('RGB'));full={}
 for view,roi in c['views'].items():
  x0,y0,x1,y1=roi;a=arr[y0:y1,x0:x1].astype(int);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
  color=(b-r>25)&(g-r>20)&(b>80)&(r<205) if key=='daekimi' else (g-r>20)&(g-b>12)&(g>60)&(r<195)
  yy=np.arange(y0,y1)[:,None]; face_y=((yy>=700)&(yy<=790)) if key=='daekimi' else ((yy>=745)&(yy<=855)); extras=(np.max(a,axis=2)<150)&face_y;
  if key=='oejimong': extras|=(r>g+1)&(g-b>5)&(r>120)&face_y
  raw=largest(color|extras);mask=fillholes(raw);bnd=rect(mask,[x0,y0]);h=bnd[3]-bnd[1]
  full[view]={'roi_xyxy':roi,'bbox_xyxy_exclusive':bnd,'projected_height_px':h,'width_px':bnd[2]-bnd[0],'body_color_mask_pixels':int(raw.sum()),'filled_silhouette_pixels':int(mask.sum()),'coordinate_method':'body-color + facial dark/cream mask; largest 4-connected component; enclosed-hole fill; retains outside leg gap; no smoothing or symmetrizing','loops_source_pixel_cell_edges':boundary(mask,[x0,y0]),'scanline_source_pixels':scan(mask,[x0,y0]),'view_normalization':'u=100*(source_y-bbox_top)/projected_height; x centered on bbox mid; no cm depth inference'}
 frontH=full['front']['projected_height_px'];eyeinfos={}
 for side,roi in c['eyes'].items():
  x0,y0,x1,y1=roi;a=arr[y0:y1,x0:x1];m=largest(np.max(a,axis=2)<100);m=fillholes(m);bnd=rect(m,[x0,y0]);loops=boundary(m,[x0,y0]);width=bnd[2]-bnd[0];height=bnd[3]-bnd[1]
  # Sharp medial lower corner proxy: select lower-medial quadrant, extremal toward nose.
  loop=loops[0];cx=(bnd[0]+bnd[2])/2;cy=(bnd[1]+bnd[3])/2
  cand=[p for p in loop if p[1]>=cy and ((p[0]>=cx) if side=='left' else (p[0]<=cx))]
  tip=max(cand,key=lambda p:p[0]) if side=='left' else min(cand,key=lambda p:p[0]);same=[p for p in cand if p[0]==tip[0]];tip=min(same,key=lambda p:abs(p[1]-(bnd[1]+height*.78)))
  idx=loop.index(tip);n=len(loop)-1;kstep=6;p=loop[(idx-kstep)%n];q=loop[(idx+kstep)%n];v1=np.array(p)-np.array(tip);v2=np.array(q)-np.array(tip);den=np.linalg.norm(v1)*np.linalg.norm(v2);angle=math.degrees(math.acos(max(-1,min(1,float(v1@v2)/den)))) if den else None
  sensitivity={}
  for t in [80,100,120]:sensitivity[str(t)]=rect(fillholes(largest(np.max(a,axis=2)<t)),[x0,y0])
  eyeinfos[side]={'roi_xyxy':roi,'bbox_xyxy_exclusive':bnd,'width_px':width,'height_px':height,'threshold_sensitivity_bbox':sensitivity,'outer_loops_source_pixel_edges':loops,'scanline_source_pixels':scan(m,[x0,y0]),'medial_lower_corner':{'xy_source':tip,'support_before_xy':p,'support_after_xy':q,'support_distance_boundary_edges':kstep,'finite_scale_corner_angle_deg':angle,'interpretation':'threshold-defined local angle over 6 boundary edge steps, NOT exact original Bezier curvature; pointedness must be checked in reference viewer'},'design':{'shape':'rounded triangular/teardrop with narrower medial-lower corner; do not replace with ellipse','highlight_count_user_fixed':3}}
 parts={}
 for name,box in c['part_boxes'].items():
  parts[name]={'bbox_xyxy_exclusive_manual':box,'width_px':box[2]-box[0],'height_px':box[3]-box[1],'basis':'manual source boundary reading; joins/overlap may be uncertain; not exact recovered model'}
 stations=[]
 for y,l,r in c['body_stations']:
  stations.append({'y_source':y,'left_x_manual':l,'right_x_manual':r,'width_px':r-l,'height_u_from_front_bbox':100*(y-full['front']['bbox_xyxy_exclusive'][1])/frontH,'width_u':(r-l)*100/frontH,'width_cm_if_same_frontal_scale':(r-l)*c['height_cm']/frontH,'basis':'manual visible torso/arm separation reading; lower join partially occluded, +/-2px reading range recommended, not statistical confidence'})
 info={'package_version':'source-detail-01','name':c['name'],'character_key':key,'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':[int(arr.shape[1]),int(arr.shape[0])],'height_cm_user_fixed':c['height_cm'],'front_height_px_mask':frontH,'cm_per_front_pixel':c['height_cm']/frontH,'primary_reference':'TURNAROUND; preserve each view separately; not a recovered common-scale orthographic CAD set','views':full,'front_eyes':eyeinfos,'manual_part_bounds':parts,'manual_front_head_landmark_loop':{'points_source':c['head_front_points'],'basis':'manual visible head/ear attachment seam readings; hidden portion not established; point linkage is a guide, not original vector reconstruction'},'front_torso_stations':stations,'front_ear_landmark_loops':{'points_source':c['ear_points'],'basis':'manual visible outer and attachment seam landmarks; do not treat ROI cutting edges as anatomical edges'},'thumb_reference':c['thumb'],'front_tone_patches':[patch(arr,*p) for p in c['patches']],'design_invariants':{'antenna_count':2,'round_ball_count':2,'highlights_per_open_eye':3,'default_blush':False,'muzzle':'blue face, no white patch' if key=='daekimi' else 'cream #F8F0E4, same as visible inner ear'},'limits':['No hidden topology or original 3D shader can be recovered exactly from these 2D boards','No numeric reduction ratios from v04 are used','Silhouette pixel threshold changes edge positions; manual stations are marked separately','Visible thumbs are gesture-dependent; do not add visible fingers to a closed silhouette']}
 (OUT/f'{key}_source_detail_01.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 print(key,'views',[(k,v['bbox_xyxy_exclusive'],v['projected_height_px']) for k,v in full.items()],'eyes',[(k,v['bbox_xyxy_exclusive'],v['medial_lower_corner']) for k,v in eyeinfos.items()])

from pathlib import Path
from PIL import Image
import numpy as np,json,math
for key,c in CONFIG.items():
 p=OUT/f'{key}_source_detail_01.json';d=json.loads(p.read_text());arr=np.array(Image.open(ROOT/d['source']).convert('RGB'))
 for side,e in d['front_eyes'].items():
  loop=e['outer_loops_source_pixel_edges'][0];b=e['bbox_xyxy_exclusive'];w,h=b[2]-b[0],b[3]-b[1];n=len(loop)-1;k=12;candidates=[]
  for i,pt in enumerate(loop[:-1]):
   if not b[1]+.65*h<=pt[1]<=b[1]+.96*h:continue
   if (side=='left' and pt[0]<b[0]+.65*w) or (side=='right' and pt[0]>b[0]+.35*w):continue
   a=loop[(i-k)%n];z=loop[(i+k)%n];v=np.array(a)-pt;u=np.array(z)-pt;den=float(np.linalg.norm(v)*np.linalg.norm(u))
   if den:candidates.append((math.degrees(math.acos(max(-1,min(1,float(v@u)/den)))),pt,a,z))
  angle,tip,a,z=min(candidates)
  e['medial_lower_corner']={'xy_source':tip,'support_before_xy':a,'support_after_xy':z,'support_distance_boundary_edges':12,'finite_scale_corner_angle_deg':angle,'method':'minimum supported angle in lower 65%-96% of eye and medial 35%; 12 source pixel-cell edge steps before/after','interpretation':'finite-scale projected corner diagnostic, not true analytic tangent angle or original Bezier curvature'}
 if key=='daekimi':
  old=json.loads((ROOT/'output/daekimi_measurement/daekimi_source_measurements_01.json').read_text())
  for side in ['left','right']:d['front_eyes'][side]['three_design_highlights']=old['front_eyes'][side+'_eye']['manually_identified_three_design_highlights']
 else:
  motifs={'left':[('large_star',[72,779,98,803],155),('small_gray_sparkle',[69,799,85,817],70),('tiny_reflection',[67,777,82,789],100)],'right':[('large_star',[144,780,172,805],155),('small_gray_sparkle',[154,803,173,820],70),('tiny_diamond',[136,790,151,807],100)]}
  for side,items in motifs.items():
   eb=d['front_eyes'][side]['bbox_xyxy_exclusive'];w,h=eb[2]-eb[0],eb[3]-eb[1];features=[]
   for name,roi,t in items:
    x0,y0,x1,y1=roi;a=arr[y0:y1,x0:x1];neutral=np.max(a.astype(int),2)-np.min(a.astype(int),2)<40;seg=largest((np.min(a,2)>=t)&neutral);yy,xx=np.nonzero(seg);b=rect(seg,[x0,y0]);center=[float(xx.mean()+x0),float(yy.mean()+y0)];rgb=np.median(a[seg],axis=0).round().astype(int).tolist()
    features.append({'semantic_label':name,'manual_roi_xyxy':roi,'threshold_min_channel':t,'bbox_xyxy_exclusive':b,'area_px':int(seg.sum()),'centroid_xy':center,'center_percent_of_eye_box':[(center[0]-eb[0])/w*100,(center[1]-eb[1])/h*100],'width_percent_of_eye_box':(b[2]-b[0])/w*100,'height_percent_of_eye_box':(b[3]-b[1])/h*100,'rgb_median_of_segment':rgb,'hex':'#%02X%02X%02X'%tuple(rgb)})
   d['front_eyes'][side]['three_design_highlights']=features
 # Full local color source samples, not new design colors.
 palettes=json.loads((ROOT/'specs/color_samples.json').read_text())[key]
 d['palette']={'brand_body_hex_printed_on_board':palettes['body_hex_printed_on_board'],'swatches':palettes['swatch_samples'],'interpretation':'brand base value and source swatch medians; not every shaded skin pixel'}
 d['contour_resolution']='source pixel-cell boundary only; no smoothing, ellipse replacement, mirror, or resculpting applied'
 d['normalization_policy']='front mask height is reported separately from earlier manual 214/210px readings; use this package mask convention consistently, do not mix denominators; manual support not a recovered true world ruler'
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 print(key,'eye corners',[(s,e['medial_lower_corner']['xy_source'],round(e['medial_lower_corner']['finite_scale_corner_angle_deg'],1)) for s,e in d['front_eyes'].items()])
 print('highlights',[(s,[(f['semantic_label'],f['bbox_xyxy_exclusive'],f['hex']) for f in e['three_design_highlights']]) for s,e in d['front_eyes'].items()])

from pathlib import Path
import json
for key,H,top,axis in [('daekimi',214,638,130),('oejimong',210,705,120)]:
 p=Path('output/mascot_source_sheets')/(key+'_source_detail_01.json');d=json.loads(p.read_text());d['front_normalization_height_px_manual']=H;d['front_normalization_top_y_manual']=top;d['front_center_axis_x_manual']=axis;d['cm_per_front_pixel']=d['height_cm_user_fixed']/H
 for row in d['front_torso_stations']:
  row['height_u_from_front_reference']=100*(row['y_source']-top)/H;row.pop('height_u_from_front_bbox',None);row['width_u']=row['width_px']*100/H;row['width_cm_if_same_frontal_scale']=row['width_px']*d['height_cm_user_fixed']/H
 for v in d['views'].values():v['view_normalization']='All source absolute coordinates retained; dimensions may be scaled by this view projected height. Bbox midpoint is NOT anatomical axis because tails/ears are asymmetric.'
 d['normalization_policy']='Canonical front reference is manual top-to-sole 214px (Daekimi) or 210px (Oejimong), consistent with earlier source reading; threshold mask bbox differs by 1-2px because of highlights/edge shading. Detected and manual bounds are separate. Other views are not forced to same pixel height.'
 if key=='oejimong':
  th=d['thumb_reference'];th.update({'roi':[425,1328,480,1378],'palm_bbox':[445,1337,465,1361],'thumb_lobe_bbox':[436,1334,450,1344],'notch_xy':[450,1338],'points':{'thumb_tip':[442,1335],'thumb_outer':[436,1341],'thumb_notch':[450,1338],'palm_outer':[464,1349],'palm_bottom':[450,1361]},'basis':'manual two-lobe reading rechecked with source-coordinate grid; no hand reconstruction from hidden anatomy'})
 boxes={'left_antenna_ball':[94,638,118,665],'right_antenna_ball':[141,638,166,664],'left_antenna_stem_projection':[106,661,120,687],'right_antenna_stem_projection':[139,661,153,686]} if key=='daekimi' else {'left_antenna_ball':[85,705,111,733],'right_antenna_ball':[139,706,166,734],'left_antenna_stem_projection':[96,730,110,750],'right_antenna_stem_projection':[137,731,152,751]}
 for side,ps in d['front_ear_landmark_loops']['points_source'].items():boxes[side+'_ear_visible_projection']=[min(x for x,y in ps),min(y for x,y in ps),max(x for x,y in ps),max(y for x,y in ps)]
 for name,b in boxes.items():d['manual_part_bounds'][name]={'bbox_xyxy_exclusive_manual':b,'width_px':b[2]-b[0],'height_px':b[3]-b[1],'basis':'manually read visible projected region, sphere/stem join and ear/head overlap uncertain; not independent physical diameter'}
 d['part_dimension_note']='Ball width/height are projected cap bounds, not exact 3D sphere diameter; stem box includes tilt and is not stem cross-sectional diameter; ears use visible lobe and seam landmarks.'
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

from pathlib import Path
from PIL import Image as PILImage
import json,csv,base64,html,math,shutil,re,zipfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak,Flowable,KeepTogether
from reportlab.lib.pagesizes import A4
ROOT=Path.cwd();OUT=ROOT/'output/mascot_source_sheets'
pdfmetrics.registerFont(TTFont('SheetKR','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
pdfmetrics.registerFont(TTFont('SheetHead','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
pdfmetrics.registerFontFamily('SheetKR',normal='SheetKR',bold='SheetHead',italic='SheetKR',boldItalic='SheetHead')
NAVY=colors.HexColor('#17354C');MUTED=colors.HexColor('#567083');PALE=colors.HexColor('#F0F5F8');WIDTH=A4[0]-80
ST={
'p':ParagraphStyle('p',fontName='SheetKR',fontSize=8.7,leading=13.5,spaceAfter=5,textColor=NAVY,wordWrap='CJK'),
'h':ParagraphStyle('h',fontName='SheetHead',fontSize=18,leading=24,spaceAfter=12,textColor=NAVY,keepWithNext=True,wordWrap='CJK'),
's':ParagraphStyle('s',fontName='SheetHead',fontSize=11,leading=16,spaceBefore=9,spaceAfter=6,textColor=NAVY,keepWithNext=True,wordWrap='CJK'),
'cell':ParagraphStyle('cell',fontName='SheetKR',fontSize=7.8,leading=11.2,textColor=NAVY,wordWrap='CJK'),
'head':ParagraphStyle('head',fontName='SheetHead',fontSize=7.8,leading=11.5,textColor=colors.white,wordWrap='CJK')}
VIEW_NAMES={'front':'정면','three_quarter':'45도','side':'측면','back':'후면'}
FEATURE_NAMES={'head_body':'머리 본체','torso_approx':'몸통 근사','muzzle':'크림색 주둥이','nose':'코','open_mouth':'기본 열린 입','left_arm':'화면 왼쪽 팔','right_arm':'화면 오른쪽 팔','left_leg_foot':'화면 왼쪽 다리·발','right_leg_foot':'화면 오른쪽 다리·발','left_antenna_ball':'화면 왼쪽 구슬 투영','right_antenna_ball':'화면 오른쪽 구슬 투영','left_antenna_stem_projection':'화면 왼쪽 줄기 투영','right_antenna_stem_projection':'화면 오른쪽 줄기 투영','left_ear_visible_projection':'화면 왼쪽 귀 투영','right_ear_visible_projection':'화면 오른쪽 귀 투영'}
PATCH_NAMES={'neck':'머리 아래 연결부','belly_center':'배 중앙','belly_low_mid':'배 하부 중간','belly_lower':'배 하단','left_inner_leg':'화면 왼쪽 다리 안쪽','right_inner_leg':'화면 오른쪽 다리 안쪽','leg_gap':'다리 사이 틈','ground_contact':'바닥 접지 음영','ground_background':'바닥 배경'}
MOTIF={'large_star':'큰 별','small_gray_sparkle':'작은 회색 반짝임','tiny_reflection':'아주 작은 반사·마름모','tiny_diamond':'아주 작은 마름모'}

def csvwrite(path,headers,rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.writer(f);w.writerow(headers);w.writerows(rows)
def pathsvg(loop):return 'M '+' L '.join(f'{x},{y}' for x,y in loop)+' Z'
def boxsvg(b,col='#FF476D'):
 x0,y0,x1,y1=b;return f'<rect class="overlay" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" stroke="{col}" stroke-width=".5" fill="none"/>'
def linesvg(points,col='#eb4e75',closed=False):
 return '<'+('polygon' if closed else 'polyline')+' class="overlay" points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{col}" stroke-width=".5"/>'

def table(rows):
 n=len(rows[0]);weights={2:[.32,.68],3:[.34,.33,.33],4:[.24,.24,.24,.28],5:[.20,.25,.15,.19,.21],6:[.15,.22,.13,.16,.17,.17]}.get(n,[1/n]*n)
 data=[[Paragraph(html.escape(str(v)),ST['head' if i==0 else 'cell']) for v in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=[WIDTH*x for x in weights],repeatRows=1,hAlign='LEFT');cmd=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d7e2eb'))]
 for i in range(1,len(data)):
  if i%2:cmd.append(('BACKGROUND',(0,i),(-1,i),PALE))
 t.setStyle(TableStyle(cmd));return t
class SourcePanel(Flowable):
 def __init__(self,source,roi,maxheight=280,maxwidth=WIDTH,loops=None,lines=None,boxes=None,points=None):
  super().__init__();self.source=source;self.roi=roi;self.loops=loops or [];self.lines=lines or [];self.boxes=boxes or [];self.points=points or [];self.scale=min(maxwidth/(roi[2]-roi[0]),maxheight/(roi[3]-roi[1]));self.width=maxwidth;self.height=(roi[3]-roi[1])*self.scale
 def draw(self):
  c=self.canv;x0,y0,x1,y1=self.roi;s=self.scale;ox=(self.width-(x1-x0)*s)/2;c.saveState();c.translate(ox,0);clip=c.beginPath();clip.rect(0,0,(x1-x0)*s,(y1-y0)*s);c.clipPath(clip,stroke=0,fill=0);im=PILImage.open(self.source);c.drawImage(str(self.source),-x0*s,(y1-im.height)*s,width=im.width*s,height=im.height*s)
  def drawline(ps,color,close=False):
   if not ps:return
   p=c.beginPath();p.moveTo((ps[0][0]-x0)*s,(y1-ps[0][1])*s)
   for x,y in ps[1:]:p.lineTo((x-x0)*s,(y1-y)*s)
   if close:p.close()
   c.setStrokeColor(colors.HexColor(color));c.setLineWidth(.55);c.drawPath(p,stroke=1,fill=0)
  for loop in self.loops:drawline(loop,'#E23F70',True)
  for ps,col in self.lines:drawline(ps,col,False)
  for b,col in self.boxes:
   a,v,z,w=b;drawline([[a,v],[z,v],[z,w],[a,w],[a,v]],col)
  for xy,col in self.points:
   c.setFillColor(colors.HexColor(col));c.circle((xy[0]-x0)*s,(y1-xy[1])*s,2,stroke=0,fill=1)
  c.restoreState()

def paragraph(s,style='p'):return Paragraph(html.escape(s),ST[style])
def mdtable(rows):return '\n'.join(['| '+' | '.join(map(str,r))+' |' for r in rows[:1]]+['|'+'---|'*len(rows[0])]+['| '+' | '.join(map(str,r))+' |' for r in rows[1:]])

for key in ['daekimi','oejimong']:
 d=json.loads((OUT/f'{key}_source_detail_01.json').read_text());name=d['name'];folder=OUT/key;refs=folder/'reference';refs.mkdir(parents=True,exist_ok=True);source=ROOT/d['source'];shutil.copyfile(source,refs/'original_board.png');d['source_in_package']='reference/original_board.png';(folder/'measurements.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 H=d['front_normalization_height_px_manual'];top=d['front_normalization_top_y_manual'];axis=d['front_center_axis_x_manual'];cm=d['height_cm_user_fixed']/H
 # Persist every contour, all rows, and per-view SVG source pixel traces.
 for view,v in d['views'].items():
  roi=v['roi_xyxy'];csvwrite(folder/f'{view}_outline.csv',['loop','point','source_x','source_y','front_u_x_relative_axis' if view=='front' else 'view_u_x_from_bbox_left','front_u_y' if view=='front' else 'view_u_y','coordinate_basis'],[[j,i,x,y,round((x-axis)*100/H,4) if view=='front' else round((x-v['bbox_xyxy_exclusive'][0])*100/v['projected_height_px'],4),round((y-top)*100/H,4) if view=='front' else round((y-v['bbox_xyxy_exclusive'][1])*100/v['projected_height_px'],4),'canonical front reference' if view=='front' else 'this projected view only'] for j,loop in enumerate(v['loops_source_pixel_cell_edges']) for i,(x,y) in enumerate(loop)])
  csvwrite(folder/f'{view}_scanlines.csv',['source_y','outer_left_x','outer_right_exclusive_x','outer_width_px','occupied_width_px','separate_runs_x'],[[r['y'],r['outer_left'],r['outer_right_exclusive'],r['outer_width_px'],r['occupied_width_px'],json.dumps(r['runs_x_exclusive'])] for r in v['scanline_source_pixels']])
  paths=''.join(f'<path d="{pathsvg(loop)}" fill="none" stroke="#153A56" stroke-width=".55"/>' for loop in v['loops_source_pixel_cell_edges'])
  (folder/f'{view}_source_trace.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{roi[0]} {roi[1]} {roi[2]-roi[0]} {roi[3]-roi[1]}"><title>{name} {VIEW_NAMES[view]} 원본 픽셀 외곽 추적; 새 디자인 아님</title>{paths}</svg>')
 for side,e in d['front_eyes'].items():csvwrite(folder/f'eye_{side}_outline.csv',['loop','point','source_x','source_y','eye_local_x_percent','eye_local_y_percent'],[[j,i,x,y,round((x-e['bbox_xyxy_exclusive'][0])/e['width_px']*100,4),round((y-e['bbox_xyxy_exclusive'][1])/e['height_px']*100,4)] for j,loop in enumerate(e['outer_loops_source_pixel_edges']) for i,(x,y) in enumerate(loop)])
 csvwrite(folder/'torso_width_stations.csv',['source_y','left_x_manual','right_x_manual','width_px','width_u','width_cm','basis'],[[r['y_source'],r['left_x_manual'],r['right_x_manual'],r['width_px'],r['width_u'],r['width_cm_if_same_frontal_scale'],r['basis']] for r in d['front_torso_stations']])
 csvwrite(folder/'head_landmarks.csv',['index','source_x','source_y','x_u','y_u','basis'],[[i,x,y,(x-axis)*100/H,(y-top)*100/H,'manual visible head/seam reading, hidden portions not established'] for i,(x,y) in enumerate(d['manual_front_head_landmark_loop']['points_source'])])

 for side,ps in d['front_ear_landmark_loops']['points_source'].items():csvwrite(folder/f'ear_{side}_landmarks.csv',['point','source_x','source_y','basis'],[[i,x,y,'manual visible outer/seam point; do not infer hidden anatomy'] for i,(x,y) in enumerate(ps)])
 csvwrite(folder/'thumb_gesture_landmarks.csv',['landmark','source_x','source_y','reference_view'],[[k,xy[0],xy[1],d['thumb_reference']['view']] for k,xy in d['thumb_reference']['points'].items()])
 # All content below is shared between PDF and Markdown blocks.
 blocks=[]
 def h(s):blocks.append(('h',s))
 def p(s):blocks.append(('p',s))
 def t(rows):blocks.append(('t',rows))
 def image(roi,label,maxheight=260,**kwargs):blocks.append(('img',{'roi':roi,'label':label,'maxheight':maxheight,**kwargs}))
 h('01. 원본과 좌표·근거')
 p(f'{name}의 반복 활용을 위한 원본 관측 시트다. 캐릭터 디자인을 바꾸지 않고 제공된 설정 보드의 픽셀 외곽·얼굴·손·음영을 기록했다. v4에서 임의로 줄였던 눈·몸통·귀·구슬 값은 이번 측정의 근거로 사용하지 않았다. 전체 키 {d["height_cm_user_fixed"]}cm는 사용자 지정값이다.')
 p(f'정면 환산 기준은 위쪽 y={top}부터 발바닥 y={top+H}까지 {H}px=100u={d["height_cm_user_fixed"]}cm다. 1px≈{cm:.3f}cm. 원본 좌상단이(0,0), 오른쪽+x·아래쪽+y다. 정면 중심축 x={axis}. 모든 사각형의 오른쪽·아래 좌표는 미포함이다.')
 p('수치의 종류를 구분한다. 자동 추출값=색·밝기 임계값에서 얻은 픽셀 경계. 수동 판독값=겹친 부위의 외곽·이음선·엄지 위치를 원본에서 읽은 근사점. 사용자 확정값=키·개수·색 영역 등. 가려진 구조와 원본 3D 모델의 정확한 곡률·깊이는 임의로 만들지 않는다.')
 vrows=[['시점','원본 분석 영역','검출 외곽 경계','투영 높이px']]
 for v,info in d['views'].items():vrows.append([VIEW_NAMES[v],str(info['roi_xyxy']),str(info['bbox_xyxy_exclusive']),info['projected_height_px']])
 t(vrows)
 p('검출 경계와 수동 키 기준은 밝은 구슬 끝·발 가장자리의 색과 그림자 때문에1~2px 차이 날 수 있다. 이는 키를 변경한 것이 아니다. 시점마다 크기·원근이 달라 공통 축척의 정밀 직교도라고 가정하지 않는다. 측면 폭을 바로 실제 머리 깊이로 승인하지 않는다.')
 for v in ['front','three_quarter','side','back']:image(d['views'][v]['roi_xyxy'],VIEW_NAMES[v]+' 원본',205)
 h('02. 얼굴형·귀: 외곽과 이음선')
 p('원본에 없는 매끈한 타원이나 원형으로 바꾸지 않는다. 원본 픽셀 외곽을 보존한 SVG·CSV가4시점별로 제공된다. 픽셀 계단을 임의로 다듬지 않았으며, 이 선은 원본 벡터 경로나3D 곡면을 복원한 것이 아니다.')
 p('머리 외곽점은 직접 보이는 경계와 귀 부착 이음선을 수동으로 읽었다. 귀에 가려진 머리 경계는 검증된 실측선이 아니다. 아래 점들을 이어 그린 선은 측정 확인용 보조선이며 캐릭터에 그리는 선이나 새 디자인이 아니다.')
 rows=[['점','원본(x,y)','정면 좌표(xu,yu)']]
 for i,(x,y) in enumerate(d['manual_front_head_landmark_loop']['points_source']):rows.append([i,f'{x}, {y}',f'{(x-axis)*100/H:.2f}, {(y-top)*100/H:.2f}'])
 t(rows)
 image(d['views']['front']['roi_xyxy'],'얼굴·귀 수동 판독점',180,lines=[(d['manual_front_head_landmark_loop']['points_source']+[d['manual_front_head_landmark_loop']['points_source'][0]],'#e04472')]+[(ps+[ps[0]],'#d49100') for ps in d['front_ear_landmark_loops']['points_source'].values()])
 p('귀 모서리와 테두리의 실제 노출 경계는 원본을 따른다. 대키미는 끝으로 좁아지는 고양이 삼각형, 외지몽은 아래로 늘어진 강아지형이다. 귀 외곽·부착점의 원본 좌표 전체는 measurements.json의 front_ear_landmark_loops에 기록했다.')
 h('03. 눈 앞머리·눈 윤곽')
 p('정면의 검정 눈 영역을 max(R,G,B)<100으로 분리하고 가장 큰 연결영역을 사용했다. 밝은 별 때문에 뚫린 내부는 채우되 바깥 윤곽은 타원으로 대체하지 않았다. 임계값80·100·120 경계도 기록했다. 좌우 차이는 원본 관찰값이며 임의로 대칭화하지 않는다.')
 rows=[['항목','화면 왼쪽 눈','화면 오른쪽 눈']]
 for lab,fun in [('경계',lambda e:str(e['bbox_xyxy_exclusive'])),('크기px',lambda e:f'{e["width_px"]}×{e["height_px"]}'),('크기cm 환산',lambda e:f'{e["width_px"]*cm:.1f}×{e["height_px"]*cm:.1f}'),('안쪽 아래 모서리',lambda e:str(e['medial_lower_corner']['xy_source'])),('모서리 전후 기준점',lambda e:str(e['medial_lower_corner']['support_before_xy'])+' / '+str(e['medial_lower_corner']['support_after_xy'])),('유한 구간 진단 각도',lambda e:f'{e["medial_lower_corner"]["finite_scale_corner_angle_deg"]:.1f}°')]:rows.append([lab,fun(d['front_eyes']['left']),fun(d['front_eyes']['right'])])
 t(rows)
 p('날카로움은 한 점의 각도만으로 고정하지 않는다. 아래쪽65~96%·코 쪽35% 영역에서 앞뒤12개 픽셀 외곽 에지를 기준으로 가장 좁게 꺾이는 지점을 찾았다. 표의 각도는 이 분석 구간의 투영 진단값이며 원본 베지어 접선 각도나3D 모서리 각도가 아니다. 실제 경계 좌표와 원본 위의 표시를 함께 사용한다.')
 loops=[];lines2=[];pts=[]
 for e in d['front_eyes'].values():
  loops+=e['outer_loops_source_pixel_edges'];c=e['medial_lower_corner'];lines2.append(([c['support_before_xy'],c['xy_source'],c['support_after_xy']],'#ffd21f'));pts.append((c['xy_source'],'#f13369'))
 a=d['front_eyes']['left']['bbox_xyxy_exclusive'];b=d['front_eyes']['right']['bbox_xyxy_exclusive'];eye_roi=[a[0]-8,min(a[1],b[1])-6,b[2]+8,max(a[3],b[3])+7]
 image(eye_roi,'눈 윤곽과 안쪽 아래 모서리 지지점',230,loops=loops,lines=lines2,points=pts)
 L=d['front_eyes']['left'];R=d['front_eyes']['right'];spacing=((R['bbox_xyxy_exclusive'][0]+R['bbox_xyxy_exclusive'][2])-(L['bbox_xyxy_exclusive'][0]+L['bbox_xyxy_exclusive'][2]))/2;gap=R['bbox_xyxy_exclusive'][0]-L['bbox_xyxy_exclusive'][2]
 p(f'눈 경계 중심 간격 {spacing:.1f}px≈{spacing*cm:.1f}cm, 눈 사이 빈 간격 {gap}px≈{gap*cm:.1f}cm. 전체 눈 외곽 좌표는 eye_left_outline.csv·eye_right_outline.csv에 있다. 정면의 값과 기울어진 대표 이미지의 투영 눈 크기를 평균내지 않는다.')
 h('04. 눈 하이라이트의 위치·크기·밝기')
 p('각 눈의 의도된 하이라이트3개를 수동 작은 영역 안에서 분리했다. 큰 별·작은 회색 반짝임·아주 작은 마름모/반사 형태를 구분한다. 자연 광택의 밝은 성분을 모두 추가 디자인 점으로 세지 않는다. 작은 반짝임까지 모두 흰색으로 올리면 원본 인상이 달라진다.')
 rows=[['눈·요소','중심: 눈 내부%','크기px','관찰색']];boxes=[]
 for side,e in d['front_eyes'].items():
  for f in e['three_design_highlights']:
   bb=f['bbox_xyxy_exclusive'];x,y=f['center_percent_of_eye_box'];rows.append([('왼쪽' if side=='left' else '오른쪽')+' '+MOTIF[f['semantic_label']],f'{x:.1f}, {y:.1f}',f'{bb[2]-bb[0]}×{bb[3]-bb[1]}',f['hex']]);boxes.append((bb,'#ed9a00'))
 t(rows);image(eye_roi,'원본 하이라이트 분리 영역',210,boxes=boxes)
 p('중심 좌표는 각 눈 경계 사각형의 좌상단(0,0)·우하단(100,100) 기준이다. 관찰색은 렌더링된 원본 픽셀의 중앙값이며 브랜드색이나 원본 셰이더의 기본색이 아니다. 좌우 눈에 동일 좌표를 무조건 복사하지 않는다.')
 h('05. 몸통 너비·곡선·팔 연결')
 p('몸통 너비는 전체 캐릭터 외곽 폭과 다르다. 외곽에는 팔·꼬리가 포함되므로, 아래는 몸통과 팔의 분리 이음선을 수동 판독한 폭이다. 가려진 접합부 때문에 양쪽 경계 각각 약±2px 판독 범위를 권장한다. 이것은 통계적 신뢰구간이나 제조 공차가 아니다. 배의 명암을 실제 돌출 경계로 오인하지 않는다.')
 rows=[['원본y','왼쪽x / 오른쪽x','몸통 폭px','100u 대비 / cm 환산']]
 for s in d['front_torso_stations']:rows.append([s['y_source'],f'{s["left_x_manual"]} / {s["right_x_manual"]}',s['width_px'],f'{s["width_u"]:.1f}u / {s["width_cm_if_same_frontal_scale"]:.1f}cm'])
 t(rows)
 bodylines=[([[s['left_x_manual'],s['y_source']],[s['right_x_manual'],s['y_source']]],'#db2e6c') for s in d['front_torso_stations']]
 bodylines += [([[s['left_x_manual'],s['y_source']] for s in d['front_torso_stations']],'#0b8e80'),([[s['right_x_manual'],s['y_source']] for s in d['front_torso_stations']],'#0b8e80')]
 bodyroi=[min(v['bbox_xyxy_exclusive_manual'][0] for k,v in d['manual_part_bounds'].items() if 'arm' in k)-5,d['manual_part_bounds']['torso_approx']['bbox_xyxy_exclusive_manual'][1]-5,max(v['bbox_xyxy_exclusive_manual'][2] for k,v in d['manual_part_bounds'].items() if 'arm' in k)+12,top+H+5]
 image(bodyroi,'몸통 폭 판독선·팔·다리 연결',280,lines=bodylines)
 p('목은 드러나지 않고 머리 아래와 자연스럽게 연결된다. 어깨를 구형 관절처럼 분리하지 않는다. 배는 짧은 둥근 볼륨이며 하단에서 다리로 이어진다. 표의 판독점을 이은 선은 위치 확인선이지 캐릭터에 추가하는 옆선이 아니다. 전 시점의 실제 외곽 곡선은 매 픽셀 행과 경계 에지 좌표로 제공한다.')
 h('06. 손·엄지의 구분')
 th=d['thumb_reference'];pb=th['palm_bbox'];tb=th['thumb_lobe_bbox']
 p('기본 정면에서 팔을 내렸을 때는 손가락 윤곽이 가려져 있다. 엄지가 보이는 동작을 별도 관측한다. 손바닥의 큰 둥근 덩어리와 측면의 작은 엄지 돌출, 그 사이의 얕은 오목점을 유지한다. 다섯 손가락을 펼친 사람 손으로 바꾸거나 모든 자세에서 엄지를 강제로 밖으로 빼지 않는다.')
 p('참조 동작: '+th['view']+'. 다음은 해당 동작의 원본 픽셀 수동 판독값이다. 원근과 자세가 다른 정면 전체 키 기준으로 cm를 바로 환산하지 않는다.')
 rows=[['요소','원본 좌표','크기px / 의미'],['손바닥 경계',str(pb),f'{pb[2]-pb[0]}×{pb[3]-pb[1]}'],['엄지 돌출 경계',str(tb),f'{tb[2]-tb[0]}×{tb[3]-tb[1]}'],['손바닥·엄지 사이 오목점',str(th['notch_xy']),'겹침·명암으로 보이는 얕은 분리 위치']]
 for k,xy in th['points'].items():rows.append([k,str(xy),'수동 확인점'])
 t(rows);image(th['roi'],'원본의 손바닥·엄지 구분',290,boxes=[(pb,'#e04370'),(tb,'#efab00')],points=[(th['notch_xy'],'#00a399')])
 p('표의 엄지 경계는 해당 동작에서 엄지로 읽히는 노출 돌출부의 관측 영역이다. 손바닥·팔에 겹친 전체 엄지 길이와 부피를 이 사각형으로 확정하지 않는다. 정면에서 이 형태가 가려지면 엄지를 강제로 추가하지 않는다. 짧은 원본 픽셀 때문에1~2px의 판독 변화도 크다.')
 h('07. 부위별 경계·귀·안테나·꼬리')
 rows=[['부위','원본 수동 경계','너비×높이px','100u / cm 환산']]
 for k,v in d['manual_part_bounds'].items():
  b=v['bbox_xyxy_exclusive_manual'];w,hgt=v['width_px'],v['height_px'];rows.append([FEATURE_NAMES[k],str(b),f'{w}×{hgt}',f'{w*100/H:.1f}×{hgt*100/H:.1f}u / {w*cm:.1f}×{hgt*cm:.1f}cm'])
 t(rows)
 p('이 표는 경계 사각형이지 형태를 대체하는 도형이 아니다. 코·입·발의 고유 윤곽은 원본을 따른다. 다리와 발은 구분되지만 원본에 있는 발등 명암을 임의의 신발 테두리나 발목 띠로 바꾸지 않는다.')
 p('안테나2개·끝 구슬2개를 유지한다. 측면에서 안테나 하나가 다른 하나에 가려져도 실제 개수를 줄이지 않는다. 구슬과 줄기가 같은 색으로 이어져 있으므로 원본 픽셀만으로 접합부의 정확한3D 구 지름을 분리했다고 주장하지 않는다. 전 시점의 관측 외곽은 SVG·CSV에 보존했다.')
 p('대키미는 긴 말린 고양이 꼬리, 외지몽은 짧고 뭉툭한 강아지 꼬리를 유지한다. 정면에서 가려진 꼬리 뿌리·손의 뒤쪽·귀 뒤 구조는 후면과 측면에서 보이는 범위까지만 판단한다. 후면의 꼬리 방향을 정면과 기계적으로 좌우 반전하여 새 구조로 만들지 않는다.')
 h('08. 전 시점 실루엣·높이별 폭')
 p('각 시점에 원본색 마스크와 얼굴의 검정·크림색 돌출부를 포함하고, 원본 외부와 이어진 다리 사이 틈은 유지했다. 닫힌 눈·주둥이 같은 내부 구멍만 채워 외곽을 얻었다. 색 임계값의 등고선이므로 미세한 가장자리 차이를 원본 벡터의 정확한 곡률로 해석하지 않는다.')
 rows=[['시점','높이25% 부근 폭px','높이50% 부근 폭px','높이75% 부근 폭px']]
 for view,v in d['views'].items():
  topv=v['bbox_xyxy_exclusive'][1];hv=v['projected_height_px'];vals=[]
  for f in [.25,.5,.75]:
   target=topv+hv*f;row=min(v['scanline_source_pixels'],key=lambda r:abs(r['y']-target));vals.append(row['outer_width_px'])
  rows.append([VIEW_NAMES[view]]+vals)
 t(rows)
 p('위 폭은 귀·팔·꼬리를 포함한 화면상의 전체 외곽 폭이다. 몸통 폭으로 사용하지 않는다. scanlines CSV에는 매 행의 바깥 폭과 분리된 실제 점유 구간을 모두 저장하여 다리 사이 틈을 검정으로 채우는 오류를 막는다.')
 for view in ['side','back']:image(d['views'][view]['roi_xyxy'],VIEW_NAMES[view]+' 원본 위 픽셀 외곽선',200,loops=d['views'][view]['loops_source_pixel_cell_edges'])
 h('09. 기본색·눈 광택·배 아래 음영')
 pal=d['palette'];rows=[['부위','관찰 또는 명시값','근거'],['대표 몸색',pal['brand_body_hex_printed_on_board'],'보드에 명시된 HEX']]
 for k,v in pal['swatches'].items():rows.append([k,v['hex'],'견본 내부9×9px 중앙값'])
 t(rows)
 p('기본 홍조는 없다. 대키미 코·입 주변은 하늘색, 외지몽 주둥이와 보이는 귀 안쪽은 같은 크림빛 흰색을 유지한다. 보드 일부 감정 장면의 패치·홍조는 기본형에 상시 적용하지 않는다. 브랜드 기본색과 조명 아래 피부의 관찰색은 구분한다.')
 rows=[['위치','원본 중심(x,y)','관찰색','선형 상대휘도Y']];patchboxes=[]
 for f in d['front_tone_patches']:rows.append([PATCH_NAMES[f['label']],str(f['xy']),f['hex'],f'{f["linear_srgb_Y"]:.4f}']);x,y=f['xy'];patchboxes.append(([x-2.5,y-2.5,x+2.5,y+2.5],'#dd3b73'))
 t(rows);image(bodyroi,'배 아래·다리 사이·바닥 샘플',170,boxes=patchboxes)
 p('색은5×5px 채널 중앙값이고 Y는 sRGB 가정 아래 계산한 선형 상대휘도다. 원본 셰이더의 빛 세기·거칠기·재질 기본색을 역산한 값이 아니다. 배 하단에는 부드러운 피부 음영을 유지하고, 다리 사이의 밝은 배경·발밑의 접지 그림자와 구분한다. 별도 검정 반달·배의 수평 홈·봉제선·색 띠를 추가하지 않는다.')
 p('몸 표면의 부드러운 낮은 광택과 검정 눈의 광택을 분리한다. 작은 반짝임·큰 별의 밝기를 구분하고, 원본보다 과도하게 쨍한 색·강한 반사·거친 점토 결·솜털을 추가하지 않는다. 이번 시트에는 원본에서 복원할 수 없는 roughness 같은 재질계수를 임의로 넣지 않았다.')
 h('10. 반복 활용 방법과 판정')
 p('원본 보드와 이 시트의 해당 시점 자료를 함께 사용한다. 먼저 기본형을 맞추고 그다음 포즈·표정을 확장한다. 원본 얼굴형·눈 앞머리·엄지 돌출·몸통 곡선·배 명암이 맞는지 각각 검수한다. 텍스트·수치만으로 생성형 모델이 동일한 픽셀과3D 구조를 보장하는 것은 아니므로 결과를 곧바로 공식 기준으로 등록하지 않는다.')
 p('정확한 외곽이 필요한 일러스트·모델링 작업에서는 해당 시점 SVG·좌표를 실제 가이드로 사용한다. 원본 픽셀 외곽은 충분히 확대하면 계단이 보이므로, 원본 해상도 이상으로 임의의 곡면이 확정된 것으로 해석하지 않는다. 더 높은 해상도 원본이나 원본3D가 생기면 같은 좌표 체계에서 갱신한다.')
 prompt=f'첨부된 {name} 원본 설정 보드의 TURNAROUND 시점을 기준으로 동일 캐릭터를 재현한다. 새로 귀엽게 재디자인하지 않는다. 눈은 눈앞 안쪽 아래가 좁아지는 원본 윤곽을 유지하고 단순한 원·타원으로 바꾸지 않는다. 각 눈3개 하이라이트의 위치와 밝기를 원본처럼 구분한다. 손을 든 자세에서 손바닥·작은 엄지 돌출·얕은 오목점을 유지하고 나머지 손가락을 추가하지 않는다. 몸통 폭은 머리와 구분되는 원본의 높이별 곡선을 유지하며 배·볼·어깨를 부풀리지 않는다. 배 아래 피부 명암, 다리 사이의 밝은 틈, 발밑 접지 음영을 구분한다. 안테나2개, 전체 키{d["height_cm_user_fixed"]}cm, 기본 홍조 없음. '+('입 주변은 하늘색으로 유지한다.' if key=='daekimi' else '주둥이와 보이는 귀 안쪽은 동일한 크림빛 흰색을 유지한다.')
 p(prompt);(folder/'reference_prompt.txt').write_text(prompt+'\n')
 p('첨부 파일: 원본 PNG, measurements.json, 각 시점 outline.csv·scanlines.csv·source_trace.svg, 눈 외곽 CSV2개, 몸통 폭 CSV, 얼굴 기준점 CSV, 원본 확대·측정 표시 HTML. 이전 임의 조정값을 사용하지 않았으며 원본 이미지와 PART별 원문을 변경하지 않았다.')
 # Markdown records numeric rows and links to the same raw source panels.
 md=[f'# {name} 원본 기반 세부 캐릭터 시트','',f'**SOURCE DETAIL 01 / 2026-11-03 / 전체 키 {d["height_cm_user_fixed"]}cm**','','원본 유지 · 4시점 외곽 · 눈 앞머리 · 엄지 · 얼굴·몸통 곡선 · 명암 기록','']
 for typ,val in blocks:
  if typ=='h':md +=['## '+val,'']
  elif typ=='p':md +=[val,'']
  elif typ=='t':md +=[mdtable(val),'']
  elif typ=='img':md +=[f'원본 확인: **{val["label"]}**, 영역 {val["roi"]}. 확대·겹침 확인은 [측정 뷰어](measurement_viewer.html)를 사용한다.','']
 md+=['## 원본 보드','','![원본 설정 보드](reference/original_board.png)','']
 (folder/'character_sheet.md').write_text('\n'.join(md))
 # Viewer references immutable source pixels once; vector overlays are independent of raster.
 overlays=[]
 def panel(label,roi,over=''):
  x,y,z,w=roi;return f'<section><h2>{html.escape(label)}</h2><svg viewBox="{x} {y} {z-x} {w-y}" aria-label="{html.escape(label)}"><image class="board" x="0" y="0" width="793" height="1983"/>{over}</svg></section>'
 panels=[]
 for view,v in d['views'].items():
  over=''.join(f'<path class="overlay" d="{pathsvg(loop)}" fill="none" stroke="#ed3e71" stroke-width=".55"/>' for loop in v['loops_source_pixel_cell_edges']);panels.append(panel(VIEW_NAMES[view]+' 原본 픽셀 외곽'.replace('原','원'),v['roi_xyxy'],over))
 over=''
 for e in d['front_eyes'].values():
  for loop in e['outer_loops_source_pixel_edges']:over+=linesvg(loop,'#e34b71',True)
  c=e['medial_lower_corner'];over+=linesvg([c['support_before_xy'],c['xy_source'],c['support_after_xy']],'#ffda2b')
  over+=f'<circle class="overlay" cx="{c["xy_source"][0]}" cy="{c["xy_source"][1]}" r=".8" fill="#f33365"/>'
  for f in e['three_design_highlights']:over+=boxsvg(f['bbox_xyxy_exclusive'],'#f2a600')
 panels.append(panel('눈 앞머리·눈 윤곽·하이라이트',eye_roi,over))
 over=linesvg(d['manual_front_head_landmark_loop']['points_source'],'#e23b71',True)
 for ps in d['front_ear_landmark_loops']['points_source'].values():over+=linesvg(ps,'#e1a000',True)
 panels.append(panel('얼굴형·귀 부착 이음선: 수동 판독점',d['views']['front']['roi_xyxy'],over))
 over=''
 for s in d['front_torso_stations']:over+=linesvg([[s['left_x_manual'],s['y_source']],[s['right_x_manual'],s['y_source']]],'#e23c71')
 for f in d['front_tone_patches']:
  x,y=f['xy'];over+=boxsvg([x-2.5,y-2.5,x+2.5,y+2.5],'#008f89')
 panels.append(panel('몸통 너비·배 아래 음영 위치',bodyroi,over))
 over=boxsvg(pb,'#e23c71')+boxsvg(tb,'#e4a000');xy=th['notch_xy'];over+=f'<circle class="overlay" cx="{xy[0]}" cy="{xy[1]}" r="1" fill="#00a391"/>'
 panels.append(panel('손바닥·엄지 돌출·오목점: 동작별 원본',th['roi'],over))
 datauri='data:image/png;base64,'+base64.b64encode(source.read_bytes()).decode()
 css='body{margin:0;background:#eef3f7;color:#18364c;font-family:system-ui;line-height:1.7}main{max-width:1180px;margin:auto;padding:28px}h1{font-size:28px}h2{font-size:18px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}section{background:white;padding:20px;border:1px solid #d7e3eb;border-radius:14px}svg{display:block;width:100%;max-height:650px}label{display:block;position:sticky;top:0;padding:16px;background:#dfeefb;z-index:5;margin-bottom:22px;border-radius:10px}body.hide .overlay{display:none}@media(max-width:760px){.grid{grid-template-columns:1fr}}'
 page='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+name+' 원본 측정 뷰어</title><style>'+css+'</style><main><h1>'+name+' 원본 기반 측정 확인</h1><p>원본 픽셀을 재디자인하지 않고 그대로 확대합니다. 분홍색=자동 외곽·판독선, 노란색=눈 모서리 지지점·하이라이트·엄지, 초록색=명암 샘플·손의 오목점. 자동 경계와 수동 판독선은 PDF 설명을 함께 확인하세요.</p><label><input type="checkbox" checked onchange="document.body.classList.toggle(\'hide\',!this.checked)"> 측정 표시 켜기 / 끄기</label><div class="grid">'+''.join(panels)+'</div></main><script>const source='+json.dumps(datauri)+';document.querySelectorAll("image.board").forEach(e=>e.setAttribute("href",source));</script></html>'
 (folder/'measurement_viewer.html').write_text(page)
 # PDF: same content blocks with original-pixel analytical panels.
 story=[paragraph(name+' 원본 기반 세부 캐릭터 시트','h'),paragraph('SOURCE DETAIL 01  /  2026-11-03'),paragraph('전체 키 '+str(d['height_cm_user_fixed'])+'cm · 원본 유지 · 눈 앞머리 · 엄지 · 얼굴·몸통 곡선'),Spacer(1,12),SourcePanel(source,d['views']['front']['roi_xyxy'],maxheight=430),Spacer(1,12),paragraph('자동 픽셀 외곽과 수동 판독점을 구분한2D 관측 자료입니다. 원본과 다른 새 캐릭터를 생성하지 않았습니다.'),PageBreak()]
 for typ,val in blocks:
  if typ=='h':
   if len(story)>1 and isinstance(story[-1],PageBreak):pass
   else:story.append(PageBreak())
   story.append(paragraph(val,'h'))
  elif typ=='p':story.append(paragraph(val))
  elif typ=='t':story.extend([table(val),Spacer(1,9)])
  elif typ=='img':
   args=dict(val);label=args.pop('label');story.extend([paragraph(label,'s'),SourcePanel(source,**args),Spacer(1,9)])
 def decor(c,doc,name=name):
  w,h=A4;c.saveState();c.setFont('SheetKR',7.4);c.setFillColor(MUTED);c.drawString(40,h-26,name+'  |  원본 기반 세부 캐릭터 시트');c.drawRightString(w-40,h-26,'SOURCE DETAIL 01');c.setStrokeColor(colors.HexColor('#d9e4ec'));c.line(40,h-33,w-40,h-33);c.line(40,33,w-40,33);c.drawString(40,21,'SOURCE PIXELS / MANUAL LANDMARKS / NO REDESIGN');c.drawRightString(w-40,21,str(doc.page));c.restoreState()
 doc=SimpleDocTemplate(str(folder/'character_sheet.pdf'),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=49,bottomMargin=46,title=name+' 원본 기반 세부 캐릭터 시트',author='대구 사투리 축제 마스코트 프로젝트');doc.build(story,onFirstPage=decor,onLaterPages=decor)
 print('Exported',name,folder)

(OUT/'README.md').write_text('''# 대키미·외지몽 원본 기반 세부 시트

기존 임의 조정 v4의 후속 원본 관측 자료다. 디자인을 변경하지 않았으며 원본 파일은 바이트 그대로 포함했다.

- daekimi/character_sheet.pdf, character_sheet.md: 대키미 시트.
- oejimong/character_sheet.pdf, character_sheet.md: 외지몽 시트.
- 각 폴더 measurement_viewer.html: 원본 확대·표시 켜기/끄기.
- measurements.json: 모든 자동·수동 좌표, 원본 해시, 분석 방법.
- 4시점 outline.csv·scanlines.csv·source_trace.svg: 원본 픽셀별 외곽과 가로 폭.
- eye_left_outline.csv·eye_right_outline.csv: 눈 실제 외곽. 단순 원·타원으로 대체하지 않는다.
- torso_width_stations.csv·head_landmarks.csv: 수동 판독값과 원본 위치.
- reference/original_board.png: 변경하지 않은 원본.

자동 임계값 경계와 수동 이음선 판독값은 구분했다. 엄지 좌표는 실제로 보이는 동작에만 적용한다. 가려진 부분·원본3D 깊이·재질계수는 임의로 만들지 않았다. 사용자 지정 키는 대키미103cm·외지몽105cm를 유지했다. 측면·45도·후면을 공통 축척의 정밀 직교도라고 가정하지 않는다.
''')
zip_path=OUT.parent/'mascot_source_sheets_01.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,Path('mascot_source_sheets')/p.relative_to(OUT))
print('ZIP',zip_path)
