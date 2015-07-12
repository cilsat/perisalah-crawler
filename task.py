import newspaper
import os
import multiprocessing
import sys

from newspaper import Config, Source, nlp, news_pool
from newspaper.extractors import ContentExtractor

class IntiSource(Source):

    def inti_set_categories():
        pass

class IntiExtractor(ContentExtractor):

    def inti_get_categories():
        pass


if __name__ == ('__main__'):
    main(sys.argv)

"""
We need to define a common memo cache between task and past crawlers.
Newspaper memo caches are made per source url. For now we'll go along with it.
The task crawler runs for news articles that appear in the front page categories of the sources in our sources.txt file.
It scraps all the urls in these category pages without downloading them.
Thus NO RECURSION IS INVOLVED.

TODO: We need to expand each category of each subdomain of each domain into its own source
1. We need to modify the get_category() function within extractors.py to see all the categories beneath it. Since this will be called through Source we also need a custom Source class.
2. We need to call get_category() recursively to compile and return a list of sources instantiated from these categories. The stop condition must be formulated. This should probably be done in our custom Source child class.
3. We might want to do this just once and save the list of categories in the domain for future use, and build this list directly (instead of going through the top domain).
4. Our task and past crawlers must share the same memo cache
5. While running the task crawler we should check the memo_cache
"""
def main(argv):
    sourcelist = []
    if len(argv) > 1:
        sourcefile = argv[1]
        try:
            with open(sourcefile,'r') as f:
                sourcelist = f.read().strip().split('/n')
        except IOError:
            print("File does not exist")

    """
    Check for existence of memo cache
    If it doesn't exist, create memo cache and populate top sources file with the specified sources.txt file. If it is not specified return an error and terminate.
    If memo cache exists, if sources.txt is specified do a check against top sources and add any new ones. If no sources.txt is specified use top sources file.
     """
    firstrun = False
    memo_cache_path = os.path.join(os.path.dirname(__file__), '.memo_cache')
    if not os.path.exists(memo_cache_path):
        if len(sourcelist) > 0:
            firstrun = True
            os.makedirs(memo_cache_path)
            with open(os.path.join(memo_cache_path, '.top_sources'), 'w') as f:
                [f.write(source + '\n') for source in sourcelist]
        else:
            print("You must specify an input file on the first run")
            print("An input file contains line-separated urls to the top-level domains you wish to crawl")
            raise SystemExit
    else:
        if len(sourcelist) > 0:
            with open(os.path.join(memo_cache_path, '.top_sources'), 'w') as f:
                [f.write(source + '\n') for source in sourcelist]

        else:
            with open(os.path.join(memo_cache_path, '.top_sources'), 'r') as f:
                sourcelist = f.read().split('\n')

    # this config applies to the entire crawling process
    config = Config()
    config.language = 'id'
    config.MIN_SENT_COUNT = 20
    config.memoize = True
    config.fetch_images = False

    top_sources = [IntiSource(url=source,config=config) for source in sourcelist]

    if firstrun:
        build_categories(top_sources)

