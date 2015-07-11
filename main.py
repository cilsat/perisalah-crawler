import newspaper
import os
import multiprocessing
import sys

from newspaper import Config, nlp, news_pool

def article_parse(_sources):
    for source in _sources:
        for article in source.articles:
            article.parse()
            sentences = newspaper.nlp.split_sentences(article.text)
            sentences = [sentence.replace('\n','') for sentence in sentences]
            
            with open('output.txt','a') as f:
                [f.write(sentence + '\n') for sentence in sentences]

def rbuild(sources, depth):
    pass

def main(argv):
    sourcefile = argv[1]

    config = Config()
    config.language = 'id'
    config.MIN_SENT_COUNT = 20
    config.memoize = True
    config.fetch_images = False

    with open(os.path.join(os.path.dirname(__file__), sourcefile), 'r') as f:
        sourcelist = f.read().strip().split('\n')
    
    sources = [newspaper.build(url=source,config=config) for source in sourcelist]
    news_pool.set(sources, threads_per_source = 4)
    news_pool.join()

    article_parse(sources)
    

if __name__ == ('__main__'):
    main(sys.argv)
