import gensim
import pymongo
import logging

from pathlib import Path
from datetime import datetime, timedelta
from scrapy.utils.project import get_project_settings

import jieba

class Sentences(object):
  def __init__(self, corpus: Path):
    self.corpus = corpus

  def __iter__(self):
    for fname in self.corpus.iterdir():
      if fname.is_file():
        for line in open(fname, 'r', encoding='utf-8'):
          yield line.split()

class WordVec(object):
  """
  Window Size: 5
  Dynamic Window: Yes
  Sub-sampling: 1e-5
  Low-Frequency Word: 10
  Iteration: 5
  """
  def __init__(self, dim=128):
    self.settings = get_project_settings()
    self.client = pymongo.MongoClient(self.settings['MONGO_HOST'], self.settings['MONGO_PORT'])
    self.db = self.client[self.settings['MONGO_DBNAME']]
    self.wallstreet = self.db[self.settings['MONGO_COLLECTION_WALLSTREET']]
    self.hexun = self.db[self.settings['MONGO_COLLECTION_HEXUN']]
    self.sina_roll = self.db[self.settings['MONGO_COLLECTION_SINA_ROLL']]
    self.tencent = self.db[self.settings['MONGO_COLLECTION_TENCENT']]
    self.tables = [self.wallstreet, self.hexun, self.sina_roll, self.tencent]
    self.corpus = Path("./corpus")
    self.model_name = "wv.model"
    self.model = None

    self.dim = dim

  def write_documents(self):
    for i, table in enumerate(self.tables):
      corpus_name = "corpus" + str(i) + ".txt"
      with open(self.corpus / corpus_name, 'w', encoding='utf-8') as f:
        for doc in table.find():
          title = None
          paras = None
          if 'title' in doc:
            title = doc['title']
          if 'para_content_text_and_images' in doc:
            paras = doc['para_content_text_and_images']
          if title:
            seg = jieba.cut(title, cut_all=False)
            # print("/ ".join(seg))
            f.write(" ".join(seg))
            f.write("\n")
          if paras:
            for para in paras:
              if isinstance(para, str): # some paras are still list
                if not '//' in para:
                  seg = jieba.cut(para, cut_all=False)
                  f.write(" ".join(seg))
                  f.write("\n")
              elif isinstance(para, list):
                for p in para:
                  if not '//' in p:
                    seg = jieba.cut(p, cut_all=False)
                    f.write(" ".join(seg))
                    f.write("\n")
          f.flush()

  def train_wv(self):
    sentences = Sentences(self.corpus)
    self.model = gensim.models.Word2Vec(sentences, size=self.dim, window=5, min_count=5)
    self.model.save(self.model_name)

  def getvec(self, word: str):
    if not self.model:
      self.model = gensim.models.Word2Vec.load(self.model_name)
    if word in self.model.wv:
      return self.model.wv[word]
    else:
      return [0.0] * self.dim








