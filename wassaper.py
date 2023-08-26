from collections import Counter
from wordcloud import WordCloud
from stop_words import get_stop_words
from PIL import Image
import numpy as np
import pandas as pd
import spacy as sp
import matplotlib.pyplot as plt
import random
from datetime import datetime

__author__ = "Pablo Coello Pulido"
__email__ = "pablo.coello@outlook.es"


class Wassaper:
    '''
    Wassaper.py: This class analyzes the plain text of a conversation
    generating, from it, graphics and images that detail the temporal
    frequency of the messages emitted by each individual belonging to the chat.
    '''
    def __init__(self, conf):
        self.conf_ = conf
        with open(self.conf_["path"], "r", encoding="utf8") as current_file:
            self.text_ = current_file.read().\
                replace("\n", " \n ").\
                replace("\r", "").\
                replace("\x96", "")

            self.split_messages()
            self.text_ = self.preprocess_data()
            self.matrix_ = self.create_matrix()
            self.matrix_ = self.postprocess_data()

        self.users_ = self.get_users_array()
        self.dictionary_text_ = self.get_dict_text_users()

    def split_messages(self):
        '''
        Separate words corresponding to different lines
        '''
        self.text_ = self.text_.split("\n")

    def del_emoji(self, String):
        '''
        Delete emojis from raw text. This function also deletes
        orthographic accents.
        '''
        return String.encode('ascii', 'ignore').decode('ascii')

    def preprocess_data(self):
        '''
        First step in data processing. Delete all raw text elements that are
        not text or multimedia messages sent by group members.

        Uncomment line 55 to delete emojis.
        '''
        toret = []
        for message in self.text_:
            # message = del_emoji(String=message)
            if len(message.split(":")) == 3 and\
                    message[1] != "[" and\
                    message[1] != "+":
                toret.append(message)
        return(toret)

    def create_matrix(self):
        '''
        Second step in data processing. Creation of base matrix composed of the
        variables date / time, user and message content.
        '''
        toret = []
        for message in self.text_:
            if len(message.split(":"))>2:
                event = []
                date = message.split("-")[0]
                date = date.strip(" ")
                name = message.split(":")[1]
                name = name[5:]
                content = message.split(":")[2]
                content = content.strip(" ")
                event.append(name)
                event.append(date)
                event.append(content)
                toret.append(event)
        toret = pd.DataFrame(toret, columns=["name", "date", "content"])
        return(toret)

    def postprocess_data(self):
        '''
        Third step in data processing. Delete all leftover
        elements from the base matrix.
        '''
        toret = []
        for index_row, row in self.matrix_.iterrows():
            try:
                date_format = datetime.strptime(row["date"], '%d/%m/%y, %H:%M')
                toret.append(row)
            except:
                pass
        toret = pd.DataFrame(toret)
        return(toret)

    def get_users_array(self):
        '''
        Returns array with user names.
        '''
        users = list(self.matrix_["name"].unique())
        users.append("Total")
        return(users)

    def get_user_matrix(self, name):
        '''
        Separate the base matrix into individual matrices per user.
        '''
        string = ""
        if name != "Total":
            toret = self.matrix_[self.matrix_["name"] == name]
        else:
            toret = self.matrix_
        return(toret)

    # Wordcloud functions
    def get_dict_text_users(self):
        '''
        Returns a dictionary variable with user key and value all
        the text written corresponding to that user.
        '''
        values = {}
        for user in self.users_:
            toret = self.get_user_matrix(name=user)
            values[user] = self.concatenate_text(matrix=toret)
        return(values)

    def concatenate_text(self, matrix):
        '''
        Concatenate string arrays.
        '''
        string = " ".join(list(matrix["content"]))
        return(string)

    def generate_wordcloud(self,
                           stopwords,
                           contour,
                           width,
                           maxwords,
                           background):
        '''
        Generate wordcloud object based on the selected aspect parameters.
        '''
        image = self.conf_["mask"]
        color = self.conf_["color"]
        if image == "Random":
            image = random.choice(["./masks/twitter_mask.png",
                                   "./masks/alicia_mask.png",
                                   "./masks/avestruz_mask.png",
                                   "./masks/gato_mask.png",
                                   "./masks/patada_mask.png",
                                   "./masks/pato_mask.png"])
        mask_image = np.array(Image.open(image))
        stop_words = get_stop_words(self.conf_["language"])
        newStopWords = stopwords
        stop_words.extend(newStopWords)
        if color == "Random":
            color = random.choice([
                'viridis', 'plasma', 'inferno', 'magma', 'cividis',
                'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                'hot', 'afmhot', 'gist_heat', 'copper',
                'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'])
        wc = WordCloud(background_color=background,
                       max_words=maxwords,
                       stopwords=stop_words,
                       mask=mask_image,
                       contour_width=width,
                       contour_color=contour,
                       colormap=color)
        return(wc)

    # Pie chart functions:
    def word_stats(self, word_counts):
        '''
        Returns frequency of each word.
        '''
        num_unique = len(word_counts)
        counts = word_counts.values()
        return (num_unique, counts)

    def count_words(self, user):
        '''
        Counts word frequency.
        '''
        skips = [".", ", ", ":", ";", "'", '"']
        for elem in skips:
            text = self.dictionary_text_[user].replace(elem, "")
        word_counts = Counter(text.split(" "))
        return word_counts

    def get_pie_chart(self):
        '''
        Returns Pie chart object.
        '''
        total_words = []
        for user in self.users_:
            word_counts = self.count_words(user)
            (num_unique, counts) = self.word_stats(word_counts)
            total_words.append(sum(counts))
        total_words.pop(-1)
        self.users_.pop()
        return(plt.pie(total_words,
                       labels=self.users_,
                       autopct='%1.1f%%',
                       colors={'b', 'g', 'r', 'c', 'm', 'y', 'k', 'w'}))

    def get_time_chart(self, time_period, user):
        '''
        Returns bar graphs with the absolute frequency of messages issued
        by user for a specified time frequency
        '''
        unit = []
        array = []
        toret = self.get_user_matrix(name=user)
        for message in toret['date']:
            message_date = datetime.strptime(message, '%d/%m/%y, %H:%M')
            if time_period == "day":
                unit.append(message_date.day)
            elif time_period == "month":
                unit.append(message_date.month)
            elif time_period == "year":
                unit.append(message_date.year)
            elif time_period == "progression":
                unit.append(message_date.date())
            else:
                unit.append(message_date.hour)
        if time_period == "day" or\
                time_period == "month" or\
                time_period == "year" or\
                time_period == "progression":
            index = np.unique(unit)
            unit = np.array(unit)
            for date in index:
                array.append(len(np.where(unit == date)[0]))
            plt.bar(index, array)
            plt.title('Messages per ' + time_period + " " + user)
            plt.xticks(rotation=45)
            return(plt.show())
        else:
            labels = list(range(0, 23))
            for value in labels:
                array.append(unit.count(value))
            plt.bar(labels, array)
            plt.title('Hourly messages of ' + user)
            plt.xticks(labels, rotation=45)
            return(plt.show())


if __name__ == '__main__':
    conf = dict(path="PATH TO YOUR .txt FILE",
                mask="PATH TO THE MASK IMAGE FOR WORDCLOUD",
                color="Random",
                language="spanish",
                chart_periods=["hour", "day", "month", "year", "progression"])
    was = Wassaper(conf)

    # Wordcloud
    users_ = was.get_users_array()
    dictionary_text_ = was.get_dict_text_users()

    for user in users_:
        wc = was.generate_wordcloud(stopwords=["Multimedia", "omitido"],
                                    contour='black', width=0,
                                    maxwords=2000, background="white")
        wc.generate(was.dictionary_text_[user])
        plt.imshow(wc, interpolation='bilinear')
        plt.axis("off")
        plt.show()
        print(user)
        # wc.to_file("./output/"+user+".png")

    # Pie chart
    chart = was.get_pie_chart()
    plt.show()
    # plt.savefig('./output/chart.png')
    plt.close()

    # time chart
    users_ = was.get_users_array()
    for chart in conf["chart_periods"]:
        for user in users_:
            was.get_time_chart(time_period=chart, user=user)
            # plt.savefig('./output/chart'+user+chart+'.png')
            plt.close()