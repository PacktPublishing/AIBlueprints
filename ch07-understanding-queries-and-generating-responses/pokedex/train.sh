#!/bin/sh

python3 -m rasa_nlu.train --config config.yml --data training/pokedex-training_rasa.json --path pokedex_rasa

