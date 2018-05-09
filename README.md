# DIP - Manual
Master Thesis: Torrent Peer Monitoring<br>
Author: David Bezdek, xbezde11@stud.fit.vutbr.cz<br>
Faculty of Information Technology, Brno University of Technology<br>
23. 5. 2018

Tento adresář obsahuje zdrojové soubory k diplomové práci Monitorování peerů sdílejících Torrenty.

## Obsah adresáře:
1. crawler - obsahující zdrojové soubory k modulu DHT Crawler:
   - btdht_crawler.py - crawler využívající knihovnu btdht.
   - dht_crawler.py - crawler implementující moduly IPv4 a IPv6 DHT crawler.
   - evaluator.py - pomocný skript, který prohledá všechny soubory s prefixem output ve složce, ve které je umístěný.
   - rss_age_finder.py - jednoduchý skript, který načte vybraný RSS soubor a zjišťuje stáří jednotlivých torrentů.
  
2. evaluating:
   - geo_analyzer.py - zdrojový soubor pro geografickou lokalizaci
   - summarizer.py - skript, který prohledává soubory output od DHT crawlerů v dostupných složkách. Tento soubor je nutné umístit do adresáře Data.
   - p_count - Prochází složky s prefixem "exp" a sumarizuje výsledky všech jednotlivých měření. Počítá pravděpodobnost nalezení uzlu p včetně odchylky. Je nutné jej umístit do adresáře Data.
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
   - setter.py - tento skritp vytvoří soubor s 50ti ID uzlů pro injektované uzly. Také vygeneruje 5 ID pro crawlery a příkazy ke spuštění crawlerů vypisuje na stdout.
   - xnode_crawler.py - IPv4 i IPv6 crawler
   - xnode_crawler_no_limits.py - IPv4 i IPv6 crawler bez omezení pro kompletní crawling sítě. !!! to-do
   - xnode_maintainer.py - soubor, který poskytuje uzly ze stejné 12 bitové zóny.
  
6. client-socket.py - zdrojový soubor implementující klientskou část aplikačního rozhraní.

## Manuál
Pro zdrojový soubor btdht_crawler.py je zapotřebí nainstalovat knihovnu příkazem:
sudo pip install btdht

### Spuštění modulů DHT crawleru
Výpis nápovědy se seznamem možných parametrů, které lze libovolně kompinovat: <br>
    -r [--rss] URL -- URL of RSS feed <br>
    -i [--input-announcement] filename -- already downloaded RSS feed <br>
    -c [--set-limit] -- choose number of files ( negative number means files from the end ) <br>
    -s [--substr] -- substring for choosing files - case sensitive! <br>
    -v [--verbose] -- choose between version with or without outputs <br>
    -t [--type] number -- (4 or 6) choose type of crawler (IPv4 or IPv6). Implicit IPv4 <br>

Příklady spuštění: <br>
- python btdht_crawler.py <br>(automaticky hledá soubor rss_feed.xml, pokud neexistuje, tak jej stáhne a vytvoří a následné vyhledává peery pro všechny torrenty) <br>
- python btdht_crawler.py -i rss_file_name.xml <br> (vyhledávání peerů pro všechny torrenty z daného souboru) <br>
- python btdht_crawler.py -r url <br>(stáhne RSS soubor z daného url) <br>
- python btdht_crawler.py -c 10  <br>(vyhledávání peerů pro prvních 10 torrentů z daného souboru) <br>
- python btdht_crawler.py -c -10 <br>(vyhledávání peerů pro posledních 10 torrentů z daného souboru) <br>
- python btdht_crawler.py -i rss_file_name.xml -c -10 <br>
- python btdht_crawler.py -v <br> (vypnutí výpisů na stdout) <br>
- python btdht_crawler.py -s substring <br>(vyhledávání peerů pro torrenty, které v názvu obsahují zadaný podřetězec) <br>
   <br>
dht_crawler je obohacen o parametr -t, který určí typ crawleru (IPv4 nebo IPv6) <br>
- python dht_crawler.py -t 6 <br> (přepne crawler pro protokol IPv6) <br>
- python dht_crawler.py -i rss_file_name.xml -c -10 -t 6 <br> <br>

Pomocné skripty: <br>
- python summanizer.py <br> (spouští se ve složce Data)
- python rss_age_finder.py -i rss_feed.xml -c 10
- python evaluator.py  <br> (spouští se ve složce obsahující výstupy DHT crawlerů)

### Spuštění skriptu evaluating
Pro tento skript je důležité, aby ve stejné složce byly umístěny databáze ip.db a ip6.db obsahující potřebné lokalizační informace. Testovaný soubor nemusí být ve stejné složce.
- python geo_analyzer.py logfile

### Spuštění modulů Zónových agentů
Tyto skripty se spouštějí v pořadí, ve kterém jsou uvedené, tzn.: 1. setter, 2. xnode_maintainer, 3. node_injector, 4. xnode_crawler, 5. finder, 6. p_count
- python setter.py <br> (příprava ID pro experiment + výpis příkazů pro spuštění zbylých zdrojových souborů) 
- python xnode_maintainer.py --id 605790311400116453953805559992836567457494275251 -t 4 
- python xnode_maintainer.py --id 605790311400116453953805559992836567457494275251 -t 6 <br><br>

- python node_injector.py 605790311400116453953805559992836567457494275251 
- python node_injector6.py 605790311400116453953805559992836567457494275251 <br><br>

- python xnode_crawler.py --id 605851242537948466844038222167079975228757870220 -t 4
- python xnode_crawler.py --id 605851242537948466844038222167079975228757870220 -t 6 <br><br>

- python finder.py <br> (finder se spouští ve složce se soubory [ipv4/ipv6]nodes)
- python p_count.py <br> (p_count se spouští ve složce Data)

### Spuštění souborů aplikačního rozhraní

1. Server se spustí na pozadí:
   - python3 dht_server_obj.py &
   - python3 dht_server_obj.py <br> (při spuštění na popředí lze pozorovat statistiky ohledně ukládání do databáze typu: kolik uzlů/peerů bylo přidáno, kolik bylo duplicitních, čas atd.)
  
2. Klient:
   - python3 client-socket.py -r
   - python3 client-socket.py -r ipv4nodes.json
   - python3 client-socket.py -s ipv6 <br> (prefix souborů, které bude klient posílat)
   - python3 client-socket.py -s ipv6nodes.id.datum.json
