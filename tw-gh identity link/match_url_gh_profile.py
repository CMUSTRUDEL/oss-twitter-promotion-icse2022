import pymongo
import pymysql
import progressbar
import tweepy
import stscraper as scraper

user_login_list = []  #


print("size of user_login_list", len(user_login_list))

p = progressbar.ProgressBar()
p.start()

# input your twitter keys to create a api connection
consumer_key = ""
consumer_secret = ""
api_key = ""
api_secret = ""

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(api_key, api_secret)
api = tweepy.API(auth, wait_on_rate_limit = True)

tw_screen2login = {}
for user_login_index in p(range(len(user_login_list))):
    user_login = user_login_list[user_login_index]
    try:
        tw_user_name_iterator = gh_api.v4("""
                    query ($login: String!) {
                        user(login: $login){
                            twitterUsername
                        }
                    }""", ('user', 'twitterUsername'), login = user_login)
        for tw_user_name in tw_user_name_iterator:
            if tw_user_name is not None:
                try:
                    user = api.get_user(screen_name = tw_user_name)
                except tweepy.error.TweepError:
                    break

                tw_screen2login[tw_user_name] = user_login
    except scraper.base.VCSError:
        continue
    except:
        continue

p.finish()

# tw_screen2login is the outcome dict 
