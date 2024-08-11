import datetime as dt

import pymongo

client = pymongo.MongoClient('localhost', 27017)
db = client['tehnika_bot_db']
vehicles = db['vehicles']


pipeline = [
    {'$group': {'_id': f'$vehicle', 'count': {'$sum': 1}}},
    {'$sort': { 'count': -1}}
]
qs = vehicles.aggregate(pipeline)
# print(list(qs))

res = [v['_id'] for v in list(qs)]
print(res)
