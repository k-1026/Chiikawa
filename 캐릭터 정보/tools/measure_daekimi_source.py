from PIL import Image
from pathlib import Path
from statistics import median
import unicodedata,json,math,hashlib
root=Path.cwd();path=next(p for p in (root/'character').glob('*.png') if '대키미' in unicodedata.normalize('NFC',p.name));im=Image.open(path).convert('RGB');pix=im.load()
def components(mask):
 mask=set(mask);result=[]
 while mask:
  seed=mask.pop();todo=[seed];pts=[seed]
  while todo:
   x,y=todo.pop()
   for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if q in mask:mask.remove(q);todo.append(q);pts.append(q)
  result.append(pts)
 return sorted(result,key=len,reverse=True)
def bbox(pts):return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
def eye(roi):
 x0,y0,x1,y1=roi
 def comp(t):return components((x,y) for y in range(y0,y1) for x in range(x0,x1) if max(pix[x,y])<t)[0]
 pts=comp(100);b=bbox(pts);rows={}
 for x,y in pts:rows.setdefault(y,[]).append(x)
 filled={(x,y) for y,xs in rows.items() for x in range(min(xs),max(xs)+1)}
 contour=[]
 for y in range(b[1],b[3]):
  xs=rows.get(y,[])
  if xs:contour.append({'y':y,'left_x':min(xs),'right_x':max(xs)})
 highlights=[]
 for c in components((x,y) for x,y in filled if min(pix[x,y])>=155 and max(pix[x,y])-min(pix[x,y])<40):
  if len(c)<2:continue
  cb=bbox(c);center=[sum(x for x,y in c)/len(c),sum(y for x,y in c)/len(c)]
  highlights.append({'pixel_count':len(c),'bbox_xyxy_exclusive':cb,'centroid_xy':center,'center_percent_of_eye_box':[(center[0]-b[0])/(b[2]-b[0])*100,(center[1]-b[1])/(b[3]-b[1])*100]})
 return {'roi_xyxy':roi,'dark_threshold':'max(R,G,B)<100; largest 4-connected component; horizontal scan fill to include highlights','bbox_xyxy_exclusive':b,'width_px':b[2]-b[0],'height_px':b[3]-b[1],'filled_silhouette_area_px':len(filled),'centroid_xy':[sum(x for x,y in filled)/len(filled),sum(y for x,y in filled)/len(filled)],'bbox_at_thresholds':{str(t):bbox(comp(t)) for t in [80,100,120]},'scanline_contour':contour,'bright_components_threshold_min155':highlights}
def sample(label,x,y,size=5):
 half=size//2;vals=[pix[i,j] for j in range(y-half,y+half+1) for i in range(x-half,x+half+1)]
 rgb=[round(median(v[k] for v in vals)) for k in range(3)]
 srgb=[v/255 for v in rgb];lin=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in srgb]
 return {'label':label,'center_xy':[x,y],'patch_size':size,'rgb_median':rgb,'hex':'#%02X%02X%02X'%tuple(rgb),'relative_luminance_linear_srgb':sum(a*b for a,b in zip(lin,[.2126,.7152,.0722]))}
