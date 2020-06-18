#! /usr/local/bin/python3

import boto3
from botocore.exceptions import ClientError
from argparse import ArgumentParser
from subprocess import run
from pathlib import Path
import logging
import json
import sys

# - Convert file if necessary
# - push to AWS bucket
# - issue trascribe command
# - check status

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.start_transcription_job

LANGUAGE_CODES = ['en-US', 'es-US', 'en-AU', 'fr-CA', 'en-GB', 'de-DE', 'pt-BR', 'fr-FR', 'it-IT', 'ko-KR', 'es-ES', 'en-IN', 'hi-IN', 'ar-SA', 'ru-RU', 'zh-CN', 'nl-NL', 'id-ID', 'ta-IN', 'fa-IR', 'en-IE', 'en-AB', 'en-WL', 'pt-PT', 'te-IN', 'tr-TR', 'de-CH', 'he-IL', 'ms-MY', 'ja-JP', 'ar-AE']

def convert_to_mp4(path, log=None):
    "Converts an audio file to mp4 in the same directory"
    log = log or logging
    output_path = path.with_suffix(".mp4")
    if not output_path.exists():
        log.info("Converting to {}".format(output_path))
        run("ffmpeg -i {} {}".format(path.resolve(), output_path.resolve()), shell=True)
    else:
        log.info("No need to convert audio file format. {} already exists.".format(output_path))
    return output_path

def object_in_bucket(key, bucket):
    return key in [o.key for o in bucket.objects.all()]

def start_or_check_transcription_job(audio_file, bucket_name, audio_file_s3_key=None, language_code="en-US", job_name=None, out_file_path=None, print_result=False, log=None):
    log = log or logging.getLogger(__name__)
    audio_path = Path(audio_file)
    if not audio_path.exists():
        raise ValueError("{} does not exist")
    if audio_path.suffix != '.mp4':
        audio_path = convert_to_mp4(audio_path, log=log)
    if audio_file_s3_key is None:
        audio_file_s3_key = str(audio_path.name)
    S3 = boto3.resource('s3')
    s3 = boto3.client('s3')
    bucket = S3.Bucket(bucket_name)
    if object_in_bucket(audio_file_s3_key, bucket):
        log.info("No need to upload. {} already exists in bucket {}".format(audio_file_s3_key, bucket_name))
    else:
        if audio_file_s3_key == str(audio_path.name):
            log.info("Uploading {}".format(audio_path))
        else:
            log.info("Uploading {} as {}".format(audio_path, s3_name))
        s3.upload_file(str(audio_path), bucket_name, audio_file_s3_key)

    if job_name is None:
        job_name = audio_path.stem
    if out_file_path is None:
        out_file_path = audio_path.with_suffix(".json")

    transcribe = boto3.client('transcribe')
    existing_jobs = transcribe.list_transcription_jobs(JobNameContains=job_name)
    job_exists = len(existing_jobs['TranscriptionJobSummaries'])
    if job_exists:
        job_data = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        log.debug(job_data)
        if job_data['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
            log.info("Job {} is complete".format(job_name))
            if out_file_path.exists():
                log.info("Results saved at {}".format(out_file_path))
            else:
                log.info("Downloading result as {}".format(out_file_path))
                bucket.download_file(job_name + ".json", str(out_file_path))
            if print_result:
                with open(job_name + ".json") as fh:
                    result = json.load(fh)
                    log.info(result["results"]["transcripts"][0]["transcript"])
        else:
            log.info("Status of job {} is {}".format(job_name, jobdata['TranscriptionJobStatus']))
    else:
        log.info("Creating new transcription job called {}".format(job_name))
        result = transcribe.start_transcription_job(
            TranscriptionJobName=job_name, 
            LanguageCode=args.language, 
            Media={'MediaFileUri': "s3://{}/{}".format(args.bucket, audio_file_s3_key)},
            OutputBucketName=args.bucket,
        )
        log.debug(result)
        log.debug("OK")
        log.info("Job {} status is {}".format(job_name, result['TranscriptionJobStatus']))

if __name__ == '__main__':
    parser = ArgumentParser("Transcribe audio via aws. If a job already exists, provides a status update.")
    parser.add_argument("audio_file", help="Audio file to transcribe")
    parser.add_argument("bucket", help="s3 bucket name")
    parser.add_argument("-k", "--key", help="audio file s3 key")
    parser.add_argument("-l", "--language", help="language code", choices=LANGUAGE_CODES, default='en-US')
    parser.add_argument("-j", "--job", help="aws transcription job name")
    parser.add_argument("-o", "--outfile", help="filename for output file (will have .json suffix)")
    parser.add_argument("-p", "--print_result", help="Print transcript result", action="store_true")
    parser.add_argument("-v", "--verbose", help="verbose", action="store_true")
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(levelname)-8s: %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    start_or_check_transcription_job(
        audio_file=args.audio_file, 
        bucket_name=args.bucket, 
        audio_file_s3_key=args.key, 
        language_code=args.language, 
        job_name=args.job, 
        out_file_path=args.outfile, 
        print_result=args.print_result,
        log=log
    )
