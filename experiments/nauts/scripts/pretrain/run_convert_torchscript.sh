#!/bin/bash

export MODEL_NAME=bert-base-cased
export TOKENIZER_NAME=bert_word_piece
export SNAPSHOT=20220420_103052_307204
export CHECKPOINT=global_step0

# cp pre-trained model to nauts dir
mkdir -p $NAUTS_LOCAL_ROOT/user/nauts/mart/plm/models/$MODEL_NAME

cp $NAUTS_LOCAL_ROOT/user/nauts/pretrain/model/bert/$SNAPSHOT/config.json $NAUTS_LOCAL_ROOT/user/nauts/mart/plm/models/$MODEL_NAME/
cp $NAUTS_LOCAL_ROOT/user/nauts/pretrain/model/bert/$SNAPSHOT/$CHECKPOINT/mp_rank_00_model_states.pt $NAUTS_LOCAL_ROOT/user/nauts/mart/plm/models/$MODEL_NAME/pytorch_model.bin

cd src && nohup python -m dashi.torch2torchscript_for_pretraining \
  --pt_model_name=$MODEL_NAME \
  --tokenizer_name=$TOKENIZER_NAME \
  > ../torch2torchscript_for_pretraining.nohup \
  2>&1 &
