# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import io
import logging
import time
import grpc  # pylint: disable=import-error
import speech_pb2  # pylint: disable=import-error
import speech_pb2_grpc  # pylint: disable=import-error
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s: %(message)s')
eos_found = False
def generate_message(config_request, sample_rate, audio):
    yield config_request
    interval = 40
    num_bytes_per_interval = int(sample_rate / 1000 * 2 * interval)
    offset = 0
    while not eos_found:
        start = offset
        end = offset + num_bytes_per_interval
        if end >= len(audio):
            end = len(audio)
        if start >= len(audio):
            break
        audio_request = speech_pb2.StreamingRecognizeRequest(
            audio_content=audio[start:end])
        yield audio_request
        # Send audio data per 10ms
        offset = end
        time.sleep(float(interval) / float(1000))
    if eos_found:
        logging.info(
            'Error or silence end has been received, quit sending audio')
def run(host, wav_file, sample_rate, context, disable_itn,
    endpoint_detection, continuous_decoding):
    logging.info('run {}'.format(wav_file))
    channel = grpc.insecure_channel(host)
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
    except grpc.FutureTimeoutError:
        exit("Error connecting to server")
    stub = speech_pb2_grpc.SpeechStub(channel)
    with io.open(wav_file, 'rb') as audio_file:
        audio_content = audio_file.read()
    if context:
        context_words = context.split(",")
    else:
        context_words = []
    recognition_config = speech_pb2.RecognitionConfig(
        encoding=speech_pb2.RecognitionConfig.Encoding.Value("WAV16"),
        sample_rate=sample_rate,
        channel=1,
        max_alternatives=1,
        query_context=context_words,
        disable_itn=disable_itn,
        enable_continuous_decoding=continuous_decoding)

    endpoint_config = speech_pb2.EndpointConfig(start_silence=10,
                                                end_silence=2)
    streaming_recognition_config = speech_pb2.StreamingRecognitionConfig(
        config=recognition_config,
        endpoint_detection=endpoint_detection,
        partial_result=True,
        endpoint_config=endpoint_config)
        
    request = speech_pb2.StreamingRecognizeRequest(
        streaming_config=streaming_recognition_config)
    global eos_found
    eos_found = False
    for response in stub.StreamingRecognize(
        generate_message(request, sample_rate, audio_content)):
        if response.error.code != 0:
            eos_found = True
            logging.error('Error is found {}'.format(response.error.message))
            return
        # speech_event_type code:
        # 0 SPEECH_EVENT_UNSPECIFIED;
        # 1 END_OF_SINGLE_UTTERANCE;
        # 2 CONTINUOUS_DECODING_END_OF_UTTERANCE;
        # 3 STEADY_SPEECH_DETECTED.
        if response.speech_event_type == 0:
            result_txt = response.results[0].alternatives[0].transcript
            if len(result_txt) > 0:
                logging.info("partial_result: {}".format(result_txt))
        elif response.speech_event_type == 1:
            result_txt = response.results[0].alternatives[0].transcript
            if len(result_txt) > 0:
                logging.info("speech_end: {}".format(result_txt))
            eos_found = True
        elif response.speech_event_type == 2:
            result_txt = response.results[0].alternatives[0].transcript
            if len(result_txt) > 0:
                logging.info("final_result: {}".format(result_txt))
        elif response.speech_event_type == 3:
            pass
if __name__ == '__main__':
    usage = '''Get recognition result from ASR grpc server by streaming method'''
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument('--host',
                        help='gRPC server address.',
                        default="106.75.64.52:32768")
    parser.add_argument('--sample_rate',
                        type=int,
                        help='Wav sample rate. Default is 16000Hz',
                        default=16000)
    parser.add_argument('--context',
                        help='Context word to improve recognition accuracy, eg. 专有名词,大城小爱',
                        default="")
    parser.add_argument('--disable_itn',
                        action='store_true',
                        help='Disable ITN.')
    parser.add_argument('--disable_endpoint_detection',
                        action='store_true',
                        help='Disable endpoint detection.')
    parser.add_argument('--continuous_decoding',
                        action='store_true',
                        help='Specify continuous decoding mode.')
    parser.add_argument('wav_file', help='wav file to be sent to server')
    args = parser.parse_args()
    run(args.host, args.wav_file, args.sample_rate, args.context,
        args.disable_itn, not args.disable_endpoint_detection,
        args.continuous_decoding)