import pymongo

# Create the client
client = pymongo.MongoClient('localhost', 27017)
db = client['otipb_db']
reports = db['reports']
