#!/bin/sh

python3 -m rasa_nlu.train --config config.yml --data training/rasa_dataset_training.json --path tarot_rasa

