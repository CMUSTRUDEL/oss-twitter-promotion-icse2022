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
from compare_tw_photos import get_img_similarity

'''
Required input:
    A mysql GHTorrent dump with the username and password to access it
    A mongo collection which stores the twitter user information (cralwed by twitter API), which are candidates of possible gh-tw account linking 
    A directory which stores the profile image of github users on GHTorrent
    A directory which stores the profile image of candidate twitter users 
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
img_directory_gh = ""
img_directory_tw = ""

jarowinkler = JaroWinkler()
name_sim_threshold = 0.9 # this threshold is selected based on manual evaluation
img_sim_threshold = 0.75 # this threshold is selected based on manual evaluation
name_sim_distance = 2

db = pymysql.connect('localhost', MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB_NAME)
cursor = db.cursor() 

def convert_string(string):
    return string.lower().replace('-', '').replace('_','').replace(' ','')

def check_gh_img_validity(img):
    if img.shape[0] == 420:
        empty_pix_count = np.sum((img[:, :] == [240,240,240]).all(axis = 2))
        if empty_pix_count > 0.1 * 420 * 420:
            return False
        else:
            return True

    return True

def get_img_directory(pre_fix, img_name):
    if os.path.exists(''.join([pre_fix, img_name, '.jpg'])):
        img_dire = ''.join([pre_fix, img_name, '.jpg'])
    elif os.path.exists(''.join([pre_fix, img_name, '.png'])):
        img_dire = ''.join([pre_fix, img_name, '.png'])
    elif os.path.exists(''.join([pre_fix, img_name, '.jpeg'])):
        img_dire = ''.join([pre_fix, img_name, '.jpeg'])
    else:
        img_dire = None

    return img_dire


def check_name_sim(candidate_name_dict, target_name, candidate_cvt_func, tname_out, tname2cname_set):

    target_name_1cha = target_name[0]
    target_name_fcha = target_name[-1]
    target_name_len = len(target_name)
    if target_name_1cha in candidate_name_dict and target_name_fcha in candidate_name_dict[target_name_1cha]:
        for len_checked in range(target_name_len - name_sim_distance, target_name_len + name_sim_distance + 1):
            if len_checked in candidate_name_dict[target_name_1cha][target_name_fcha]:
                for candidate_name in candidate_name_dict[target_name_1cha][target_name_fcha][len_checked]:
                    if candidate_name not in tname2cname_set[tname_out]:
                        cname_converted = candidate_cvt_func(candidate_name)
                        if jarowinkler.similarity(target_name, cname_converted) >= name_sim_threshold:
                            # name matched
                            tname2cname_set[tname_out].add(candidate_name)





client = pymongo.MongoClient(host='localhost', username = MONGO_USER, 
    password = MONGO_PASSWORD, authSource = MONGO_DB_NAME, port=27017)
db = client.twitter

tw_sname_2tw_uid_str = {}
tw_sname_2cvt_tw_dname = {}


for user in db[mongo_collection_name_twitter_candidate].find():
    if not user['default_profile_image']:
        tw_uid_str = str(user['id_str'])

        img_url = user['profile_image_url'].replace('_normal.', '.')
        target = img_directory_tw + '%s.jpg' % tw_uid_str
        if os.path.exists(target):
            assert user['screen_name'] is not None
            assert user['name'] is not None
            if len(convert_string(user['screen_name'])) == 0:
                continue
            tw_sname_2tw_uid_str[user['screen_name']] = tw_uid_str
            tw_sname_2cvt_tw_dname[user['screen_name']] = convert_string(user['name'])
print('size of potential valid twitter users', len(tw_sname_2tw_uid_str))


login_with_img_set = set()
for jpg_name in os.listdir(img_directory_gh):
    name, postfix = jpg_name.split('.')
    login_with_img_set.add(name)
    assert name is not None

login2cvt_gh_dname = {}

login_1cha_fcha_len = defaultdict(dict)
gh_dname_1cha_fcha_len = defaultdict(dict)

for login in login_with_img_set:
    converted_login = convert_string(login)
    if len(converted_login) == 0:
        continue
    cursor.execute('select id, name from users_private where login = "%s"' %(login))
    res = cursor.fetchall()
    if len(res) != 1:
        continue
    id, gh_dname = res[0]

    if gh_dname is not None:
        gh_dname = convert_string(gh_dname)
        if len(gh_dname) > 0:
            gh_dname_1cha = gh_dname[0]
            gh_dname_fcha = gh_dname[-1]
            gh_dname_len = len(gh_dname)
            gh_dname_1cha_fcha_len[gh_dname_1cha].setdefault(gh_dname_fcha, defaultdict(list))
            gh_dname_1cha_fcha_len[gh_dname_1cha][gh_dname_fcha][gh_dname_len].append(login)

    login2cvt_gh_dname[login] = gh_dname

    login_1cha = converted_login[0]
    login_fcha = converted_login[-1]
    login_len = len(converted_login)


    login_1cha_fcha_len[login_1cha].setdefault(login_fcha, defaultdict(list))
    login_1cha_fcha_len[login_1cha][login_fcha][login_len].append(login)
    
valid_user_login_list = list(login_with_img_set & set(login2cvt_gh_dname.keys()))
valid_screen_name_list = list(tw_sname_2tw_uid_str.keys())
print('size of potential valid github users', len(valid_user_login_list))

data_size = len(valid_screen_name_list)
total_process_count = 12
batch_size = int(math.ceil(data_size * 1.0 / total_process_count))
split_data = [[] for _ in range(total_process_count)]
for data_batch_index in range(total_process_count):
    for data_index in range(batch_size*data_batch_index, batch_size*(data_batch_index + 1)):
        if data_index < data_size:
            split_data[data_batch_index].append(valid_screen_name_list[data_index])

data_input = [[batch_index, split_data[batch_index]] for batch_index in range(total_process_count)]

# the package is from https://github.com/luozhouyang/python-string-similarity#jaro-winkler

def get_cvt_gh_name(login):
    return login2cvt_gh_dname[login]

def get_linked_user(data_input):
    process_index = data_input[0]
    tw_sname_list = data_input[1]
    client = pymongo.MongoClient(host='localhost', username = MONGO_USER, 
        password = MONGO_PASSWORD, authSource = MONGO_DB_NAME, port=27017)
    db = client.twitter
    range_ = range(len(tw_sname_list))
    if process_index == 0:
        p = progressbar.ProgressBar()
        p.start()
        range_ = p(range_)

    sname2login_set = defaultdict(set)
    
    for sname_index in range_:
        tw_sname = tw_sname_list[sname_index]
        sname_converted = convert_string(tw_sname)
        tw_dname = tw_sname_2cvt_tw_dname[tw_sname]

        check_name_sim(login_1cha_fcha_len, sname_converted, convert_string, tw_sname, sname2login_set)
        # find login similar to twitter screen name
        check_name_sim(gh_dname_1cha_fcha_len, sname_converted, get_cvt_gh_name, tw_sname, sname2login_set)
        # find github display name similar to twitter screen name

        if len(tw_dname) > 0:
            check_name_sim(login_1cha_fcha_len, tw_dname, convert_string, tw_sname, sname2login_set)
            # find login similar to twitter display name
            check_name_sim(gh_dname_1cha_fcha_len, tw_dname, get_cvt_gh_name, tw_sname, sname2login_set)
            # find github display name similar to twitter display name
    

    sname_list = list(sname2login_set.keys())
    sname2login_list = {}
    for sname in sname2login_set:
        sname2login_list[sname] = list(sname2login_set[sname])

    range_ = range(len(sname_list))
    if process_index == 0:
        print("get linked user with names finished")
        p.finish()
        p.start()
        range_ = p(range_)



    client = pymongo.MongoClient(host='localhost', username = MONGO_USER, 
        password = MONGO_PASSWORD, authSource = MONGO_DB_NAME, port=27017)
    db = client.twitter

    # compare image
    
    for sname_index in range_:
        sname = sname_list[sname_index]
        highest_sim = img_sim_threshold
        identified_login = None
        tweet_user_id = tw_sname_2tw_uid_str[sname]
        tw_img_dire = img_directory_tw + '%s.jpg' % tweet_user_id
        for login_to_compare in sname2login_list[sname]:
            gh_img_dire = get_img_directory(img_directory_gh, login_to_compare)
            if gh_img_dire is not None:
                gh_img = cv2.imread(gh_img_dire)
                if gh_img is None:
                    continue
                tw_img = cv2.imread(tw_img_dire)
                if tw_img is None:
                    continue
                img_similarity = get_img_similarity(gh_img, tw_img)
                if img_similarity > highest_sim:
                    identified_login = login_to_compare
                    highest_sim = img_similarity


        if identified_login is not None:
            db[mongo_collection_linkage_result].insert_one({'tweet_user_id_str': str(tweet_user_id),
                                                 'login': identified_login,
                                                 'screen_name': sname})
        
    return None
pool = multiprocessing.Pool(total_process_count) 

results = pool.map_async(get_linked_user, data_input).get()
