"""
Creates legal entities and adds them to transaction normalized rows and award rows based on transaction_location_data
from `create_locations`
"""

import logging

from django.core.management.base import BaseCommand
from django.db import connection


logger = logging.getLogger('console')
exception_logger = logging.getLogger("exceptions")


class Command(BaseCommand):

    def handle(self, *args, **options):

        with connection.cursor() as curs:
            curs.execute(self.CREATE_FABA_CORRECTOR_TABLE)
            curs.execute(self.ALTER_FABA_CORRECTOR_TABLE)
            logger.info('FABA_CORRECTOR TABLE CREATED')

            curs.execute(self.UNLINK_FILE_C_FILE_D)
            logger.info('FILE_C_FILE_D_UNLINKED. {} file C rows'.format(curs.rowcount))

            curs.execute(self.CREATE_FILE_C_FILE_D_MAPPING_AWARD)
            logger.info('NEW LINKAGES ADDED TO FABA CORRECTOR. {} potential links '
                        '(including duplicates)'.format(curs.rowcount))

            curs.execute(self.CREATE_FILE_C_FILE_D_MAPPING_TRANSACTION)
            logger.info('NEW LINKAGES ADDED TO FABA CORRECTOR (awards with URI and FAIN). {} potential links '
                        '(including duplicates)'.format(curs.rowcount))

            curs.execute(self.LINK_FILE_C_FILE_D)
            logger.info('NEW LINKAGES APPLIED TO FILE C: FILE D. {} successful links'.format(curs.rowcount))

    CREATE_FABA_CORRECTOR_TABLE = """
        CREATE TEMPORARY TABLE faba_corrector (
            financial_accounts_by_awards_id int,
            new_award_id int,
            update_date timestamp with time zone   -- add a last updated line
            );
    """

    ALTER_FABA_CORRECTOR_TABLE = """
        ALTER TABLE faba_corrector ADD CONSTRAINT faba_corrector_uc
        UNIQUE (financial_accounts_by_awards_id, new_award_id);
    """

    UNLINK_FILE_C_FILE_D = """
        UPDATE financial_accounts_by_awards
            SET award_id = NULL;
    """

    CREATE_FILE_C_FILE_D_MAPPING_AWARD = """
        WITH bad_faba AS   -- GET BAD/Unmapped FABA
            (SELECT
                financial_accounts_by_awards_id,
                faba.piid,
                faba.fain,
                faba.uri,
                faba.parent_award_id,
                awards.recipient_id
            FROM financial_accounts_by_awards as faba
            LEFT OUTER JOIN awards
                ON award_id = awards.id
            WHERE awards.recipient_id IS NULL --Bad link or Unlinked
            AND (faba.piid is not Null
                OR (faba.fain is not Null AND faba.uri is Null)
                OR (faba.uri is not Null AND faba.fain is Null)
                )
            ),
        correct_awards AS
            (SELECT a.id, a.piid, a.fain, a.uri, pa.piid as parent_award_piid
            FROM awards AS a
            LEFT OUTER JOIN awards AS pa
                ON pa.id = a.parent_award_id
            where a.recipient_id is not Null
            AND (a.piid is not Null
                OR (a.fain is not Null AND a.uri is Null)
                OR (a.uri is not Null AND a.fain is Null)
                )
            )
        INSERT INTO faba_corrector (financial_accounts_by_awards_id, new_award_id)
          SELECT bad_faba.financial_accounts_by_awards_id, correct_awards.id FROM bad_faba, correct_awards
          WHERE COALESCE(correct_awards.piid, '') = COALESCE(bad_faba.piid, '')
            AND COALESCE(correct_awards.fain, '') = COALESCE(bad_faba.fain, '')
            AND COALESCE(correct_awards.uri, '') = COALESCE(bad_faba.uri, '')
            AND COALESCE(correct_awards.parent_award_piid, '') = COALESCE(bad_faba.parent_award_id, '')
            --FABA has piid in parent award id val
            ON CONFLICT ON CONSTRAINT faba_corrector_uc
                DO NOTHING
        ;
    """

    # This script attempts to find file C awards with URI and FAIN, and link them to a distinct award_id.
    CREATE_FILE_C_FILE_D_MAPPING_TRANSACTION = """
        WITH bad_faba AS   -- GET BAD/Unmapped FABA
            (SELECT 
                financial_accounts_by_awards_id,
                faba.fain,
                faba.uri,
                awards.recipient_id
            FROM financial_accounts_by_awards as faba
            left outer JOIN awards
                ON award_id = awards.id
            WHERE (awards.latest_transaction_id IS NULL) --BAD or NOTMAPPED
            AND (faba.fain is not Null AND faba.uri is not Null)
            ),
        correct_transactions AS
            (SELECT DISTINCT tn.award_id, tf.fain, tf.uri
            from transaction_normalized as tn
            join transaction_fabs as tf 
                on tf.transaction_id = tn.id
            where (tf.fain is not Null AND tf.uri is not Null)
            )
        INSERT INTO faba_corrector (financial_accounts_by_awards_id, new_award_id)
            
          SELECT bad_faba.financial_accounts_by_awards_id, correct_transactions.award_id FROM bad_faba, correct_transactions
          WHERE COALESCE(correct_transactions.fain, '') = COALESCE(bad_faba.fain, '')
            AND COALESCE(correct_transactions.uri, '') = COALESCE(bad_faba.uri, '')
            ON CONFLICT ON CONSTRAINT faba_corrector_uc 
                DO NOTHING
    """

    LINK_FILE_C_FILE_D = """
        UPDATE financial_accounts_by_awards as faba
            SET award_id = faba_corrector.new_award_id
            FROM faba_corrector
            WHERE (faba.financial_accounts_by_awards_id = faba_corrector.financial_accounts_by_awards_id
            AND (Select Count(*) from faba_corrector
            where faba.financial_accounts_by_awards_id=faba_corrector.financial_accounts_by_awards_id) = 1);
    """
