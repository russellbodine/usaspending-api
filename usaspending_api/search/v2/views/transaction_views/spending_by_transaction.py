import logging

from rest_framework.views import APIView

from usaspending_api.common.cache_decorator import cache_response
from functools import total_ordering
from usaspending_api.search.v2.views.search_helpers.spending_by_award_or_transaction_helper import \
    SpendingByAwardOrTransaction

logger = logging.getLogger(__name__)


class SpendingByTransactionMatviewVisualizationViewSet(APIView):
    """
    This route takes award filters and fields, and returns the fields of the filtered awards.
    endpoint_doc: /advanced_award_search/spending_by_award.md
    """
    @total_ordering
    class MinType(object):
        def __le__(self, other):
            return True

        def __eq__(self, other):
            return self is other
    Min = MinType()

    @cache_response()
    def post(self, request):

        return SpendingByAwardOrTransaction.spending_by_award_or_transaction(request, "transaction")
