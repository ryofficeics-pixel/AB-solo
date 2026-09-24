import os,re,io,zipfile,shutil
from pathlib import Path
from PIL import Image,ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ROOT=Path(".")
OUT=Path("AB_solo_photo_sheet.pdf")
TMP=Path("_photo_pdf_tmp")
if TMP.exists(): shutil.rmtree(TMP)
TMP.mkdir()
EXT={".jpg",".jpeg",".png",".webp",".bmp",".tif",".tiff"}

def nnum(name):
    m=re.search(r"(?i)\\bno\\s*([0-9]+)",name) or re.search(r"([0-9]+)",name)
    return int(m.group(1)) if m else 999999

def nkey(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\\d+)",s)]

items=[]
for p in sorted(ROOT.iterdir(),key=lambda x:nkey(x.name)):
    if p.name.startswith(".") or p.name.startswith("_") or p.name==OUT.name: continue
    num=nnum(p.name)
    if p.suffix.lower()==".zip":
        d=TMP/f"no_{num}"; d.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(p,"r") as z:
            for info in z.infolist():
                if info.is_dir(): continue
                q=Path(info.filename)
                if q.suffix.lower() not in EXT: continue
                dst=d/q.name
                k=1
                while dst.exists():
                    dst=d/f"{q.stem}_{k}{q.suffix}"; k+=1
                with z.open(info) as src,open(dst,"wb") as out:
                    shutil.copyfileobj(src,out)
                items.append((num,dst,q.stem))
    elif p.suffix.lower() in EXT:
        items.append((num,p,p.stem))

items.sort(key=lambda t:(t[0],nkey(t[1].name)))
print("PHOTO_COUNT",len(items))
for num,path,stem in items:
    print(f"ITEM no={num} file={path} stem={stem}")

W,H=A4
mx=my=28
gx=gy=16
cw=(W-2*mx-gx)/2
ch=(H-2*my-gy)/2
cap=38
pad=8
ibw=cw-2*pad
ibh=ch-cap-2*pad

c=canvas.Canvas(str(OUT),pagesize=A4)
c.setTitle("")
c.setAuthor("")

group_count={}
for idx,(num,path,stem) in enumerate(items):
    slot=idx%4
    if slot==0 and idx>0: c.showPage()
    row,col=slot//2,slot%2
    x=mx+col*(cw+gx)
    y=H-my-(row+1)*ch-row*gy

    c.setStrokeColorRGB(.86,.86,.86)
    c.setLineWidth(.7)
    c.roundRect(x,y,cw,ch,7,stroke=1,fill=0)

    ix=x+pad
    iy=y+cap+pad
    try:
        im=ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        iw,ih=im.size
        s=min(ibw/iw,ibh/ih)
        dw,dh=iw*s,ih*s
        dx=ix+(ibw-dw)/2
        dy=iy+(ibh-dh)/2
        bio=io.BytesIO()
        im.save(bio,format="JPEG",quality=88,optimize=True)
        bio.seek(0)
        c.drawImage(ImageReader(bio),dx,dy,width=dw,height=dh,preserveAspectRatio=True,mask="auto")
    except Exception as e:
        c.setFont("Helvetica",9)
        c.setFillColorRGB(.45,.45,.45)
        c.drawCentredString(x+cw/2,iy+ibh/2,"Foto tidak dapat dibaca")
        print("IMAGE_ERROR",path,e)

    group_count[num]=group_count.get(num,0)+1
    label=f"No. {num}" if num!=999999 else "Tanpa nomor"
    c.setFillColorRGB(.12,.12,.12)
    c.setFont("Helvetica-Bold",11)
    c.drawString(x+pad,y+23,label)

    desc=f"Foto {group_count[num]}"
    c.setFont("Helvetica",8.5)
    c.setFillColorRGB(.38,.38,.38)
    c.drawString(x+pad,y+9,desc)

if not items:
    c.setFont("Helvetica",14)
    c.drawCentredString(W/2,H/2,"Tidak ada foto yang ditemukan")

c.save()
print("WROTE",OUT,OUT.stat().st_size)
