import csv
import io
import logging
import time

import boto
import smart_open
import zipstream
from django.conf import settings
from django.db.models import Q

from usaspending_api.download.lookups import JOB_STATUS_DICT
from usaspending_api.download.v2 import download_column_historical_lookups
import traceback
logger = logging.getLogger('console')


def update_number_of_columns(row, download_job):
    if download_job.number_of_columns is None:
        download_job.number_of_columns = len(row)
    else:
        download_job.number_of_columns = max(download_job.number_of_columns, len(row))


def csv_row_emitter(body, download_job):
    header_row = True
    for row in body:
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)
        writer.writerow(row)
        if header_row:
            update_number_of_columns(row, download_job)
            header_row = False
        else:
            download_job.number_of_rows += 1
            if download_job.number_of_rows > settings.MAX_DOWNLOAD_LIMIT:
                break
                raise Exception('Requested query beyond max supported ({})'.format(settings.MAX_DOWNLOAD_LIMIT))

        yield string_buffer.getvalue().encode('utf8')


class CsvSource:
    def __init__(self):
        self.human_names = download_column_historical_lookups.human_names[self.model_type][self.file_type]
        self.query_paths = download_column_historical_lookups.query_paths[self.model_type][self.file_type]

    def values(self, header):
        query_paths = [self.query_paths[hn] for hn in header]
        return self.queryset.values_list(query_paths).iterator()

    def columns(self, requested):
        """Given a list of column names requested, returns the ones available in the source"""

        if requested:
            result = []
            for column in requested:
                if column in self.human_names:
                    result.append(column)
        else:
            result = self.human_names

        # remove headers that we don't have a query path for
        result = [h for h in result if h in self.query_paths]

        return result

    def row_emitter(self, headers_requested):
        headers = self.columns(headers_requested)
        yield headers
        query_paths = [self.query_paths[hn] for hn in headers]
        yield from self.queryset.values_list(*query_paths).iterator()


class ContractsPrimeAwardsCsvSource(CsvSource):

    model_type = 'award'
    file_type = 'd1'
    file_descrip = 'contracts_prime_awards'
    filter = Q(latest_transaction__contract_data__isnull=False)


class AssistancePrimeAwardsCsvSource(CsvSource):

    model_type = 'award'
    file_type = 'd2'
    file_descrip = 'assistance_prime_awards'
    filter = Q(latest_transaction__assistance_data__isnull=False)


class ContractsSubAwardsCsvSource(CsvSource):

    model_type = 'subaward'
    file_type = 'd1'
    file_descrip = 'contracts_subawards'
    filter = Q()


class AssistanceSubAwardsCsvSource(CsvSource):

    model_type = 'subaward'
    file_type = 'd2'
    file_descrip = 'assistance_subawards'
    filter = Q()


class ContractsPrimeTransactionsCsvSource(CsvSource):

    model_type = 'transaction'
    file_type = 'd1'
    file_descrip = 'contracts_prime_transactions'
    filter = Q(contract_data__isnull=False)


class AssistancePrimeTransactionsCsvSource(CsvSource):

    model_type = 'transaction'
    file_type = 'd2'
    file_descrip = 'assistance_prime_transactions'
    filter = Q(assistance_data__isnull=False)


def write_csvs(download_job, file_name, columns, sources):
    """Derive the relevant location and write CSVs to it.

    :return: the final file name (complete with prefix)"""

    download_job.job_status_id = JOB_STATUS_DICT['running']
    download_job.number_of_rows = 0
    download_job.file_size = 0
    download_job.save()

    try:
        file_path = settings.CSV_LOCAL_PATH + file_name
        zstream = zipstream.ZipFile()
        minutes = settings.DOWNLOAD_TIMEOUT_MIN_LIMIT
        timeout = time.time() + 60 * minutes

        logger.debug('Generating {}'.format(file_name))

        for source in sources:
            zstream.write_iter('{}.csv'.format(source.file_descrip), csv_row_emitter(
                source.row_emitter(columns), download_job))
            logger.debug('wrote %s.csv' % source.file_descrip)

        if settings.IS_LOCAL:

            with open(file_path, 'wb') as zipfile:
                for chunk in zstream:
                    zipfile.write(chunk)
                    # Adding timeout to break the stream if exceeding time limit, closes out thread
                    if time.time() > timeout:
                        raise Exception('Stream exceeded time of {} minutes.'.format(minutes))

                download_job.file_size = zipfile.tell()
        else:
            bucket = settings.CSV_S3_BUCKET_NAME
            region = settings.CSV_AWS_REGION
            s3_bucket = boto.s3.connect_to_region(region).get_bucket(bucket)
            conn = s3_bucket.new_key(file_name)
            stream = smart_open.smart_open('s3://{}/{}'.format(bucket, file_name), 'wb', region_name=region)
            for chunk in zstream:
                stream.write(chunk)
                # Adding timeout to break the stream if exceeding time limit, closes out thread
                if time.time() > timeout:
                    raise Exception('Stream exceeded time of {} minutes.'.format(minutes))
            download_job.file_size = stream.tell()

    except Exception as e:
        download_job.job_status_id = JOB_STATUS_DICT['failed']
        download_job.error_message = 'An exception was raised while attempting to write the CSV'
        logger.error(traceback.format_exc())

        if settings.DEBUG:
            download_job.error_message += '\n' + str(e)
    else:
        download_job.job_status_id = JOB_STATUS_DICT['finished']
    finally:
        try:
            stream.close()
            s3_bucket.lookup(conn.key).set_acl('public-read')
        except NameError:
            # there was no stream to close
            pass

    download_job.save()

    return file_name
