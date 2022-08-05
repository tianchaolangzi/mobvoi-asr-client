# Attention:
   1. Your python must be python3
   2. You can add --continuous_decoding to specify it's continuous decoding mode.


# Requriements: 
    pip install grpcio-tools
# Usage:
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. speech.proto
    python grpc_client.py --host=ip:prot test.wav



# mobvoi asr service 
    cantonese asr host: 117.50.100.153:9595
    sichuan dialect asr host: 117.50.100.153:9596


# example

    python grpc_client.py --continuous_decoding --host=117.50.100.153:9595 test_wavs/test_yue_1.wav

    python grpc_client.py --continuous_decoding --host=117.50.100.153:9596 test_wavs/test_chuan_1.wav
