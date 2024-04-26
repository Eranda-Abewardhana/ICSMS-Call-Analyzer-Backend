import pymongo

get_next_operator_id_pipeline = [
    {
        '$sort': {
            'operator_id': pymongo.DESCENDING
        }
    },
    {
        '$limit': 1
    },
    {
        '$project': {
            '_id': 0,
            'operator_id': {
                '$add': ['$operator_id', 1]
            }
        }
    },
]


add_string_id = {
    '$addFields': {
        'id': {
            '$toString': '$_id'
        }
    }
}

join_analytic_records = {
    '$lookup': {
        'from': 'analytics',
        'localField': 'id',
        'foreignField': 'call_id',
        'as': 'result'
    }
}

remove_string_id = {
    '$unset': 'id'
}

convert_object_to_analytics_record_array = {
    '$unwind': {
        'path': '$result'
    }
}

add_boolean_category_fields = {
    '$addFields': {
        'is_neutral': {
            '$cond': {
                'if': {
                    '$eq': [
                        '$result.sentiment_category', 'Neutral'
                    ]
                },
                'then': 1,
                'else': 0
            }
        },
        'is_negative': {
            '$cond': {
                'if': {
                    '$eq': [
                        '$result.sentiment_category', 'Negative'
                    ]
                },
                'then': 1,
                'else': 0
            }
        },
        'is_positive': {
            '$cond': {
                'if': {
                    '$eq': [
                        '$result.sentiment_category', 'Positive'
                    ]
                },
                'then': 1,
                'else': 0
            }
        }
    }
}

group_records_by_sentiment_category = {
    '$group': {
        '_id': '$operator_id',
        'total_calls': {
            '$count': {}
        },
        'avg_handle_time': {
            '$avg': '$call_duration'
        },
        'positive_calls': {
            '$sum': '$is_positive'
        },
        'negative_calls': {
            '$sum': '$is_negative'
        },
        'neutral_calls': {
            '$sum': '$is_neutral'
        }
    }
}

project_data_without_id = {
    '$project': {
        '_id': 0
    }
}


def operator_analytics_pipeline(operator_id: int) -> list[dict]:
    pipeline = [
        {
            '$match': {
                'operator_id': operator_id
            }
        },
        add_string_id,
        join_analytic_records,
        remove_string_id,
        convert_object_to_analytics_record_array,
        add_boolean_category_fields,
        group_records_by_sentiment_category,
        project_data_without_id
    ]

    return pipeline
