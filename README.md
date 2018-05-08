# DIP - Manual
Master Thesis: Torrent Peer Monitoring
Author: David Bezdek, xbezde11@stud.fit.vutbr.cz
Faculty of Information Technology, Brno University of Technology
23. 5. 2018

Tento adresář obsahuje zdrojové soubory k práci Monitorování peerů sdílejících Torrenty.

## Obsah adresáře:
1. crawler - obsahující zdrojové soubory k modulu DHT Crawler:
  - btdht_crawler.py - crawler využívající knihovnu btdht.
  - dht_crawler.py - crawler implementující moduly IPv4 a IPv6 DHT crawler.
  - evaluator.py - pomocný skript, který prohledá všechny soubory s prefixem output ve složce, ve které je umístěný.
  - summarizer.py - skript, který prohledává soubory output v dostupných složkách. Tento soubor je nutné umístit do adresáře obsahujícího složky s prefixem "peers".
  - rss_age_finder.py - jednoduchý skript, který načte vybraný RSS soubor a zjišťuje stáří jednotlivých torrentů.
  
2. evaluating:
  - geo_analyzer.py - zdrojový soubor pro geografickou lokalizaci
  
3. imports - adresář obsahující pomocné zdrojové soubory:
  - python moduly bencode a common
  - abstract_crawler.py - abstraktní třída pro monitorovací moduly
  - db_utils.py - zdrojový soubor obsahující pomocné funkce
  - khash.py - zdrojový soubor volně dostupný pod licencí BitTorrent Open Source License obsahující pomocné funkce pro práci se 160 bitovými ID uzlů atd.
  - param_parser.py - zdrojový soubor s pomocnou třídou pro zpracování argumentů terminálu
  - torrent_crawler.py - třída implementující stažení a uložení RSS souborů
  
4. server

5. zone_agents
zdrojový soubor: client-socket.py

