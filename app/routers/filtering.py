from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from app.database.db import DatabaseConnector
from app.models.action_result import ActionResult
from datetime import datetime
from app.models.call_filtering import CallFilter

filter_router = APIRouter()
db = DatabaseConnector("call")
analytics_db = DatabaseConnector("analytics")


@filter_router.post("/filter-calls", response_model=ActionResult)
async def read_items(call_filtering: CallFilter):
    action_result = ActionResult(status=True)
    filter_query_analytics = {}
    filter_query_calls = {}
    # Define the parameters as a list
    params_analytics = [call_filtering.keyword, call_filtering.sentiment_category]
    params_calls = [call_filtering.start_date, call_filtering.end_date, call_filtering.duration]
    # Loop through the parameters and add non-None ones to the filter_query dictionary
    for param_name, param_value in zip(["keyword", "sentiment_category"], params_analytics):
        if param_value is not None:
            filter_query_analytics[param_name] = param_value
    for param_name, param_value in zip(["start_date", "end_date", "duration"], params_calls):
        if param_value is not None:
            filter_query_calls[param_name] = param_value

    # Return the filter_query dictionary
    result_analytics = await analytics_db.find_entities(filter_query_analytics)
    result_calls = await db.find_entities(filter_query_calls)

    # Check if params_analytics is empty
    if not params_analytics:
        common_matches_list = result_calls
    # Check if params_calls is empty
    elif not params_calls:
        common_matches_list = result_analytics
    else:
        matching_ids = [call_record.get("id") for call_record in result_calls]
        matching_call_ids = [analytics_record.get("call_id") for analytics_record in result_analytics]
        common_matches = set(matching_ids) & set(matching_call_ids)
        common_matches_list = list(common_matches)

        merged_list = []

        # Iterate through each ID in common_matches_list
        for common_id in common_matches_list:
            # Find the call record corresponding to the current ID in result_calls
            call_record = next((record for record in result_calls if record.get("id") == common_id), None)
            # Find the analytics record corresponding to the current ID in result_analytics
            analytics_record = next((record for record in result_analytics if record.get("call_id") == common_id), None)

            # Check if both call_record and analytics_record are not None
            if call_record and analytics_record:
                # Merge call_record and analytics_record based on the common ID
                merged_record = {**call_record, **analytics_record}
                merged_list.append(merged_record)

        # Return the merged list
        return merged_list
