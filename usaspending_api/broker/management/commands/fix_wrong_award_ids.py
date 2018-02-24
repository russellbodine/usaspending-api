import logging
import timeit

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from usaspending_api.etl.award_helpers import update_awards, update_award_categories, update_award_subawards
from usaspending_api.awards.models import Award, TransactionNormalized, Subaward, FinancialAccountsByAwards
from usaspending_api.etl.broker_etl_helpers import dictfetchall


logger = logging.getLogger('console')
exception_logger = logging.getLogger("exceptions")


class Command(BaseCommand):
    help = "Updates awards based on transactions in the database or based on Award IDs passed in"

    @transaction.atomic
    def handle(self, *args, **options):
        logger.info('Starting generated unique award id fix...')
        overall_start = timeit.default_timer()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM wrong_award_ids")
            bad_txs = dictfetchall(cursor)

        logger.info('Number of bad transactions: %s' % str(len(bad_txs)))

        correct_award_id_dict = {}

        # group the transactions based on their corrected award ids
        logger.info('Grouping transactions with their correct award ids...')
        start = timeit.default_timer()
        for tx in bad_txs:
            key = tx['correct_generated_unique_award_id']
            if key in correct_award_id_dict:
                correct_award_id_dict[key].append(tx)
            else:
                correct_award_id_dict[key] = [tx]

        end = timeit.default_timer()
        logger.info('Finished grouping transactions with their correct award ids in ' + str(end - start) + ' seconds')

        awards_to_update = {}

        # sort the list for each correct award id so the newest awards are first
        logger.info('Getting consolidated award object...')
        start = timeit.default_timer()
        for correct_award_id, tx_list in correct_award_id_dict.items():
            new_list = sorted(tx_list, key=lambda x: x['award_id'], reverse=True)

            # after this row is sorted, pull out the latest award, and update it's generated_unique_award_id
            try:
                award_obj = Award.objects.get(generated_unique_award_id=correct_award_id)
            except ObjectDoesNotExist:
                newest_award_id = new_list[0]['award_id']
                award_obj = Award.objects.get(id=newest_award_id)

            awards_to_update[correct_award_id] = award_obj
        end = timeit.default_timer()
        logger.info('Finished getting consolidated award object in ' + str(end - start) + ' seconds')

        award_ids_to_recalc = []
        award_ids_to_delete = set()

        logger.info('Correcting references to point to consolidated award...')
        start = timeit.default_timer()
        example_flag = False

        for correct_award_id, award_obj in awards_to_update.items():
            if award_obj.generated_unique_award_id != correct_award_id:
                if not example_flag:
                    logger.info('Example of old generated unique award id: %s' %
                                str(award_obj.generated_unique_award_id))
                    logger.info('Example of new generated unique award id: %s' % str(correct_award_id))
                    example_flag = True

                award_obj.generated_unique_award_id = correct_award_id
                award_obj.save()
            else:
                logger.info('Award identifier not updated for %s (pk) and %s (generated identifier)' %
                            (str(award_obj.id), award_obj.generated_unique_award_id))

            # update transaction normalized & subawards awards references
            tx_id_list = [tx['transaction_id'] for tx in correct_award_id_dict[correct_award_id]]
            old_award_ids = [tx['award_id'] for tx in correct_award_id_dict[correct_award_id]]

            award_ids_to_delete |= (set(old_award_ids) - {award_obj.id})

            TransactionNormalized.objects.filter(id__in=tx_id_list).update(award_id=award_obj.id,
                                                                           generated_unique_award_id=correct_award_id)
            Subaward.objects.filter(award_id__in=old_award_ids).update(award_id=award_obj.id)
            FinancialAccountsByAwards.objects.filter(award_id__in=old_award_ids).update(award_id=award_obj.id)

            award_ids_to_recalc.append(award_obj.id)
        end = timeit.default_timer()
        logger.info('Finished correcting references to point to consolidated award in ' + str(end - start) + ' seconds')

        logger.info('Deleting %s stale awards...' % str(len(award_ids_to_delete)))
        example_flag = False
        start = timeit.default_timer()
        # check transaction normalized & subaward references for stale awards
        for award_id in award_ids_to_delete:
            if not example_flag:
                logger.info('Example of award pk to be deleted: %s' % str(award_ids_to_delete[0]))
                example_flag = True

            if not (TransactionNormalized.objects.filter(award_id=award_id).exists()
                    or Subaward.objects.filter(award_id=award_id).exists()
                    or FinancialAccountsByAwards.objects.filter(award_id=award_id).exists()):
                Award.objects.filter(id=award_id).delete()
            else:
                raise Exception("Attempted to delete Award PK %s but it's still referenced" % str(award_id))
        end = timeit.default_timer()
        logger.info('Finished deleting stale records in ' + str(end - start) + ' seconds')

        # Update Awards based on changed FABS records
        logger.info('Updating awards to reflect their latest associated transaction info...')
        start = timeit.default_timer()
        update_awards(tuple(award_ids_to_recalc))
        end = timeit.default_timer()
        logger.info('Finished updating awards in ' + str(end - start) + ' seconds')

        # Update AwardCategories based on changed FABS records
        logger.info('Updating award category variables...')
        start = timeit.default_timer()
        update_award_categories(tuple(award_ids_to_recalc))
        end = timeit.default_timer()
        logger.info('Finished updating award category variables in ' + str(end - start) + ' seconds')

        logger.info('Updating subawards...')
        start = timeit.default_timer()
        update_award_subawards(tuple(award_ids_to_recalc))
        end = timeit.default_timer()
        logger.info('Finished updating subawards in ' + str(end - start) + ' seconds')

        end = timeit.default_timer()
        logger.info('Finished generated unique award id fix in ' + str(end - overall_start) + ' seconds')
