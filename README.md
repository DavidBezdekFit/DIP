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
  
4. server:
   - dtb - adresář obsahující soubory pro vytvoření a přístup k databázi:
    - fill_db_class.py - zápis dat do databáze
    - read_db_class.py - čtení dat z databáze
    - set_db.py - vytvoření databáze
   - dht_server_obj.py - zdrojový soubor implementovaného serveru

5. zone_agents
   - fidner.py - soubor, který se spouští po vícero spuštění crawlerů. Prochází soubory s uzly a snaží se v nich najít uzly ze souboru obsahující ID injektovaných uzlů.
   - node_injector.py - injektované uzly
   - node_injector6.py - injektované uzly pro IPv6
   - p_count - Prochází složky s prefixem "exp" a sumarizuje výsledky všech jednotlivých měření. Počítá pravděpodobnost nalezení uzlu p včetně odchylky.
   - setter.py - tento skritp vytvoří soubor s 50ti ID uzlů pro injektované uzly. Také vygeneruje 5 ID pro crawlery a příkazy ke spuštění crawlerů vypisuje na stdout.
   - xnode_crawler.py - IPv4 i IPv6 crawler
   - xnode_crawler_no_limits.py - IPv4 i IPv6 crawler bez omezení pro kompletní crawling sítě. !!! to-do
   - xnode_maintainer.py - soubor, který poskytuje uzly ze stejné 12 bitové zóny.
  
6. client-socket.py - zdrojový soubor implementující klientskou část aplikačního rozhraní.

## Manuál



