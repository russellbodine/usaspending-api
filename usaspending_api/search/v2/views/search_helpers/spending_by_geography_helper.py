import ast
import logging

from rest_framework.response import Response
from django.db.models import FloatField
from django.db.models.functions import Cast
from usaspending_api.awards.v2.filters.location_filter_geocode import geocode_filter_locations
from usaspending_api.awards.v2.filters.filter_helpers import sum_transaction_amount, sum_award_amount
from usaspending_api.awards.v2.filters.view_selector import spending_by_geography
from usaspending_api.awards.v2.filters.view_selector import spending_by_geography_award

from usaspending_api.awards.v2.lookups.lookups import award_type_mapping
from usaspending_api.common.exceptions import InvalidParameterException
from usaspending_api.references.abbreviations import code_to_state, fips_to_code, pad_codes


logger = logging.getLogger(__name__)


class SpendingByGeography:
    # geo_layer = None  # State, county or District
    # geo_layer_filters = None  # Specific geo_layers to filter on
    # queryset = None  # Transaction queryset
    # geo_queryset = None  # Aggregate queryset based on scope

    def spending_by_geography(self, request, transaction_or_award):
        print("HERE27")
        json_request = request.data
        self.scope = json_request.get("scope")
        self.filters = json_request.get("filters", {})
        self.geo_layer = json_request.get("geo_layer")
        self.geo_layer_filters = json_request.get("geo_layer_filters")

        fields_list = []  # fields to include in the aggregate query

        loc_dict = {
            'state': 'state_code',
            'county': 'county_code',
            'district': 'congressional_code'
        }

        model_dict = {
            'place_of_performance': 'pop',
            'recipient_location': 'recipient_location'
        }

        # Build the query based on the scope fields and geo_layers
        # Fields not in the reference objects above then request is invalid

        scope_field_name = model_dict.get(self.scope)
        loc_field_name = loc_dict.get(self.geo_layer)
        loc_lookup = '{}_{}'.format(scope_field_name, loc_field_name)

        if scope_field_name is None:
            raise InvalidParameterException("Invalid request parameters: scope")

        if loc_field_name is None:
            raise InvalidParameterException("Invalid request parameters: geo_layer")

        if transaction_or_award not in ["award", "transaction"]:
            raise InvalidParameterException("Invalid request parameters: transaction_or_award")

        amount_column = None
        if transaction_or_award == "transaction":
            self.queryset, self.matview_model = spending_by_geography(self.filters)
            amount_column = "federal_action_obligation"
        elif transaction_or_award == "award":
            self.queryset, self.matview_model = spending_by_geography_award(self.filters)
            amount_column = "total_obligation"

        if self.geo_layer == 'state':
            # State will have one field (state_code) containing letter A-Z
            kwargs = {
                '{}_country_code'.format(scope_field_name): 'USA',
                '{}__isnull'.format(amount_column): False
            }

            # Only state scope will add its own state code
            # State codes are consistent in db ie AL, AK
            fields_list.append(loc_lookup)

            state_response = {
                'scope': self.scope,
                'geo_layer': self.geo_layer,
                'results': SpendingByGeography.state_results(self, kwargs, fields_list, loc_lookup, transaction_or_award)
            }

            return Response(state_response)

        else:
            # County and district scope will need to select multiple fields
            # State code is needed for county/district aggregation
            state_lookup = '{}_{}'.format(scope_field_name, loc_dict['state'])
            fields_list.append(state_lookup)

            # Adding regex to county/district codes to remove entries with letters since
            # can't be surfaced by map
            kwargs = {'{}__isnull'.format(amount_column): False}

            if self.geo_layer == 'county':
                # County name added to aggregation since consistent in db
                county_name = '{}_{}'.format(scope_field_name, 'county_name')
                fields_list.append(county_name)
                self.county_district_queryset(
                    kwargs,
                    fields_list,
                    loc_lookup,
                    state_lookup,
                    scope_field_name
                )

                county_response = {
                    'scope': self.scope,
                    'geo_layer': self.geo_layer,
                    'results': self.county_results(state_lookup, county_name, transaction_or_award)
                }

                return Response(county_response)
            else:
                self.county_district_queryset(
                    kwargs,
                    fields_list,
                    loc_lookup,
                    state_lookup,
                    scope_field_name
                )

                district_response = {
                    'scope': self.scope,
                    'geo_layer': self.geo_layer,
                    'results': self.district_results(state_lookup)
                }

                return Response(district_response)

    def state_results(self, filter_args, lookup_fields, loc_lookup, transaction_or_award='transaction'):
        # Adding additional state filters if specified
        if self.geo_layer_filters:
            self.queryset = self.queryset.filter(**{'{}__{}'.format(loc_lookup, 'in'): self.geo_layer_filters})
        else:
            # Adding null filter for state for specific partial index
            # when not using geocode_filter
            filter_args['{}__isnull'.format(loc_lookup)] = False

        self.geo_queryset = self.queryset.filter(**filter_args) \
            .values(*lookup_fields)
        filter_types = self.filters['award_type_codes'] if 'award_type_codes' in self.filters else award_type_mapping

        if transaction_or_award == 'transaction':
            self.geo_queryset = sum_transaction_amount(self.geo_queryset, filter_types=filter_types)
        else:
            self.geo_queryset = sum_award_amount(self.geo_queryset, filter_types=filter_types)


        # State names are inconsistent in database (upper, lower, null)
        # Used lookup instead to be consistent
        results = [
            {
                'shape_code': x[loc_lookup],
                'aggregated_amount': x['transaction_amount'],
                'display_name': code_to_state.get(x[loc_lookup], {'name': 'None'}).get('name').title()
            } for x in self.geo_queryset
        ]

        return results

    def county_district_queryset(self, kwargs, fields_list, loc_lookup, state_lookup, scope_field_name):
        # Filtering queryset to specific county/districts if requested
        # Since geo_layer_filters comes as concat of state fips and county/district codes
        # need to split for the geocode_filter
        if self.geo_layer_filters:
            self.queryset &= geocode_filter_locations(scope_field_name, [
                {'state': fips_to_code.get(x[:2]), self.geo_layer: x[2:], 'country': 'USA'}
                for x in self.geo_layer_filters
            ], self.matview_model, True)
        else:
            # Adding null,USA, not number filters for specific partial index
            # when not using geocode_filter
            kwargs['{}__{}'.format(loc_lookup, 'isnull')] = False
            kwargs['{}__{}'.format(state_lookup, 'isnull')] = False
            kwargs['{}_country_code'.format(scope_field_name)] = 'USA'
            kwargs['{}__{}'.format(loc_lookup, 'iregex')] = r'^[0-9]*(\.\d+)?$'

        # Turn county/district codes into float since inconsistent in database
        # Codes in location table ex: '01', '1', '1.0'
        # Cast will group codes as a float and will combine inconsistent codes
        self.geo_queryset = self.queryset.filter(**kwargs) \
            .values(*fields_list)
        self.geo_queryset = self.geo_queryset.annotate(code_as_float=Cast(loc_lookup, FloatField()))
        filter_types = self.filters['award_type_codes'] if 'award_type_codes' in self.filters else award_type_mapping
        self.geo_queryset = sum_transaction_amount(self.geo_queryset, filter_types=filter_types)

        return self.geo_queryset

    def county_results(self, state_lookup, county_name, transaction_or_award='transaction'):
        # Returns county results formatted for map
        results = [
            {
                'shape_code': code_to_state.get(x[state_lookup])['fips'] +
                pad_codes(self.geo_layer, x['code_as_float']),
                'aggregated_amount': x['transaction_amount'],
                'display_name': x[county_name].title() if x[county_name] is not None
                else x[county_name]
            }
            for x in self.geo_queryset
        ]

        return results

    def district_results(self, state_lookup):
        # Returns congressional district results formatted for map
        results = [
            {
                'shape_code': code_to_state.get(x[state_lookup])['fips'] +
                pad_codes(self.geo_layer, x['code_as_float']),
                'aggregated_amount': x['transaction_amount'],
                'display_name': x[state_lookup] + '-' +
                pad_codes(self.geo_layer, x['code_as_float'])
            } for x in self.geo_queryset
        ]

        return results
