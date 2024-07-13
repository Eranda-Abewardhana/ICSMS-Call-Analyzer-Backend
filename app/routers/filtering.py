from fastapi import APIRouter
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from datetime import datetime
from app.models.call_filtering import CallFilter

filter_router = APIRouter()
db = DatabaseConnector("calls")
analytics_db = DatabaseConnector("analytics")


@filter_router.post("/filter-calls", response_model=ActionResult)
async def read_items(call_filtering: CallFilter):
    action_result = ActionResult(status=True)
    filter_query_analytics = {}
    filter_query_calls = {}
    # Define the parameters as a list
    params_analytics = [call_filtering.keywords, call_filtering.sentiment_category, call_filtering.topics]
    params_calls = [call_filtering.start_date, call_filtering.end_date, call_filtering.duration]
    # Loop through the parameters and add non-None ones to the filter_query dictionary
    for param_name, param_value in zip(["keywords", "sentiment_category", "topics"], params_analytics):
        if param_value not in ("", []):
            # Constructing regex pattern to match any substring containing each keyword
            regex_pattern = f'({"|".join(param_value)})'
            # Using the constructed regex pattern in the query
            filter_query_analytics[param_name] = {"$regex": regex_pattern}
            # filter_query_analytics[param_name] = param_value
    for param_name, param_value in zip(["start_date", "end_date", "call_duration"], params_calls):
        if param_value not in ("", []):
            if param_name in ["start_date", "end_date"]:
                if "call_date" not in filter_query_calls:
                    filter_query_calls["call_date"] = {}
                if param_name == "start_date" and param_value != "":
                    filter_query_calls["call_date"]["$gte"] = datetime.strptime(param_value, '%Y-%m-%dT%H:%M:%S.%fZ')
                elif param_name == "end_date" and param_value != "":
                    filter_query_calls["call_date"]["$lte"] = datetime.strptime(param_value, '%Y-%m-%dT%H:%M:%S.%fZ')
            elif param_name == "call_duration":
                if param_value != 0:

                    min_duration = max(param_value - 60, 0)
                    max_duration = min(param_value + 60, 3600)
                    filter_query_calls["call_duration"] = {"$gte": min_duration, "$lte": max_duration}

    # Return the filter_query dictionary
    result_analytics = await analytics_db.find_entities_async(filter_query_analytics)
    result_calls = await db.find_entities_async(filter_query_calls)

    merged_list = []

    # Extract IDs and find common matches
    matching_calls_ids = [call_record["_id"]["$oid"] for call_record in result_calls.data if
                          "_id" in call_record and "$oid" in call_record["_id"]]
    matching_analytics_ids = [analytics_record["call_id"] for analytics_record in result_analytics.data if
                              "call_id" in analytics_record]

    common_matches = set(matching_analytics_ids) | set(matching_calls_ids)
    common_matches_list = list(common_matches)
    for common_id in common_matches_list:
        # Find the call record corresponding to the current ID in result_calls
        call_record = next((record for record in result_calls.data if record.get("_id").get("$oid") == common_id), None)
        # Find the analytics record corresponding to the current ID in result_analytics
        analytics_record = next(
            (record for record in result_analytics.data if record.get("call_id") == common_id),
            None)
        # Check if both call_record and analytics_record are not None
        if call_record and analytics_record:
            # Merge call_record and analytics_record based on the common ID
            merged_record = {**call_record, **analytics_record}
            merged_list.append(merged_record)
# Return the merged list
    return ActionResult(data=merged_list)
