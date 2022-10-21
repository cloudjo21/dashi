python -m dashi.torch2onnx_for_pretraining \
    --model_type=hf.plm_model \
    --pt_model_name=monologg/koelectra-small-v3-discriminator \
    --tokenizer_name=monologg/koelectra-small-v3-discriminator