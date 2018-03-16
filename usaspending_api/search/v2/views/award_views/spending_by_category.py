import logging

from rest_framework.views import APIView

from usaspending_api.common.cache_decorator import cache_response
from usaspending_api.search.v2.views.search_helpers.spending_by_category_helper import SpendingByCategory

logger = logging.getLogger(__name__)


class SpendingByCategoryAwardVisualizationViewSet(APIView):
    """
    This route takes award filters, and returns spending by the defined category/scope.
    The category is defined by the category keyword, and the scope is defined by is denoted by the scope keyword.
    endpoint_doc: /advanced_award_search/spending_by_category.md
    """
    @cache_response()
    def post(self, request):

        return SpendingByCategory.spending_by_category(request, "award")
