import newspaper
from newspaper import Config, Source
from newspaper.source import Category

class IntiSource(Source):

    def inti_set_categories():
        pass

    # Manually set categories from a list
    def set_categories(self, category_list):
        self.categories = [Category(category_url) for category_url in category_list]

