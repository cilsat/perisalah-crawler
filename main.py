import newspaper
import os
import multiprocessing
import sys
from time import strftime

from newspaper import Config, news_pool, utils, urls
from newspaper.source import Source, Category
from newspaper.extractors import ContentExtractor

from tldextract import tldextract

TOP_PATH = os.path.dirname(__file__)
OUT_PATH = os.path.join(TOP_PATH, 'output')
CAT_PATH = os.path.join(TOP_PATH, 'categories.txt')


class IntiExtractor(ContentExtractor):

    def get_category_urls(self, source_url, doc):
        """Inputs source lxml root and source url, extracts domain and
        finds all of the top level urls, we are assuming that these are
        the category urls.
        cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
        """
        page_urls = self.get_urls(doc)
        valid_categories = []
        for p_url in page_urls:
            scheme = urls.get_scheme(p_url, allow_fragments=False)
            domain = urls.get_domain(p_url, allow_fragments=False)
            path = urls.get_path(p_url, allow_fragments=False)

            if not domain and not path:
                if self.config.verbose:
                    print('elim category url %s for no domain and path'
                            % p_url)
                    continue
            if path and path.startswith('#'):
                if self.config.verbose:
                    print('elim category url %s path starts with #' % p_url)
                continue
            if scheme and (scheme != 'http' and scheme != 'https'):
                if self.config.verbose:
                    print(('elim category url %s for bad scheme, '
                        'not http nor https' % p_url))
                    continue

            if domain:
                child_tld = tldextract.extract(p_url)
                domain_tld = tldextract.extract(source_url)
                child_subdomain_parts = child_tld.subdomain.split('.')
                subdomain_contains = False
                for part in child_subdomain_parts:
                    if part == domain_tld.domain:
                        if self.config.verbose:
                            print(('subdomain contains at %s and %s' %
                                (str(part), str(domain_tld.domain))))
                            subdomain_contains = True
                        break

                # Ex. microsoft.com is definitely not related to
                # espn.com, but espn.go.com is probably related to espn.com
                if not subdomain_contains and \
                        (child_tld.domain != domain_tld.domain):
                            if self.config.verbose:
                                print(('elim category url %s for domain '
                                    'mismatch' % p_url))
                                continue
                elif child_tld.subdomain in ['m', 'i']:
                    if self.config.verbose:
                        print(('elim category url %s for mobile '
                            'subdomain' % p_url))
                        continue
                else:
                    valid_categories.append(scheme+'://'+domain)
                    # TODO account for case where category is in form
                    # http://subdomain.domain.tld/category/ <-- still legal!

        stopwords = [
                'about', 'help', 'privacy', 'legal', 'feedback', 'sitemap',
                'profile', 'account', 'mobile', 'sitemap', 'facebook', 'myspace',
                'twitter', 'linkedin', 'bebo', 'friendster', 'stumbleupon',
                'youtube', 'vimeo', 'store', 'mail', 'preferences', 'maps',
                'password', 'imgur', 'flickr', 'search', 'subscription', 'itunes',
                'siteindex', 'events', 'stop', 'jobs', 'careers', 'newsletter',
                'subscribe', 'academy', 'shopping', 'purchase', 'site-map',
                'shop', 'donate', 'newsletter', 'product', 'advert', 'info',
                'tickets', 'coupons', 'forum', 'board', 'archive', 'browse',
                'howto', 'how to', 'faq', 'terms', 'charts', 'services',
                'contact', 'plus', 'admin', 'login', 'signup', 'register',
                'developer', 'proxy']

        _valid_categories = []

        # TODO Stop spamming urlparse and tldextract calls...

        for p_url in valid_categories:
            path = urls.get_path(p_url)
            subdomain = tldextract.extract(p_url).subdomain
            conjunction = path + ' ' + subdomain
            bad = False
            for badword in stopwords:
                if badword.lower() in conjunction.lower():
                    if self.config.verbose:
                        print(('elim category url %s for subdomain '
                            'contain stopword!' % p_url))
                        bad = True
                    break
            if not bad:
                _valid_categories.append(p_url)

        _valid_categories.append('/')  # add the root

        for i, p_url in enumerate(_valid_categories):
            if p_url.startswith('://'):
                p_url = 'http' + p_url
                _valid_categories[i] = p_url

            elif p_url.startswith('//'):
                p_url = 'http:' + p_url
                _valid_categories[i] = p_url

            if p_url.endswith('/'):
                p_url = p_url[:-1]
                _valid_categories[i] = p_url

        _valid_categories = list(set(_valid_categories))

        category_urls = [urls.prepare_url(p_url, source_url)
                for p_url in _valid_categories]
        category_urls = [c for c in category_urls if c is not None]
        return category_urls


