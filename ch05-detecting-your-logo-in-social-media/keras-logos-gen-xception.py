import re
import os
import numpy as np
from tensorflow.python.keras.applications.xception import Xception
from tensorflow.python.keras import Model
from tensorflow.python.keras.models import load_model, save_model
from tensorflow.python.keras.layers import Dense, Activation
from tensorflow.python.keras.preprocessing.image import DirectoryIterator, ImageDataGenerator
from tensorflow.python.keras.callbacks import TensorBoard
from sklearn.metrics import confusion_matrix

# all images will be converted to this size
ROWS = 299 # specific for Xception model
COLS = 299 # specific for Xception model
CHANNELS = 3
EPOCHS = 200
THRESHOLD = 0.005

TRAIN_DIR = '/bigdata/data/flickrlogos/FlickrLogos-v2/train/classes/jpg/'
TRAIN_SAVE_DIR = '/bigdata/data/flickrlogos/FlickrLogos-v2/train-gen/'
TEST_DIR = '/bigdata/data/flickrlogos/FlickrLogos-v2/test/classes/jpg/'

img_generator = ImageDataGenerator(rescale=1./255, rotation_range=45, zoom_range=0.5, shear_range=30, validation_split=0.2)

train_dir_iterator = DirectoryIterator(TRAIN_DIR, img_generator, target_size=(ROWS, COLS), color_mode='rgb', save_to_dir=TRAIN_SAVE_DIR, seed=1, subset='training')
val_dir_iterator = DirectoryIterator(TRAIN_DIR, img_generator, target_size=(ROWS, COLS), color_mode='rgb', save_to_dir=TRAIN_SAVE_DIR, seed=1, subset='validation')
test_dir_iterator = DirectoryIterator(TEST_DIR, img_generator, target_size=(ROWS, COLS), color_mode='rgb', shuffle=False)

train_class_map = {v: k for k, v in train_dir_iterator.class_indices.items()}
test_class_map = {v: k for k, v in test_dir_iterator.class_indices.items()}

if not os.path.exists('keras-logos-gen-xception-ep%d.model' % EPOCHS):

    # create the base pre-trained model
    base_model = Xception(weights='imagenet', include_top=False, pooling='avg')

    # add a fully-connected layer
    dense_layer = Dense(1024, activation='relu')(base_model.output)
    out_layer = Dense(len(train_dir_iterator.class_indices))(dense_layer)
    out_layer_activation = Activation('sigmoid')(out_layer)

    # this is the model we will train
    model = Model(inputs=base_model.input, outputs=out_layer_activation)

    # first: train only the dense top layers (which were randomly initialized)
    # i.e. freeze all convolutional Xception layers
    for layer in base_model.layers:
        layer.trainable = False

    model.compile(loss='categorical_crossentropy', optimizer='sgd', metrics=['accuracy'])

    from tensorflow.python.keras.utils import plot_model
    plot_model(model, to_file='keras-logos-gen-xception-model.png', show_shapes=True, show_layer_names=True)

    model.summary()

    tensorboard = TensorBoard(log_dir='./tensorboard-logs', histogram_freq=1, write_graph=False)

    model.fit_generator(train_dir_iterator, epochs=EPOCHS, validation_data=val_dir_iterator, callbacks=[tensorboard])

    # unfreeze all layers for more training
    for layer in model.layers:
        layer.trainable = True

    model.compile(loss='categorical_crossentropy', optimizer='sgd', metrics=['accuracy'])

    model.fit_generator(train_dir_iterator, epochs=EPOCHS, validation_data=val_dir_iterator, callbacks=[tensorboard])

    save_model(model, 'keras-logos-gen-xception-ep%d.model' % EPOCHS)
else:
    model = load_model('keras-logos-gen-xception-ep%d.model' % EPOCHS)

all_predictions = []
with open("keras-logos-gen-xception-ep%d-thresh%0.2f-predictions.txt" % (EPOCHS, THRESHOLD), 'w') as out:
    idx = 0
    for batch in test_dir_iterator:
        filenames = test_dir_iterator.filenames[idx : idx + test_dir_iterator.batch_size]
        if len(filenames) == 0:
            break
        idx += test_dir_iterator.batch_size
        predictions = model.predict_on_batch(batch[0])
        for i in range(len(predictions)):
            truth = test_class_map[np.argmax(batch[1][i])]
            conf = np.max(predictions[i])
            if conf >= THRESHOLD:
                predicted = train_class_map[np.argmax(predictions[i])]
            else:
                predicted = "no-logo"
            all_predictions.append(test_dir_iterator.class_indices[predicted])
            m = re.match(r".*/(\d+)\.jpg", filenames[i])
            fid = m.group(1)
            print("file = %s\ttruth = %s\tpredicted = %s\tconfidence = %f" % (filenames[i], truth, predicted, conf))
            out.write("%s, %s, %f\n" % (fid, predicted, conf))

# generate confusion matrix
cm = confusion_matrix(test_dir_iterator.classes, all_predictions)
print(cm)

# from http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import itertools
def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    #plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=90)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    #for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
    #    plt.text(j, i, format(cm[i, j], fmt),
    #             horizontalalignment="center",
    #             color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')


# handle no-logo in the confusion matrix; probably build as we go above
classes = [test_class_map[k] for k in sorted(test_class_map.keys())]
print(classes)
plt.figure(figsize=(10,10), dpi=300)
plot_confusion_matrix(cm, classes, normalize=True)
plt.savefig("keras-logos-gen-xception-cm-ep%d-thresh%0.2f.png" % (EPOCHS, THRESHOLD))

