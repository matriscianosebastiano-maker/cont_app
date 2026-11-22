import urllib.request, os
from PIL import Image, ImageDraw
rows=[l.rstrip("\n").split("\t") for l in open("media.tsv") if "\t" in l]
os.makedirs("out",exist_ok=True)
W,H,C=400,300,5
n=len(rows); R=(n+C-1)//C
sheet=Image.new("RGB",(W*C,(H+30)*R),"white"); d=ImageDraw.Draw(sheet)
for i,(name,url) in enumerate(rows):
    try:
        p=f"img{i}"; urllib.request.urlretrieve(url+"/v1/fit/w_800,h_800/x.jpg",p)
        im=Image.open(p).convert("RGB"); im.thumbnail((W,H))
        x,y=(i%C)*W,(i//C)*(H+30)
        sheet.paste(im,(x+(W-im.width)//2,y+(H-im.height)//2))
        d.text((x+5,y+H+5),f"{i}: {name[:40]}",fill="black")
    except Exception as e: print(i,e)
sheet.save("out/sheet.jpg",quality=85)
