#!/usr/bin/env python3
from selenium import webdriver

import argparse
import html
import itertools
import re
import selenium
import sys
import time


VERSION = '1.0'

#################
# global options
#################
options = {}


##########
# helpers
##########

def get_unique_list(values):
    return list(set(values))


###############
# core classes
###############

class ArgsParser(object):
    _DEFAULT_DEPTH = 0
    _DEFAULT_MAX_SCROLLS = 0
    _DEFAULT_MIN_WORD_LENGTH = 3
    _DEFAULT_PAGE_LOAD_DELAY = 3.0
    _DEFAULT_PAGE_SCROLL_DELAY = 1.0

    @staticmethod
    def parse():
        parser = argparse.ArgumentParser(
            description='Words scraper (version: %s)' % VERSION,
        )

        # optional
        parser.add_argument(
            '--depth',
            help='scraping depth, default: %d' % ArgsParser._DEFAULT_DEPTH,
            type=ArgsParser._parse_int_positive,
            default=ArgsParser._DEFAULT_DEPTH,
        )
        parser.add_argument(
            '--max-scrolls',
            help='maximum number of the page scrolls, default: %d' % ArgsParser._DEFAULT_MAX_SCROLLS,
            type=ArgsParser._parse_int_positive,
            default=ArgsParser._DEFAULT_MAX_SCROLLS,
        )
        parser.add_argument(
            '--min-word-length',
            help='default: %d' % ArgsParser._DEFAULT_MIN_WORD_LENGTH,
            type=ArgsParser._parse_int_gt_0,
            default=ArgsParser._DEFAULT_MIN_WORD_LENGTH,
        )
        parser.add_argument(
            '--page-load-delay',
            help='page loading delay, default: %.1f' % ArgsParser._DEFAULT_PAGE_LOAD_DELAY,
            type=ArgsParser._parse_float_positive,
            default=ArgsParser._DEFAULT_PAGE_LOAD_DELAY,
        )
        parser.add_argument(
            '--page-scroll-delay',
            help='page scrolling delay, default: %.1f' % ArgsParser._DEFAULT_PAGE_SCROLL_DELAY,
            type=ArgsParser._parse_float_positive,
            default=ArgsParser._DEFAULT_PAGE_SCROLL_DELAY,
        )
        parser.add_argument(
            '--show-gui',
            help='show browser GUI',
            action='store_true'
        )
        parser.add_argument(
            '--socks-proxy',
            help='socks proxy e.g. 127.0.0.1:1080',
            type=ArgsParser._parse_socks_proxy,
        )

        # required
        parser.add_argument(
            '-o', '--output-file',
            help='save words to file',
            type=argparse.FileType('w'),
            required=True,
        )
        parser.add_argument(
            'url',
            help='URL to scrape',
            nargs='+'
        )
        args = parser.parse_args(sys.argv[1:])
        return {
            'depth': args.depth,
            'max_scrolls': args.max_scrolls,
            'min_word_length': args.min_word_length,
            'output_file': args.output_file,
            'page_load_delay': args.page_load_delay,
            'page_scroll_delay': args.page_scroll_delay,
            'show_gui': args.show_gui,
            'socks_proxy': args.socks_proxy,
            'urls': args.url,
        }

    @staticmethod
    def _parse_float_positive(value):
        try:
            float_value = float(value)
            if float_value < 0:
                raise argparse.ArgumentTypeError('must be positive')
            return float_value
        except ValueError:
            raise argparse.ArgumentTypeError('must be float')

    @staticmethod
    def _parse_int_gt_0(value):
        try:
            int_value = int(value)
            if int_value <= 0:
                raise argparse.ArgumentTypeError('must be greater than 0')
            return int_value
        except ValueError:
            raise argparse.ArgumentTypeError('must be int')

    @staticmethod
    def _parse_int_positive(value):
        try:
            int_value = int(value)
            if int_value < 0:
                raise argparse.ArgumentTypeError('must be positive')
            return int_value
        except ValueError:
            raise argparse.ArgumentTypeError('must be int')

    @staticmethod
    def _parse_socks_proxy(value):
        try:
            proxy = value.split(':')
            if len(proxy) != 2:
                raise argparse.ArgumentTypeError('invalid proxy')
            port = int(proxy[1])
            if port < 0 or port > 65535:
                raise argparse.ArgumentTypeError('invalid proxy port')
            return {
                'host': proxy[0],
                'port': port,
            }
        except ValueError:
            raise argparse.ArgumentTypeError('invalid proxy')


