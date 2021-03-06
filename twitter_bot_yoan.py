# -*- coding: utf-8 -*-
'''
svakulenko
31 March 2019

Pass tweets through the classifier and retweet
Loading the job offers classification model trained by Yoan Bachev
'''
import pickle

from tweepy.streaming import StreamListener
from tweepy import Stream, API, OAuthHandler, Cursor

from settings import *
from twitter_settings import *

from keras.preprocessing.sequence import pad_sequences


THRESHOLD = 0.88
MAX_NB_WORDS = 5000 # consider up to x most occuring words in dataset


class TweetClassifier(StreamListener):
    '''
    Overrides Tweepy class for Twitter Streaming API
    '''

    def __init__(self, model_path=MODEL_PATH, model_name='model.sav'):
        self.load_pretrained_model(model_path, model_name)
        # set up Twitter connection
        self.auth_handler = OAuthHandler(APP_KEY, APP_SECRET)
        self.auth_handler.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        self.api = API(self.auth_handler)

    def load_pretrained_model(self, model_path, model_name):
        # Load model and dictionaries
        print("Loading pre-trained model...")
        with open('./model/tokenizer.pickle', 'rb') as handle:
            self.tokenizer = pickle.load(handle)
        self.model = pickle.load(open('%s/%s' % (model_path, model_name), 'rb'))

    def on_status(self, status):
        # ignore retweets
        if not hasattr(status,'retweeted_status') and status.in_reply_to_status_id == None:
            tweet_text = status.text
            tweet_id = status.id
            # print(tweet_text)

            # preprocess
            sequences= self.tokenizer.texts_to_sequences([tweet_text])
            dat = pad_sequences(sequences, maxlen=1000)

            # classify
            prediction = self.model.predict(dat, batch_size=64)[0,1]
            # print (tweet_text)
            # print (prediction)
            
            if prediction > THRESHOLD:
                print (tweet_text)
                print (prediction)
                # retweet
                self.api.update_status(status='https://twitter.com/%s/status/%s' % (status.user.screen_name, tweet_id))
            # retweet
            # twitter_client.retweet(id=tweet_id)

    def on_error(self, status_code):
        print (status_code, 'error code')


def stream_tweets():
    '''
    Connect to Twitter API and fetch relevant tweets from the stream
    '''
    # get users from list
    listener = TweetClassifier()
    print("Collecting list members")
    members = [member.id_str for member in Cursor(listener.api.list_members, MY_NAME, LIST).items()]
    print("Done. Collected %d list members"%len(members))
    # start streaming
    while True:
        try:
            stream = Stream(listener.auth_handler, listener)
            print ('Listening...')
            # stream.filter(track=['hiring', 'job', 'career'], languages=['en'])
            stream.filter(follow=members)
            # stream.sample(languages=['en'])
        except Exception as e:
            # reconnect on exceptions
            print (e)
            continue


def test_classifier():
    classifier = TweetClassifier()


if __name__ == '__main__':
    stream_tweets()
