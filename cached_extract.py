import newspaper
import os
import multiprocessing

from newspaper import Config, nlp, news_pool

def article_parse(_sources):
    for source in _sources:
        for article in source.articles:
            article.parse()
            sentences = newspaper.nlp.split_sentences(article.text)
            sentences = [sentence.replace('\n','') for sentence in sentences]
            
            with open('output.txt','a') as f:
                [f.write(sentence + '\n') for sentence in sentences]

def main():
    sites = argv[1:]
    config = Config()
    config.language = 'id'
    config.MIN_SENT_COUNT = 20
    config.memoize = False
    config.fetch_images = False

    kompas = newspaper.build('http://www.kompas.com', config=config)
    tempo = newspaper.build('http://www.tempo.co', config=config)
    republika = newspaper.build('http://www.republika.co.id', config=config)
    sources = [kompas, tempo, republika]

    news_pool.set(sources, threads_per_source = 4)
    news_pool.join()

    article_parse(sources)
    

if __name__ == ('__main__'):
    main()

