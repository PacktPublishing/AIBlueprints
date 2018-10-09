#!/bin/sh

python3 -m rasa_nlu.train --config config.yml --data training/tarot-training_rasa.json --path tarot_rasa

