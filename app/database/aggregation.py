import pymongo

get_topics_pipeline = [
    {
        '$project': {
            'topics': 1,
            '_id': 0
        }
    }
]

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


def call_statistics_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
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
                'total_duration_in_sec': 1,
                'avg_score': 1
            }
        }
    ]


def get_all_keywords_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        {
            '$project': {
                'keywords': 1,
                '_id': 0
            }
        }, {
            '$group': {
                '_id': None,
                'keywords': {
                    '$push': '$keywords'
                }
            }
        }, {
            '$project': {
                '_id': 0,
                'keywords': {
                    '$reduce': {
                        'input': '$keywords',
                        'initialValue': [],
                        'in': {
                            '$concatArrays': [
                                '$$value', '$$this'
                            ]
                        }
                    }
                }
            }
        }
    ]


def sentiment_over_time_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$call_date'
                    }
                },
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
                    },
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
                'date': '$_id',
                'positive': 1,
                'negative': 1,
                'neutral': 1
            }
        }
    ]


def sentiment_percentages_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
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


def operator_calls_over_time_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        add_string_id,
        join_analytic_records,
        remove_string_id,
        convert_object_to_analytics_record_array,
        add_boolean_category_fields,
        group_and_count_sentiment_category
    ]


operator_calls_andAvg_call_time_pipeline = [
    add_string_id,
    join_analytic_records,
    remove_string_id,
    convert_object_to_analytics_record_array,
]


def operator_analytics_pipelines(operator_id: int, end, start) -> tuple[list[dict], list[dict]]:
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

    calls_in_last_day = [
        {
            '$match': {
                'operator_id': operator_id,
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        }, {
            '$count': 'total_calls'
        }
    ]

    return pipeline, calls_in_last_day


def operator_rating_pipeline(limit: int, start, end) -> list[dict]:
    pipeline = [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        {
            '$lookup': {
                'from': 'operators',
                'localField': 'operator_id',
                'foreignField': 'operator_id',
                'as': 'result'
            }
        }, {
            '$unwind': {
                'path': '$result'
            }
        }, {
            '$group': {
                '_id': '$operator_id',
                'total': {
                    '$count': {}
                },
                'avg_duration': {
                    '$avg': '$call_duration'
                },
                'name': {
                    '$push': '$result.name'
                }
            }
        }, {
            '$project': {
                '_id': 1,
                'total': 1,
                'avg_duration': {
                    '$round': [
                        '$avg_duration', 2
                    ]
                },
                'name': {
                    '$arrayElemAt': [
                        '$name', 0
                    ]
                }
            }
        }, {
            '$sort': {
                'total': -1,
                'avg_duration': 1
            }
        }, {
            '$limit': 3
        }
    ]

    return pipeline


def get_topics_distribution_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        {
            '$project': {
                'topics': 1,
                '_id': 0
            }
        }, {
            '$group': {
                '_id': None,
                'topics': {
                    '$push': '$topics'
                }
            }
        }, {
            '$project': {
                '_id': 0,
                'topics': {
                    '$reduce': {
                        'input': '$topics',
                        'initialValue': [],
                        'in': {
                            '$concatArrays': [
                                '$$value', '$$this'
                            ]
                        }
                    }
                }
            }
        }
    ]


all_operator_sentiment_pipeline = [
    add_string_id,
    join_analytic_records,
    remove_string_id,
    convert_object_to_analytics_record_array,
    add_boolean_category_fields,
    {
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
]


def get_overall_avg_sentiment_score_pipeline(start, end):
    return [
        {
            '$match': {
                'call_date': {
                    '$gte': start,
                    '$lte': end
                }
            }
        },
        {
            '$group': {
                '_id': None,
                'avg_score': {
                    '$avg': '$sentiment_score'
                }
            }
        },
        {
            '$project': {
                '_id': 0,
                'avg_score': 1
            }
        }
    ]
