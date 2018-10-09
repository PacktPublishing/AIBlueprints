import re
import numpy as np
from tensorflow.python.keras.models import Sequential, load_model
from tensorflow.python.keras.layers import Input, Dropout, Flatten, Conv2D, MaxPooling2D, Dense, Activation
from tensorflow.python.keras.preprocessing.image import DirectoryIterator, ImageDataGenerator

# all images will be converted to this size
ROWS = 256
COLS = 256
CHANNELS = 3

TRAIN_DIR = '/bigdata/data/flickrlogos/FlickrLogos-v2/train/classes/jpg/'
TEST_DIR = '/bigdata/data/flickrlogos/FlickrLogos-v2/test/classes/jpg/'

img_generator = ImageDataGenerator() # do not modify images

train_dir_iterator = DirectoryIterator(TRAIN_DIR, img_generator, target_size=(ROWS, COLS), color_mode='rgb', seed=1)
test_dir_iterator = DirectoryIterator(TEST_DIR, img_generator, target_size=(ROWS, COLS), color_mode='rgb', shuffle=False)

train_class_map = {v: k for k, v in train_dir_iterator.class_indices.items()}
test_class_map = {v: k for k, v in test_dir_iterator.class_indices.items()}

model = Sequential()
model.add(Conv2D(32, (3,3), strides=(1,1), padding='same', input_shape=(ROWS, COLS, CHANNELS)))
model.add(Activation('relu'))
model.add(Conv2D(32, (3,3), strides=(1,1), padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Conv2D(64, (3,3), strides=(1,1), padding='same'))
model.add(Activation('relu'))
model.add(Conv2D(64, (3,3), strides=(1,1), padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Conv2D(128, (3,3), strides=(1,1), padding='same'))
model.add(Activation('relu'))
model.add(Conv2D(128, (3,3), strides=(1,1), padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Flatten())
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_dir_iterator.class_indices)))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy', optimizer='sgd', metrics=['accuracy'])

from tensorflow.python.keras.utils import plot_model
plot_model(model, to_file='keras-logos-model.png', show_shapes=True, show_layer_names=True)

model.summary()

model.fit_generator(train_dir_iterator, epochs=20)

