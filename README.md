# GoPro Videolapse

## Kommandoer (Fra GoProControl)

Gopro har ett åpent og ett internt eks. via app.  
Åpen bruker IP:8080/gopro/  
Lukket bruker IP:8080/gp/  
Åpen dokumentasjon: https://gopro.github.io/OpenGoPro/http_2_0  
Lukket dokumentasjon: https://github.com/KonradIT/goprowifihack  
Lukket er mye større, med støtte for mer instillinger, mens åpen returnerer mer data.  
  
For å slette videoer: http://\[camIp\]:8080/gopro/media/delete/file?path=100GOPRO/\[clip name\]

## GoProLabs

!MBOOT="mVr4p50fL0te0dR60d1b1wAg0v0q0dVoV0B4D2C0SW0!S"!MWAKE=2!MTUSB=1

!MBOOT="mVr4p50fSte0hS0dR30d1b0!S"!MWAKE=2!MTUSB=1

## Miljø

Python versjon testet: `Python 3.11`, `Python 3.9`  
Biblioteker som trengs: `re`, `os`, `requests`, `psutil`, `time`, `datetime`, `suntime`  

Komando for å installere alle bibliotek: `python3 -m pip install re os requests psutil time datetime suntime`  

## Hardware liste

Liste over alle komponenter som trengs:

- Raspberrypi
- Internett/mobildata adapter
- Batteri-circut
- Kamera
- USB-C kabel mellom gopro og raspberrypi
- helst-vanntett boks å ha det oppi