class HtmlParser(object):
    def __init__(self, driver):
        self._driver = driver

    def get_words(self, source):
        words = []
        words += self._extract_words_from_html_comments(source)
        words += self._extract_words_from_text(source)
        for word in words:
            if self._is_length_enough(word):
                yield word

    def get_urls(self):
        urls = []
        for link in self._driver.find_elements_by_xpath('//a[@href]'):
            urls.append(link.get_attribute('href'))
        return urls

    @staticmethod
    def _extract_words_from_html_comments(source):
        text = ''
        for comment in re.findall(r'<!--(.*?)-->', source, flags=re.DOTALL):
            text += comment
        return html.unescape(text).split()

    @staticmethod
    def _extract_words_from_text(source):
        regexps = [
            r'<script.*?>.*?</script>',
            r'<style.*?>.*?</style>',
            r'<.*?>',
        ]
        text = source
        for regexp in regexps:
            text = re.sub(regexp, ' ', text, flags=re.DOTALL | re.IGNORECASE)
        return html.unescape(text).split()

    @staticmethod
    def _is_length_enough(value):
        return len(value) >= options['min_word_length']


class HttpClient(object):
    def __init__(self):
        driver_options = selenium.webdriver.FirefoxOptions()
        driver_options.headless = not options['show_gui']
        firefox_profile = webdriver.FirefoxProfile()
        if options['socks_proxy']:
            firefox_profile.set_preference('network.proxy.type', 1)
            firefox_profile.set_preference('network.proxy.socks', options['socks_proxy']['host'])
            firefox_profile.set_preference('network.proxy.socks_port', options['socks_proxy']['port'])
            firefox_profile.set_preference('network.proxy.socks_remote_dns', True)
        self._driver = selenium.webdriver.Firefox(options=driver_options, firefox_profile=firefox_profile)

    def get(self, url):
        return itertools.chain(
            self._load_page(url),
            self._scroll_page()
        )

    def get_driver(self):
        return self._driver

    def quit(self):
        self._driver.quit()

    def _get_scroll_top(self):
        return self._driver.execute_script('return document.documentElement.scrollTop')

    def _load_page(self, url):
        self._driver.get(url)
        time.sleep(options['page_load_delay'])
        yield self._driver.page_source

    def _scroll_page(self):
        prev_scroll_top = self._get_scroll_top()
        scroll_times = 0
        while scroll_times < options['max_scrolls']:
            self._driver.execute_script('window.scrollBy(0, document.documentElement.clientHeight)')
            curr_scroll_top = self._get_scroll_top()
            if curr_scroll_top == prev_scroll_top:
                break
            prev_scroll_top = curr_scroll_top
            time.sleep(options['page_scroll_delay'])
            yield self._driver.page_source
            scroll_times += 1


class Scraper(object):
    _ALLOWED_SCHEMAS = ['http://', 'https://']

    def __init__(self, html_parser, http_client):
        self._html_parser = html_parser
        self._http_client = http_client
        self._scrapped_urls = []
        self._words = {}

    def run(self):
        try:
            for url in options['urls']:
                self._scrape_url(url, 0)
            self._save_words()
        finally:
            self._http_client.quit()

    def _is_url_allowed(self, url):
        url_low = url.lower()
        for allowed_schema in self._ALLOWED_SCHEMAS:
            if url_low.startswith(allowed_schema):
                return True
        return False

    def _save_words(self):
        words = [k for k, v in sorted(self._words.items(), key=lambda item: item[1], reverse=True)]
        output_file = options['output_file']
        if words:
            output_file.write('\n'.join(words))
            output_file.write('\n')
        output_file.close()
        print('Saved %d words' % len(words))

    def _scrape_url(self, url, depth):
        print('Scrapping %s' % url)
        self._scrapped_urls.append(url)
        urls = []
        for page in self._http_client.get(url):
            for word in self._html_parser.get_words(page):
                if word not in self._words:
                    self._words[word] = 0
                self._words[word] += 1
            if depth < options['depth']:
                for url in self._html_parser.get_urls():
                    if self._is_url_allowed(url):
                        urls.append(url)
        for url in get_unique_list(urls):
            if url not in self._scrapped_urls:
                self._scrape_url(url, depth + 1)


def main():
    global options

    options = ArgsParser.parse()
    http_client = HttpClient()
    html_parser = HtmlParser(http_client.get_driver())

    Scraper(html_parser, http_client).run()


if __name__ == '__main__':
    main()
