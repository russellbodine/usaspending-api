import logging

from rest_framework.views import APIView

from usaspending_api.common.cache_decorator import cache_response
from usaspending_api.search.v2.views.search_helpers.spending_by_geography_helper import SpendingByGeography

logger = logging.getLogger(__name__)


class SpendingByGeographyAwardVisualizationViewSet(APIView):
    """
        This route takes award filters, and returns spending by state code, county code, or congressional district code.
        endpoint_doc: /advanced award search/spending_by_geography.md
    """

    @cache_response()
    def post(self, request):

        return SpendingByGeography.spending_by_geography(self, request, "award")
