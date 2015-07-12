import newspaper
import os
import multiprocessing
import sys
from time import strftime

from newspaper import Config, news_pool

TOP_PATH = os.path.dirname(__file__)
OUT_PATH = os.path.join(TOP_PATH, 'output')

def article_parse(_sources):
	for source in _sources:
		for article in source.articles:
			timenow = strftime("%Y%m%d-%H%M%S")
			article.parse()

			#sentences = newspaper.nlp.split_sentences(article.text)
			#sentences = [sentence.replace('\n','') for sentence in sentences]

			filename = timenow + '-' +  article.title.replace(' ','_')
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
	sources = [newspaper.build(url=source,config=config) for source in sourcelist]

	# Make domain directories inside our output path
	for s in sources:
		if not os.path.exists(os.path.join(OUT_PATH, s.domain)):
			dom_path = os.path.join(OUT_PATH, s.domain)
			os.makedirs(dom_path)
		s.print_summary()

	# Multithreaded source downloading and parsing
	news_pool.set(sources, threads_per_source = 4)
	news_pool.join()

	article_parse(sources)


if __name__ == ('__main__'):
	main(sys.argv)
