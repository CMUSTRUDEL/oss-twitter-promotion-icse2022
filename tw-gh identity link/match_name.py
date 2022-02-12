import pymongo
import pymysql
import progressbar
import math
import multiprocessing
import os
import json
import numpy as np
import cv2
import pandas as pd
from collections import defaultdict, OrderedDict
from strsimpy.jaro_winkler import JaroWinkler

jarowinkler = JaroWinkler()
name_sim_threshold = 0.9 # this threshold is selected based on manual evaluation

def parse_name(string):
    return string.lower().replace('-', '').replace('_','').replace(' ','')


'''
Required input:
    A mysql GHTorrent dump with the username and password to access it
    A mongo collection which stores the twitter user information (cralwed by twitter API), which are candidates of possible gh-tw account linking 
'''

'''
The script will insert the identified tw-gh link to another mongo collection

'''


# access to mysql database
MYSQL_USER = ""
MYSQL_PASSWORD = ""
MYSQL_DB_NAME = ""
# access to mongo database
MONGO_USER = ""
MONGO_PASSWORD = ""
MONGO_DB_NAME = ""

mongo_collection_name_twitter_candidate = ''
mongo_collection_linkage_result = ''

db = pymysql.connect('localhost', MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB_NAME)
cursor = db.cursor()

client = pymongo.MongoClient(host='localhost', username = MONGO_USER, 
    password = MONGO_PASSWORD, authSource = MONGO_DB_NAME, port=27017)
db = client.twitter

user_id_str2parsed_dname = {}
user_id_str2parsed_sname = {}

user_id_str2original_sname = {}
for user in db[mongo_collection_name_twitter_candidate].find():
    user_id_str = str(user['id_str'])
    parsed_dname = parse_name(user['name'])
    parsed_sname = parse_name(user['screen_name'])
    
    user_id_str2parsed_dname[user_id_str] = parsed_dname
    user_id_str2parsed_sname[user_id_str] = parsed_sname
    user_id_str2original_sname[user_id_str] = user['screen_name']
print("size of twitter user", len(user_id_str2parsed_dname))



cursor.execute('select login, name from users_private where name is not null')
valid_login2parsed_dname = {}
valid_login2parsed_login = {}

for row in cursor.fetchall():
    login, name = row
    if login in identified_login_set:
        continue
    if len(login) == 8 and login.isupper() == True:
        # fake user
        continue

    valid_login2parsed_dname[login] = parse_name(name)
    valid_login2parsed_login[login] = parse_name(login)


valid_login_list = list(valid_login2parsed_dname.keys())
print('size of github user', len(valid_login2parsed_dname))

valid_tw_id_str_list = list(user_id_str2parsed_dname.keys())

data_size = len(valid_tw_id_str_list)
total_process_count = 12
batch_size = int(math.ceil(data_size * 1.0 / total_process_count))
split_data = [[] for _ in range(total_process_count)]
for data_batch_index in range(total_process_count):
    for data_index in range(batch_size*data_batch_index, batch_size*(data_batch_index + 1)):
        if data_index < data_size:
            split_data[data_batch_index].append(valid_tw_id_str_list[data_index])

data_input = [[batch_index, split_data[batch_index]] for batch_index in range(total_process_count)]

def check_identity_eqal(name_group1_1, name_group1_2,
                    name_group2_1, name_group2_2):

    if name_group1_1 == name_group2_1 or \
        name_group1_1 == name_group2_2:
        pass
    else:
        return False


    if name_group1_2 == name_group2_1 or \
        name_group1_2 == name_group2_2:
        pass
    else:
        return False


    if name_group2_1 == name_group1_1 or \
        name_group2_1 == name_group1_2:
        pass
    else:
        return False

    if name_group2_2 == name_group1_1 or \
        name_group2_2 == name_group1_2:
        pass
    else:
        return False



    if name_group1_1 == name_group2_1 or \
        name_group1_2 == name_group2_2:
        pass
    else:
        return False


    if name_group1_1 == name_group2_2 or \
        name_group1_2 == name_group2_1:
        pass
    else:
        return False

    return True



def check_identity_jksim(name_group1_1, name_group1_2,
                    name_group2_1, name_group2_2):

    if (jarowinkler.similarity(name_group1_1, name_group2_1) >= name_sim_threshold) or \
        (jarowinkler.similarity(name_group1_1, name_group2_2) >= name_sim_threshold):
        pass
    else:
        return False


    if (jarowinkler.similarity(name_group1_2, name_group2_1) >= name_sim_threshold) or \
        (jarowinkler.similarity(name_group1_2, name_group2_2) >= name_sim_threshold):
        pass
    else:
        return False

    return True

def get_linked_user(data_input):
    process_index = data_input[0]
    tw_id_str_list = data_input[1]
    client = pymongo.MongoClient(host='localhost', username = MONGO_USER, 
        password = MONGO_PASSWORD, authSource = MONGO_DB_NAME, port=27017)
    db = client.twitter
    range_ = range(len(tw_id_str_list))
    if process_index == 0:
        p = progressbar.ProgressBar()
        p.start()
        range_ = p(range_)

    for tw_id_index in range_:
        tw_id_str = tw_id_str_list[tw_id_index]
        tw_dname = user_id_str2parsed_dname[tw_id_str]
        tw_sname = user_id_str2parsed_sname[tw_id_str]

        for login in valid_login2parsed_dname:
            if check_identity_eqal(tw_dname, tw_sname, valid_login2parsed_dname[login], valid_login2parsed_login[login]) == True:
                db[mongo_collection_linkage_result].insert_one({'tweet_user_id_str': str(tw_id_str),
                                                     'login': login,
                                                     'screen_name': user_id_str2original_sname[str(tw_id_str)]})

    return None
pool = multiprocessing.Pool(total_process_count) 

results = pool.map_async(get_linked_user, data_input).get()