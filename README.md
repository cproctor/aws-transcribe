# AWS Transcribe

This is a simple helper script to transcribe audio files using AWS Transcribe. Converts file format, uploads to AWS, checks job status, and fetches result. 

```
usage: Transcribe audio via aws. If a job already exists, provides a status update.
       [-h] [-k KEY]
       [-l {language code}]
       [-j JOB] [-o OUTFILE] [-p] [-v]
       audio_file bucket

positional arguments:
  audio_file            Audio file to transcribe
  bucket                s3 bucket name

optional arguments:
  -h, --help            show this help message and exit
  -k KEY, --key KEY     audio file s3 key
  -l {language code}, --language {language code}
                        language code. Defaults to en-US
  -j JOB, --job JOB     aws transcription job name
  -o OUTFILE, --outfile OUTFILE
                        filename for output file (will have .json suffix)
  -p, --print_result    Print transcript result
  -v, --verbose         verbose
```
