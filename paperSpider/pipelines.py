# Define your item pipelines here
# Cache buffer
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

import os
import pickle
from paperSpider import settings
from scrapy import signals
from datetime import date

import openai

class PaperspiderPipeline:
    isNew = False
    CACHE = settings.PAPERSPIDER_CACHE_LOCAL
    OUT_FILE_PATH = settings.PAPERSPIDER_OUT_FILE_PATH
    OUT_FILE_PATH_MD = settings.PAPERSPIDER_OUT_FILE_PATH_MD
    API_KEY = settings.OPENAI_API
    TITLE_SET = set()
    CHATGPT_PROMPT = "I want you to act as a scientist. I will provide you the abstract section of a paper. You should use your computer science, biology knowledge to summarize it in Chinese. I want you to only reply with bullet points."

    def open_spider(self, spider):
        #                    first initialize cache queue                    #
        try:
            if os.path.getsize(self.CACHE) > 0:
                self.papersSet = pickle.load(open(self.CACHE, 'rb'))
            else:
                self.papersSet = set()
        except:
            self.papersSet = set()


    def close_spider(self, spider):
        #                    finally close the cache queue                    #
        for item in self.papersSet:
            if item['title'] not in self.TITLE_SET:
                self.papersSet.discard(item)
                self.isNew = True

        if self.isNew:
            print("is new")
            pickle.dump(self.papersSet, open(self.CACHE, 'wb'),
                        pickle.HIGHEST_PROTOCOL)
            self._export_papers()


    def process_item(self, item, spider):
        self.TITLE_SET.add(item['title'])
        if item['title'] not in [p['title'] for p in self.papersSet]:
            messages_prompt = [{"role": "system",
                                "content": self.CHATGPT_PROMPT}]
            item["chatGPT"] = \
                self._summarize_chatGPT(messages_prompt +
                    [{"role": "user", "content": item["content"]}])
            self.papersSet.add(item)
            self.isNew = True

        return item

    def _summarize_chatGPT(self, messages_to):
        openai.api_key = self.API_KEY
        completion = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages_to)

        return completion['choices'][0]['message']['content']

    def _export_papers(self):
        print("in export paper")
        with open(self.OUT_FILE_PATH, "w") as outFile:
            for item in self.papersSet:
                tempPaper = "标题：{0}\n{1} | {2}\n{3}\n作者：{4}\n\nchatGPT 解析：\n{5}".format(
                    item['title'],
                    item['journal'],
                    item['status'],
                    item['url'],
                    item['authors'],
                    item['chatGPT'])
                outFile.write(tempPaper)
                outFile.write("\n\n-------------\n\n")
        with open(self.OUT_FILE_PATH_MD, "w") as outFile:
            outFile.write("# chatGPT 解析文献 {} \n".format(date.today()))
            for item in self.papersSet:
                tempPaper = "## {0}\n - {1} | {2}\n - [{3}]({3})\n - 作者：{4}\n\n - chatGPT 解析：\n{5}".format(
                    item['title'],
                    item['journal'],
                    item['status'],
                    item['url'],
                    item['authors'],
                    item['chatGPT'])
                outFile.write(tempPaper)
                outFile.write("\n\n-------------\n\n")
        pass
