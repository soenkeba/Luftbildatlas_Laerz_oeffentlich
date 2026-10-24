"""Lädt die Geobasisdaten M-V (WMS, CC BY 4.0, © GeoBasis-DE/M-V) für das Arbeitsgebiet.
Arbeitsgebiet: E 348600–351000, N 5906700–5909100 (EPSG:25833). Karten-Meter: x = E-348600, y = 5909100-N."""
import subprocess
B="348600,5906700,351000,5909100"
def get(svc,layer,out,w,fmt="image/jpeg",style="",extra=""):
    url=(f"https://www.geodaten-mv.de/dienste/{svc}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={layer}"
         f"&STYLES={style}&CRS=EPSG:25833&BBOX={B}&WIDTH={w}&HEIGHT={w}&FORMAT={fmt}{extra}")
    subprocess.run(["curl","-s","-m","300","-o",out,url],check=True)
get("adv_dop","mv_dop","rnow.jpg",4000)                 # 0,6 m/px
get("dop1953_wms","mv_dop1953","r53.jpg",2400)          # 1,0 m/px
get("alkis_wms","adv_alkis_flurstuecke,adv_alkis_gebaeude","alkis.png",4000,"image/png","Gelb,Gelb","&TRANSPARENT=TRUE")
