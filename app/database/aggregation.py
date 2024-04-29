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

call_statistics_pipeline = [
    {
        '$group': {
            '_id': None,
            'total_calls': {
                '$count': {}
            },
            'total_duration_in_sec': {
                '$sum': '$call_duration'
            },
            'avg_call_time_in_sec': {
                '$avg': '$call_duration'
            }
        }
    }, {
        '$project': {
            '_id': 0,
            'avg_call_time_in_sec': {
                '$ceil': '$avg_call_time_in_sec'
            },
            'total_calls': 1,
            'total_duration_in_sec': 1
        }
    }
]

sentiment_percentages_pipeline = [
    {
        '$group': {
            '_id': None,
            'positive': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$sentiment_category', 'Positive'
                            ]
                        }, 1, 0
                    ]
                }
            },
            'negative': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$sentiment_category', 'Negative'
                            ]
                        }, 1, 0
                    ]
                }
            },
            'neutral': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$sentiment_category', 'Neutral'
                            ]
                        }, 1, 0
                    ]
                }
            }
        }
    }, {
        '$project': {
            '_id': 0,
            'positive': 1,
            'negative': 1,
            'neutral': 1
        }
    }
]

group_and_count_sentiment_category = {
    '$group': {
        '_id': '$operator_id',
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

operator_calls_over_time_pipeline = [
    add_string_id,
    join_analytic_records,
    remove_string_id,
    convert_object_to_analytics_record_array,
    add_boolean_category_fields,
    group_and_count_sentiment_category
]


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