front={'left_eye':eye([66,712,121,766]),'right_eye':eye([143,711,197,766])}
hero={'left_eye':eye([466,136,552,239]),'right_eye':eye([584,166,702,270])}
frontpatch=[sample(*args) for args in [('head_neck_shadow',128,790),('belly_lit_center',128,807),('belly_lower_mid',128,825),('belly_lower_edge',128,834),('inner_left_leg_shadow',119,838),('inner_right_leg_shadow',136,840),('between_legs_background',128,840),('ground_contact_shadow',128,852),('nearby_background',128,858)]]
heropatch=[sample(*args) for args in [('belly_lit_center',570,330),('belly_lower_mid',570,360),('belly_lower_edge',570,370),('left_leg_interior',550,380),('right_lower_belly',590,380),('between_legs_background',570,380)]]
# Manual visible bounds are explicitly labeled; the exact eye contours above are pixel derived.
manual={'whole_height_y':[638,852],'head_body_bbox':[58,682,203,788],'torso_visible_bbox':[94,786,166,835],'ear_left_bbox':[56,666,102,713],'ball_left_bbox':[94,638,118,665],'ball_right_bbox':[141,638,166,664],'nose_bbox':[127,750,135,755],'open_mouth_bbox':[124,755,138,768],'arm_left_bbox':[79,790,101,824],'leg_foot_left_bbox':[96,828,126,852]}
profile=[]
for y in range(790,838):profile.append(sample('centerline',128,y,3))
report={'version':'D-measured-01','source':str(path.relative_to(root)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':list(im.size),'normalization':{'basis':'turnaround front only','height_px':214,'height_cm_user_assigned':103,'height_u':100,'cm_per_pixel':103/214,'u_per_pixel':100/214},'manual_front_bounds':manual,'front_eyes':front,'hero_eyes_oblique_view_do_not_mix_with_front':hero,'front_shadow_patches':frontpatch,'hero_shadow_patches':heropatch,'front_belly_vertical_profile':profile,'limitations':['2D projected silhouette, not true 3D dimensions','manually annotated partially occluded boundaries are approximations','linear sRGB luminance assumes sRGB, not recovered light/material parameters','threshold components do not distinguish intentional highlight shape from all optical reflections automatically']}
out=root/'output/daekimi_measurement';(out/'daekimi_source_measurements_01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for label,eyes in [('front',front),('hero',hero)]:
 for name,e in eyes.items():print(label,name,'bbox',e['bbox_xyxy_exclusive'],'size',e['width_px'],e['height_px'],'bright',e['bright_components_threshold_min155'])
for p in frontpatch:print(p['label'],p['hex'],round(p['relative_luminance_linear_srgb'],4))
print('Saved measurement JSON')

semantic={
'left_eye':[('large_star',[86,722,107,743],155),('small_gray_sparkle',[80,743,90,753],70),('tiny_reflection',[79,723,85,730],100)],
'right_eye':[('large_star',[160,721,180,743],155),('small_gray_sparkle',[174,744,182,754],70),('tiny_diamond',[154,738,160,745],100)]}
for name,items in semantic.items():
 eyeinfo=report['front_eyes'][name];b=eyeinfo['bbox_xyxy_exclusive'];features=[]
 for label,roi,threshold in items:
  x0,y0,x1,y1=roi
  comps=components((x,y) for y in range(y0,y1) for x in range(x0,x1) if min(pix[x,y])>=threshold and max(pix[x,y])-min(pix[x,y])<40)
  pts=comps[0];rgb=[round(median(pix[x,y][k] for x,y in pts)) for k in range(3)];bb=bbox(pts)
  center=[sum(x for x,y in pts)/len(pts),sum(y for x,y in pts)/len(pts)]
  feature={'semantic_label':label,'manual_roi_xyxy':roi,'threshold_min_channel':threshold,'bbox_xyxy_exclusive':bb,'area_px':len(pts),'centroid_xy':center,'center_percent_of_eye_box':[(center[0]-b[0])/eyeinfo['width_px']*100,(center[1]-b[1])/eyeinfo['height_px']*100],'width_percent_of_eye_box':(bb[2]-bb[0])/eyeinfo['width_px']*100,'height_percent_of_eye_box':(bb[3]-bb[1])/eyeinfo['height_px']*100,'rgb_median_of_segment':rgb,'hex':'#%02X%02X%02X'%tuple(rgb)}
  features.append(feature)
 eyeinfo['manually_identified_three_design_highlights']=features
 rows=eyeinfo['scanline_contour'];maxw=max(r['right_x']-r['left_x']+1 for r in rows)
 eyeinfo['scanline_summary']=[]
 for pct in [10,25,50,75,90]:
  y=round(b[1]+(b[3]-b[1]-1)*pct/100);r=next(r for r in rows if r['y']==y);width=r['right_x']-r['left_x']+1
  eyeinfo['scanline_summary'].append({'y_percent':pct,'y_px':y,'left_x':r['left_x'],'right_x':r['right_x'],'width_px':width,'width_percent_of_bbox':width/eyeinfo['width_px']*100})
 print(name,features,eyeinfo['scanline_summary'])
report['highlight_interpretation_note']='Three intended highlight motifs are identified with manual ROIs; connected bright components also include physical/specular glints and are not equal to the design motif count. Small gray sparkle color is preserved rather than made pure white.'
out=Path('output/daekimi_measurement/daekimi_source_measurements_01.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
