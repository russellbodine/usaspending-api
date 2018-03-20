import ast
import logging

from rest_framework.response import Response
from django.db.models import F

from usaspending_api.awards.models_matviews import UniversalAwardView
from usaspending_api.awards.models_matviews import UniversalTransactionView
from usaspending_api.awards.v2.filters.matview_filters import matview_search_filter
from usaspending_api.awards.v2.filters.filter_helpers import sum_transaction_amount
from usaspending_api.awards.v2.filters.view_selector import can_use_view
from usaspending_api.awards.v2.filters.view_selector import get_view_queryset
from usaspending_api.awards.v2.lookups.lookups import award_type_mapping
from usaspending_api.common.exceptions import InvalidParameterException
from usaspending_api.common.helpers import get_simple_pagination_metadata
from usaspending_api.references.models import Cfda

logger = logging.getLogger(__name__)


class SpendingByCategory:

    def spending_by_category(self, request, transaction_or_award):
        """Return all budget function/subfunction titles matching the provided search text"""
        # TODO: check logic in name_dict[x]["aggregated_amount"] statements

        json_request = request.data
        category = json_request.get("category", None)
        scope = json_request.get("scope", None)
        filters = json_request.get("filters", None)
        limit = json_request.get("limit", 10)
        page = json_request.get("page", 1)

        lower_limit = (page - 1) * limit
        upper_limit = page * limit

        if category is None:
            raise InvalidParameterException("Missing one or more required request parameters: category")
        potential_categories = ["awarding_agency", "funding_agency", "recipient", "cfda_programs", "industry_codes"]
        if category not in potential_categories:
            raise InvalidParameterException("Category does not have a valid value")
        if (scope is None) and (category != "cfda_programs"):
            raise InvalidParameterException("Missing one or more required request parameters: scope")
        if filters is None:
            raise InvalidParameterException("Missing one or more required request parameters: filters")
        amount_column = None
        queryset = None
        if transaction_or_award == "transaction":
            queryset = matview_search_filter(filters, UniversalTransactionView, transaction_or_award)
            amount_column = "federal_action_obligation"
        elif transaction_or_award == "award":
            queryset = matview_search_filter(filters, UniversalAwardView, transaction_or_award)
            amount_column = "total_obligation"
        # filter queryset

        filter_types = filters['award_type_codes'] if 'award_type_codes' in filters else award_type_mapping

        # filter the transactions by category
        if category == "awarding_agency":
            potential_scopes = ["agency", "subagency"]
            if scope not in potential_scopes:
                raise InvalidParameterException("scope does not have a valid value")

            if scope == "agency":
                queryset = queryset \
                    .filter(awarding_toptier_agency_name__isnull=False) \
                    .values(
                        agency_name=F('awarding_toptier_agency_name'),
                        agency_abbreviation=F('awarding_toptier_agency_abbreviation'))

            elif scope == "subagency":
                queryset = queryset \
                    .filter(
                        awarding_subtier_agency_name__isnull=False) \
                    .values(
                        agency_name=F('awarding_subtier_agency_name'),
                        agency_abbreviation=F('awarding_subtier_agency_abbreviation'))

            elif scope == "office":
                    # NOT IMPLEMENTED IN UI
                    raise NotImplementedError

            queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types)\
                .order_by('-aggregated_amount')
            results = list(queryset[lower_limit:upper_limit + 1])

            page_metadata = get_simple_pagination_metadata(len(results), limit, page)
            results = results[:limit]

            response = {"category": category, "scope": scope, "limit": limit, "results": results,
                        "page_metadata": page_metadata}
            return Response(response)

        elif category == "funding_agency":
            potential_scopes = ["agency", "subagency"]
            if scope not in potential_scopes:
                raise InvalidParameterException("scope does not have a valid value")

            if scope == "agency":
                queryset = queryset \
                    .filter(funding_toptier_agency_name__isnull=False) \
                    .values(
                        agency_name=F('funding_toptier_agency_name'),
                        agency_abbreviation=F('funding_toptier_agency_abbreviation'))

            elif scope == "subagency":
                queryset = queryset \
                    .filter(
                        funding_subtier_agency_name__isnull=False) \
                    .values(
                        agency_name=F('funding_subtier_agency_name'),
                        agency_abbreviation=F('funding_subtier_agency_abbreviation'))

            elif scope == "office":
                # NOT IMPLEMENTED IN UI
                raise NotImplementedError

            queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                .order_by('-aggregated_amount')
            results = list(queryset[lower_limit:upper_limit + 1])

            page_metadata = get_simple_pagination_metadata(len(results), limit, page)
            results = results[:limit]

            response = {"category": category, "scope": scope, "limit": limit, "results": results,
                        "page_metadata": page_metadata}
            return Response(response)

        elif category == "recipient":
            if scope == "duns":
                queryset = queryset \
                    .values(legal_entity_id=F("recipient_id"))
                queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                    .order_by('-aggregated_amount') \
                    .values("aggregated_amount", "legal_entity_id", "recipient_name") \
                    .order_by("-aggregated_amount")

                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])

                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]

            elif scope == "parent_duns":
                queryset = queryset \
                    .filter(parent_recipient_unique_id__isnull=False)
                queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types,
                                                  calculate_totals=False) \
                    .values(
                        'aggregated_amount',
                        'recipient_name',
                        'parent_recipient_unique_id') \
                    .order_by('-aggregated_amount')

                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])
                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]

            else:  # recipient_type
                raise InvalidParameterException("recipient type is not yet implemented")

            response = {"category": category, "scope": scope, "limit": limit, "results": results,
                        "page_metadata": page_metadata}
            return Response(response)

        elif category == "cfda_programs":
            if can_use_view(filters, 'SummaryCfdaNumbersView'):
                queryset = get_view_queryset(filters, 'SummaryCfdaNumbersView')
                queryset = queryset \
                    .filter(
                        federal_action_obligation__isnull=False,
                        cfda_number__isnull=False) \
                    .values(cfda_program_number=F("cfda_number"))
                queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                    .values(
                        "aggregated_amount",
                        "cfda_program_number",
                        program_title=F("cfda_title")) \
                    .order_by('-aggregated_amount')

                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])
                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]
                for trans in results:
                    trans['popular_name'] = None
                    # small DB hit every loop here
                    cfda = Cfda.objects \
                        .filter(
                            program_title=trans['program_title'],
                            program_number=trans['cfda_program_number']) \
                        .values('popular_name').first()

                    if cfda:
                        trans['popular_name'] = cfda['popular_name']

            else:
                queryset = queryset \
                    .filter(
                        cfda_number__isnull=False) \
                    .values(cfda_program_number=F("cfda_number"))
                queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                    .values(
                        "aggregated_amount",
                        "cfda_program_number",
                        popular_name=F("cfda_popular_name"),
                        program_title=F("cfda_title")) \
                    .order_by('-aggregated_amount')

                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])
                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]

            response = {"category": category, "limit": limit, "results": results, "page_metadata": page_metadata}
            return Response(response)

        elif category == "industry_codes":  # industry_codes
            if scope == "psc":
                if can_use_view(filters, 'SummaryPscCodesView'):
                    queryset = get_view_queryset(filters, 'SummaryPscCodesView')
                    queryset = queryset \
                        .filter(product_or_service_code__isnull=False) \
                        .values(psc_code=F("product_or_service_code"))
                else:
                    queryset = queryset \
                        .filter(psc_code__isnull=False) \
                        .values("psc_code")

                queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                    .order_by('-aggregated_amount')
                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])

                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]

                response = {"category": category, "scope": scope, "limit": limit, "results": results,
                            "page_metadata": page_metadata}
                return Response(response)

            elif scope == "naics":
                if can_use_view(filters, 'SummaryNaicsCodesView'):
                    queryset = get_view_queryset(filters, 'SummaryNaicsCodesView')
                    queryset = queryset \
                        .filter(naics_code__isnull=False) \
                        .values('naics_code')
                    queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                        .order_by('-aggregated_amount') \
                        .values(
                            'naics_code',
                            'aggregated_amount',
                            'naics_description')
                else:
                    queryset = queryset \
                        .filter(naics_code__isnull=False) \
                        .values("naics_code")
                    queryset = sum_transaction_amount(queryset, 'aggregated_amount', filter_types=filter_types) \
                        .order_by('-aggregated_amount') \
                        .values(
                            'naics_code',
                            'aggregated_amount',
                            'naics_description')

                # Begin DB hits here
                results = list(queryset[lower_limit:upper_limit + 1])

                page_metadata = get_simple_pagination_metadata(len(results), limit, page)
                results = results[:limit]

                response = {"category": category, "scope": scope, "limit": limit, "results": results,
                            "page_metadata": page_metadata}
                return Response(response)

            else:  # recipient_type
                raise InvalidParameterException("recipient type is not yet implemented")