class IntiSource(Source):

    def __init__(self, url, config=None, **kwargs):
        """The config object for this source will be passed into all of this
        source's children articles unless specified otherwise or re-set.
        """
        if (url is None) or ('://' not in url) or (url[:4] != 'http'):
            raise Exception('Input url is bad!')

        self.config = config or Configuration()
        self.config = utils.extend_config(self.config, kwargs)

        self.extractor = IntiExtractor(self.config)

        self.url = url
        self.url = urls.prepare_url(url)

        self.domain = urls.get_domain(self.url)
        self.scheme = urls.get_scheme(self.url)

        self.categories = []
        self.feeds = []
        self.articles = []

        self.html = ''
        self.doc = None

        self.logo_url = ''
        self.favicon = ''
        self.brand = tldextract.extract(self.url).domain
        self.description = ''

        self.is_parsed = False
        self.is_downloaded = False

    def build(self, response=None):
        """Encapsulates download and basic parsing with lxml. May be a
        good idea to split this into download() and parse() methods.
        """
        self.download()
        self.parse()

        self.set_categories()
        self.add_categories()
        self.download_categories()  # mthread
        self.parse_categories()

        self.set_feeds()
        self.download_feeds()       # mthread
        # TODO: self.parse_feeds()  # regex for now

        self.generate_articles()

    # HARDCODED for now. Ugly as hell
    def add_categories(self):
        print("ADDING CATEGORIES MANUALLY")
        # Open categories.txt
        categ = []
        with open(CAT_PATH, 'r') as f:
            categ = f.read().split('\n')

        # get the words to check for to indicate category
        words = []
        categ = [line for line in categ if not line.startswith('#')]
        for n in range(len(categ)):
            if categ[n].startswith(self.domain):
                words = categ[n].split(',')[1:]

        # get all urls in html (again)
        print(self.url + '\n')
        # add matched urls as categories
        all_urls = self.extractor.get_urls(self.doc)
        added_categories = []
        for word in words:
            for url in all_urls:
                if word in url:
                    full_url = self.url + url
                    self.categories.append(Category(url=full_url))



def article_parse(_sources):
    for source in _sources:
        for article in source.articles:
            timenow = strftime("%Y%m%d-%H%M%S")
    article.parse()

    #sentences = newspaper.nlp.split_sentences(article.text)
    #sentences = [sentence.replace('\n','') for sentence in sentences]

    filename = article.title.replace(' ','_')
    print(filename)

    # Write a sort-of-xml containing our metadata and text
    with open(os.path.join(OUT_PATH, source.domain, filename),'w') as f:
        f.write("<title>" + article.title + "</title>\n")
        f.write("<url>" + article.url + "</url>\n")
        f.write("<retrieved>" + timenow + "</retrieved>\n")
        f.write("<authors>")
        for n in range(len(article.authors)):
            f.write("\t<author id=" + str(n) + ">" + article.authors[n] + "</author>\n")
        f.write("</authors>\n")
        f.write("<text>" + article.text + "</text>\n")


def main(argv):
    TOP_PATH = os.path.dirname(__file__)
    OUT_PATH = os.path.join(TOP_PATH, 'output')
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)

    # Our permanent config for crawling
    config = Config()
    config.language = 'id'
    config.MIN_SENT_COUNT = 20
    config.memoize = False
    config.fetch_images = False
    config.verbose= True

    # Get contents of our source file
    sourcefile = os.path.join(TOP_PATH, "sources.txt")
    with open(os.path.join(sourcefile), 'r') as f:
        sourcelist = f.read().strip().split('\n')

    # Initialize our sources
    sources = [IntiSource(source,config=config) for source in sourcelist]

    # Make domain directories inside our output path and build sources
    for s in sources:
        if not os.path.exists(os.path.join(OUT_PATH, s.domain)):
            dom_path = os.path.join(OUT_PATH, s.domain)
            os.makedirs(dom_path)

        # Build
        s.build()

        if config.verbose:
            s.print_summary()

    # Multithreaded source downloading and parsing
    news_pool.set(sources, threads_per_source = 4)
    news_pool.join()

    article_parse(sources)


if __name__ == ('__main__'):
    main(sys.argv)
