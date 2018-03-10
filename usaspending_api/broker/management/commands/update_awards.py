import logging
import timeit

from django.core.management.base import BaseCommand
from django.db import transaction

from django.db import connection
from usaspending_api.etl.award_helpers import update_awards, update_contract_awards, update_award_categories

# start = timeit.default_timer()
# function_call
# end = timeit.default_timer()
# time elapsed = str(end - start)


logger = logging.getLogger('console')
exception_logger = logging.getLogger("exceptions")


class Command(BaseCommand):
    help = "Updates awards based on transactions in the database or based on Award IDs passed in"

    @transaction.atomic
    def handle(self, *args, **options):
        logger.info('Starting updates to award data...')

        with connection.cursor() as cursor:
            # cursor.execute("SELECT id FROM fpds_dup_award_ids")
            # contract_award_ids = cursor.fetchall()
            cursor.execute("SELECT id from awards as aw "
                           "where aw.certified_date is Null"
                           "OR aw.certified_date != ("
                                "select action_date from transaction_normalized as txn "
                                "where txn.id = aw.latest_transaction_id)")
            assistance_award_ids = cursor.fetchall()

            award_update_id_list = assistance_award_ids  # + contract_award_ids
            # award_contract_update_id_list = contract_award_ids

        # logger.info('Number of contract awards: %s' % str(len(contract_award_ids)))
        logger.info('Number of assistance awards: %s' % str(len(assistance_award_ids)))
        # logger.info('Updating %s awards' % str(len(award_update_id_list)))
        # logger.info('Updating %s contract awards' % str(len(award_contract_update_id_list)))

        award_update_id_list = [int(award_id[0]) for award_id in award_update_id_list]

        logger.info('printing a few ids for testing purposes')
        if len(award_update_id_list) > 10:
            logger.info(award_update_id_list[:10])
        else:
            logger.info(award_update_id_list)

        # award_contract_update_id_list = [int(award_id[0]) for award_id in award_contract_update_id_list]

        logger.info('Updating awards to reflect their latest associated transaction info...')
        start = timeit.default_timer()
        update_awards(tuple(award_update_id_list))
        end = timeit.default_timer()
        logger.info('Finished updating awards in ' + str(end - start) + ' seconds')

        # logger.info('Updating contract-specific awards to reflect their latest transaction info...')
        # start = timeit.default_timer()
        # update_contract_awards(tuple(award_contract_update_id_list))
        # end = timeit.default_timer()
        # logger.info('Finished updating contract specific awards in ' + str(end - start) + ' seconds')

        logger.info('Updating award category variables...')
        start = timeit.default_timer()
        update_award_categories(tuple(award_update_id_list))
        end = timeit.default_timer()
        logger.info('Finished updating award category variables in ' + str(end - start) + ' seconds')

        # Done!
        logger.info('FINISHED')
