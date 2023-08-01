# VideoLapse til nasjonalpark prosjektet

## Hva skal det gjøre

Kameraoppsett som ikke skal være plugget til strøm og skal stå på en "øde" plass uten mulighet for lett fiksing onfield.  
Solcellepanel og batterier blir brukt for strømm, altså må systemet være strøm-effektivt.  
Systemet skal filme 30 sekund med video på solnedgang soloppgang og midt på dagen, automatisk.  

## Hvordan

### Hardware

* GoPro 11, siden HDR video, høy kvalitet, Styrbart og nogså strøm-effektivt.  
* Raspberrypi for å laste opp video til dropbox via 4g modem, regne ut solnedgang, etc.  
* Mikrokontroller (Stamp S3), for å styre hovedstrømm rele og skru på systemet på riktig tidspunkt.  
* 4G Modem, Waveshare SIM7600G-H 4G DONGLE, for internett, laste opp video til dropbox og synkronisere klokken.

### Tilkoblinger

* Raspberrypien har et 4g modem koblet til usb, det er ganske stabilt, men hvis det er problemer: https://www.waveshare.com/wiki/SIM7600G-H_4G_DONGLE  
* Raspberrypi og mikrokontroller kommuniserer over serial, via rx og tx pins på Raspberrypi. (Ustabilt, se videre utvikling)  
* GoPro er koblet til raspberrypi via en usb dongle, som får eksternstrømm (goproen booter ellers rett inn i datamaskin tilkoblet modus, og da kan den ikke filme).  
* Mikrokontrolleren er av typen M5-Stack Stamp S3, skal fungere med andre også, men ikke testet.
  * Den er koblet til usb til en serial logger (bare for å få debug info over USB serial), men skal bli plugget rett inn i usb på solkontrolleren.
  * Koden som er på denne er ESP32_Vidolapse_NoSleep, NoSleep er uten deep sleep, siden deep sleep våknet opp med en gang (mest sansynlig varierende strømm etter at man tar strømmen til systemet).

### Dropbox

For å sette opp dropbox trenger man bare en bruker, en "development app", en autentikasjons nøkkel (fra appen) og en refresh nøkkel.  
Grei forklaring: https://www.dropboxforum.com/t5/Dropbox-API-Support-Feedback/Get-refresh-token-from-access-token/td-p/596739

## Videre utvikling

Serial mellom raspberry og mikrokontroller fungerer ikke som det skal, det kommer gennerelt mye søppel over linja, og mye data blir korupt. Dette fungerte mye bedre for litt siden, men stoppet plutselig å fungere. (Dårlig kontakt i loddinga? feil på raspberrypi??)  
Enten må man finne en annen måte å få raspberryen til å vokne etter x mengder sekunder, eller fikse kommunikasjon til mikro, som ikke overfører strøm (Raspberrypi er flink til å stjele strøm fra enheter som er koblet på, og har derfor overlevd strømmkutt via mikrokontroller).  
  
Kabler må loddes sammen på en bedre måte og systemet må pakkes sammen i boksen.  
  
Det var snakk om at Håvard ville ha enda ett system også, så det må bygges.  

## Tailscale linker

Raspberrypi link: https://login.tailscale.com/admin/invite/GAs7zitj2ai  
SerialLogger link: https://login.tailscale.com/admin/invite/px7C1TMdf11  
