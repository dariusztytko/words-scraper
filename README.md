# Words Scraper
Selenium based web scraper to generate passwords list.

## Installation
```
# Download Firefox webdriver from https://github.com/mozilla/geckodriver/releases
$ tar xzf geckodriver-v{VERSION-HERE}.tar.gz
$ sudo mv geckodriver /usr/local/bin # Make sure it is in your PATH
$ geckodriver --version # Make sure webdriver is properly installed
$ git clone https://github.com/dariusztytko/words-scraper
$ sudo pip3 install -r words-scraper/requirements.txt
```

## Use cases

### Scraping words from the company's pages

```
$ python3 words-scraper.py -o words.txt https://www.example.com https://blog.example.com
```
Use *--depth* option to scrape words from the linked pages as well.
Optional *--show-gui* switch may be useful to track the progress and make quick view of the company page.
```shell script
$ python3 words-scraper.py -o words.txt --show-gui --depth 1 https://www.example.com
```

Generated word list can be expanded by using words-converter.py script.
This script removes special chars and accents.
E.g. Polish word *źdźbło!* will be splitted into the following words:
* źdźbło!
* zdzblo!
* źdźbło
* zdzblo
```
$ cat words.txt | python3 words-converter.py | sort -u > words2.txt
```

### Scraping words from the company's Twitter
Twitter page is dynamically loaded while scrolling.
Use *--max-scrolls* option to scrape words.
```shell script
$ python3 words-scraper.py -o words.txt --show-gui --max-scrolls 500 https://twitter.com/example.com
```

### Scraping via Socks proxy
```
$ ssh -D 1080 -Nf {USER-HERE}@{IP-HERE} >/dev/null 2>&
$ python3 words-scraper.py -o words.txt --socks-proxy 127.0.0.1:1080 https://www.example.com
```

## Usage
```
usage: words-scraper.py [-h] [--depth DEPTH] [--max-scrolls MAX_SCROLLS]
                         [--min-word-length MIN_WORD_LENGTH]
                         [--page-load-delay PAGE_LOAD_DELAY]
                         [--page-scroll-delay PAGE_SCROLL_DELAY] [--show-gui]
                         [--socks-proxy SOCKS_PROXY] -o OUTPUT_FILE
                         url [url ...]

Words scraper (version: 1.0)

positional arguments:
  url                   URL to scrape

optional arguments:
  -h, --help            show this help message and exit
  --depth DEPTH         scraping depth, default: 0
  --max-scrolls MAX_SCROLLS
                        maximum number of the page scrolls, default: 0
  --min-word-length MIN_WORD_LENGTH
                        default: 3
  --page-load-delay PAGE_LOAD_DELAY
                        page loading delay, default: 3.0
  --page-scroll-delay PAGE_SCROLL_DELAY
                        page scrolling delay, default: 1.0
  --show-gui            show browser GUI
  --socks-proxy SOCKS_PROXY
                        socks proxy e.g. 127.0.0.1:1080
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        save words to file
```

## Known bugs
* Native browser dialog boxes (e.g. file download) freeze scraper

## Changes
Please see the [CHANGELOG](CHANGELOG)
