import pymongo

get_next_operator_id_pipeline = [
    {"$sort": {"operator_id": pymongo.DESCENDING}},
    {"$limit": 1},
    {"$project": {"_id": 0, "operator_id": 1}},
]
