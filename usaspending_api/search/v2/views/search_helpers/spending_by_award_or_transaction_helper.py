import ast
import logging
from rest_framework.response import Response

from usaspending_api.awards.models_matviews import UniversalAwardView
from usaspending_api.awards.v2.filters.matview_filters import matview_search_filter
from usaspending_api.awards.v2.lookups.lookups import contract_type_mapping
from usaspending_api.awards.v2.lookups.lookups import loan_type_mapping
from usaspending_api.awards.v2.lookups.lookups import non_loan_assistance_type_mapping
from usaspending_api.awards.v2.lookups.matview_lookups import award_contracts_mapping
from usaspending_api.awards.v2.lookups.matview_lookups import loan_award_mapping
from usaspending_api.awards.v2.lookups.matview_lookups import non_loan_assistance_award_mapping
from usaspending_api.common.exceptions import InvalidParameterException

logger = logging.getLogger(__name__)


class SpendingByAwardOrTransaction:
    def spending_by_award_or_transaction(self, request, award_or_transaction):
        """Return all budget function/subfunction titles matching the provided search text"""
        json_request = request.data
        fields = json_request.get("fields", None)
        filters = json_request.get("filters", None)
        order = json_request.get("order", "asc")
        limit = json_request.get("limit", 10)
        page = json_request.get("page", 1)

        lower_limit = (page - 1) * limit
        upper_limit = page * limit

        # input validation
        if fields is None:
            raise InvalidParameterException("Missing one or more required request parameters: fields")
        elif len(fields) == 0:
            raise InvalidParameterException("Please provide a field in the fields request parameter.")
        if filters is None:
            raise InvalidParameterException("Missing one or more required request parameters: filters")
        if "award_type_codes" not in filters:
            raise InvalidParameterException(
                "Missing one or more required request parameters: filters['award_type_codes']")
        if order not in ["asc", "desc"]:
            raise InvalidParameterException("Invalid value for order: {}".format(order))

        sort = json_request.get("sort", fields[0])
        if sort not in fields:
            raise InvalidParameterException("Sort value not found in fields: {}".format(sort))

        # build sql query filters
        queryset = matview_search_filter(filters, UniversalAwardView).values()

        values = {'award_id', 'piid', 'fain', 'uri', 'type'}  # always get at least these columns
        for field in fields:
            if award_contracts_mapping.get(field):
                values.add(award_contracts_mapping.get(field))
            if loan_award_mapping.get(field):
                values.add(loan_award_mapping.get(field))
            if non_loan_assistance_award_mapping.get(field):
                values.add(non_loan_assistance_award_mapping.get(field))

        # Modify queryset to be ordered if we specify "sort" in the request
        if sort and "no intersection" not in filters["award_type_codes"]:
            if set(filters["award_type_codes"]) <= set(contract_type_mapping):
                sort_filters = [award_contracts_mapping[sort]]
            elif set(filters["award_type_codes"]) <= set(loan_type_mapping):  # loans
                sort_filters = [loan_award_mapping[sort]]
            else:  # assistance data
                sort_filters = [non_loan_assistance_award_mapping[sort]]

            if sort == "Award ID":
                sort_filters = ["piid", "fain", "uri"]
            if order == 'desc':
                sort_filters = ['-' + sort_filter for sort_filter in sort_filters]

            queryset = queryset.order_by(*sort_filters).values(*list(values))

        limited_queryset = queryset[lower_limit:upper_limit + 1]
        has_next = len(limited_queryset) > limit

        results = []
        for award in limited_queryset[:limit]:
            row = {"internal_id": award["award_id"]}

            if award['type'] in loan_type_mapping:  # loans
                for field in fields:
                    row[field] = award.get(loan_award_mapping.get(field))
            elif award['type'] in non_loan_assistance_type_mapping:  # assistance data
                for field in fields:
                    row[field] = award.get(non_loan_assistance_award_mapping.get(field))
            elif (award['type'] is None and award['piid']) or award['type'] in contract_type_mapping:  # IDV + contract
                for field in fields:
                    row[field] = award.get(award_contracts_mapping.get(field))

            if "Award ID" in fields:
                for id_type in ["piid", "fain", "uri"]:
                    if award[id_type]:
                        row["Award ID"] = award[id_type]
                        break
            results.append(row)
        # build response
        response = {
            'limit': limit,
            'results': results,
            'page_metadata': {
                'page': page,
                'hasNext': has_next
            }
        }

        return Response(response)

