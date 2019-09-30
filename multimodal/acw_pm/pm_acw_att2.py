import os
import csv
import datetime as dt
import numpy as np
import sklearn.metrics as metrics
from keras.layers import Layer, Input, Dense, BatchNormalization, Conv1D, MaxPooling1D, LSTM, TimeDistributed, Reshape, concatenate, Multiply
from keras.models import Model
import keras.backend as K
import random
from scipy import fftpack
from keras.utils import np_utils
from tensorflow import set_random_seed
import tensorflow as tf
import sys
random.seed(0)
np.random.seed(1)

ac_frame_size = 3*1
pm_frame_size = 16*16

activity_list = ['01', '02', '03', '04', '05', '06', '07']
id_list = range(len(activity_list))
activity_id_dict = dict(zip(activity_list, id_list))

acw_path = '/Volumes/1708903/MEx/Data/acwmin/'
pm_path = '/Volumes/1708903/MEx/Data/pm_scaled/1.0_0.5_min'

results_file = 'pm_acw.csv'

pm_frames_per_second = 5
ac_frames_per_second = 100

window = 5
increment = 2
dct_length = 60
feature_length = dct_length * 3
fusion = 0

ac_min_length = 95*window
ac_max_length = 100*window
pm_min_length = pm_frames_per_second*window
pm_max_length = 15*window


class EarlyAttentionLayer(Layer):
    def __init__(self, dims, **kwargs):
        super(EarlyAttentionLayer, self).__init__(**kwargs)
        self.dims = dims
        self.W = tf.keras.layers.Dense(self.dims)
        self.V = tf.keras.layers.Dense(1)

    def build(self, input_shape):
        super(EarlyAttentionLayer, self).build(input_shape)

    def call(self, inputs):
        # (, 200)
        z = tf.concat(inputs, axis=2)
        print(K.int_shape(z))
        # (, 1, 200)
        z = tf.expand_dims(z, 1)
        print(K.int_shape(z))

        z = tf.reduce_sum(z, 4)
        print(K.int_shape(z))
        # (, 1, 200)
        score = tf.nn.tanh(self.W(z))
        print(K.int_shape(score))
        # (, 1, 200)
        attention_weights = tf.nn.softmax(score)
        print(K.int_shape(attention_weights))
        # (, 1, 200)
        context_vector = attention_weights * z
        print(K.int_shape(context_vector))
        # (, 200)
        context_vector = tf.reduce_sum(context_vector, axis=1)
        print(K.int_shape(context_vector))

        z = tf.expand_dims(context_vector, 3)
        print(K.int_shape(z))

        return z

    def compute_output_shape(self, input_shape):
        input_shapes = input_shape
        return input_shapes[0][0], input_shapes[0][1], self.dims, 1


class AttentionLayer(Layer):
    def __init__(self, dims, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)
        self.dims = dims
        self.W = tf.keras.layers.Dense(self.dims)
        self.V = tf.keras.layers.Dense(1)

    def build(self, input_shape):
        super(AttentionLayer, self).build(input_shape)

    def call(self, inputs):
        # (, 200)
        z = tf.concat(inputs, axis=1)
        print(K.int_shape(z))
        # (, 1, 200)
        z = tf.expand_dims(z, 1)
        print(K.int_shape(z))
        # (, 1, 200)
        score = tf.nn.tanh(self.W(z))
        print(K.int_shape(score))
        # (, 1, 200)
        attention_weights = tf.nn.softmax(score)
        print(K.int_shape(attention_weights))
        # (, 1, 200)
        context_vector = attention_weights * z
        print(K.int_shape(context_vector))
        # (, 200)
        context_vector = tf.reduce_sum(context_vector, axis=1)
        print(K.int_shape(context_vector))
        return context_vector

    def compute_output_shape(self, input_shape):
        input_shapes = input_shape
        return input_shapes[0][0], self.dims


def write_data(file_path, data):
    if os.path.isfile(file_path):
        f = open(file_path, 'a')
        f.write(data + '\n')
    else:
        f = open(file_path, 'w')
        f.write(data + '\n')
    f.close()


def _read(_file):
    reader = csv.reader(open(_file, "r"), delimiter=",")
    _data = []
    for row in reader:
        if len(row[0]) == 19 and '.' not in row[0]:
            row[0] = row[0]+'.000000'
        temp = [dt.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')]
        _temp = [float(f) for f in row[1:]]
        temp.extend(_temp)
        _data.append(temp)
    return _data


def read(path, _sensor):
    alldata = {}
    subjects = os.listdir(path)
    for subject in subjects:
        allactivities = {}
        subject_path = os.path.join(path, subject)
        activities = os.listdir(subject_path)
        activities = [f for f in activities if not f.startswith('.')]
        for activity in activities:
            sensor = activity.split('.')[0].replace(_sensor, '')
            activity_id = sensor.split('_')[0]
            sensor_index = sensor.split('_')[1]
            _data = _read(os.path.join(subject_path, activity), )
            if activity_id in allactivities:
                allactivities[activity_id][sensor_index] = _data
            else:
                allactivities[activity_id] = {}
                allactivities[activity_id][sensor_index] = _data
        alldata[subject] = allactivities
    return alldata


def find_index(_data, _time_stamp):
    return [_index for _index, _item in enumerate(_data) if _item[0] >= _time_stamp][0]


def trim_ac(_data):
    _length = len(_data)
    _inc = _length/(window*ac_frames_per_second)
    _new_data = []
    for i in range(window*ac_frames_per_second):
        _new_data.append(_data[i*_inc])
    return _new_data


def trim_pm(_data):
    _length = len(_data)
    _inc = _length/(window*pm_frames_per_second)
    _new_data = []
    for i in range(window*pm_frames_per_second):
        _new_data.append(_data[i*_inc])
    return _new_data


def frame_reduce(_features):
    if pm_frames_per_second == 0:
        return _features
    new_features = {}
    for subject in _features:
        _activities = {}
        activities = _features[subject]
        for activity in activities:
            activity_data = activities[activity]
            time_windows = []
            for item in activity_data:
                new_item = []
                new_item.append(trim_ac(item[0]))
                new_item.append(trim_pm(item[1]))
                time_windows.append(new_item)
            _activities[activity] = time_windows
        new_features[subject] = _activities
    return new_features


def split_windows(acw_data, pm_data):
    outputs = []
    start = acw_data[0][0]
    end = acw_data[len(acw_data) - 1][0]
    _increment = dt.timedelta(seconds=increment)
    _window = dt.timedelta(seconds=window)

    acw_frames = [a[1:] for a in acw_data[:]]
    pm_frames = [a[1:] for a in pm_data[:]]

    acw_frames = np.array(acw_frames)
    acw_frames = np.array(acw_frames)
    acw_length = acw_frames.shape[0]
    acw_frames = np.reshape(acw_frames, (acw_length*ac_frame_size))
    print(max(acw_frames))
    print(min(acw_frames))
    acw_frames = acw_frames/(max(acw_frames)-min(acw_frames))
    print(max(acw_frames))
    print(min(acw_frames))
    acw_frames = [float("{0:.5f}".format(f)) for f in acw_frames.tolist()]
    acw_frames = np.reshape(np.array(acw_frames), (acw_length, ac_frame_size))

    pm_frames = np.array(pm_frames)
    _length = pm_frames.shape[0]
    pm_frames = np.reshape(pm_frames, (_length*pm_frame_size))
    print(max(pm_frames))
    print(min(pm_frames))
    pm_frames = pm_frames/max(pm_frames)
    print(max(pm_frames))
    print(min(pm_frames))
    pm_frames = [float("{0:.5f}".format(f)) for f in pm_frames.tolist()]
    pm_frames = np.reshape(np.array(pm_frames), (_length, pm_frame_size))

    while start + _window < end:
        _end = start + _window
        acw_start_index = find_index(acw_data, start)
        acw_end_index = find_index(acw_data, _end)
        pm_start_index = find_index(pm_data, start)
        pm_end_index = find_index(pm_data, _end)
        acw_instances = [a[:] for a in acw_frames[acw_start_index:acw_end_index]]
        pm_instances = [a[:] for a in pm_frames[pm_start_index:pm_end_index]]
        start = start + _increment
        instances = [acw_instances, pm_instances]
        outputs.append(instances)
    return outputs


def extract_features(acw_data, pm_data):
    _features = {}
    for subject in acw_data:
        _activities = {}
        acw_activities = acw_data[subject]
        for acw_activity in acw_activities:
            time_windows = []
            activity_id = activity_id_dict.get(acw_activity)
            acw_activity_data = acw_data[subject][acw_activity]
            pm_activity_data = pm_data[subject][acw_activity]
            for item in acw_activity_data.keys():
                time_windows.extend(split_windows(acw_activity_data[item], pm_activity_data[item]))
            _activities[activity_id] = time_windows
        _features[subject] = _activities
    return _features


def train_test_split(user_data, test_ids):
    train_data = {key: value for key, value in user_data.items() if key not in test_ids}
    test_data = {key: value for key, value in user_data.items() if key in test_ids}
    return train_data, test_data


def dct(data):
    new_data = []
    data = np.array(data)
    print(data.shape)
    data = np.reshape(data, (data.shape[0], window, ac_frames_per_second, 3))
    print(data.shape)
    for item in data:
        new_item = []
        for i in range(item.shape[0]):
            if dct_length > 0:
                x = [t[0] for t in item[i]]
                y = [t[1] for t in item[i]]
                z = [t[2] for t in item[i]]

                dct_x = np.abs(fftpack.dct(x, norm='ortho'))
                dct_y = np.abs(fftpack.dct(y, norm='ortho'))
                dct_z = np.abs(fftpack.dct(z, norm='ortho'))

                v = np.array([])
                v = np.concatenate((v, dct_x[:dct_length]))
                v = np.concatenate((v, dct_y[:dct_length]))
                v = np.concatenate((v, dct_z[:dct_length]))
                new_item.append(v)
        new_data.append(new_item)
    return new_data


def flatten(_data):
    flatten_data = []
    flatten_labels = []
    for subject in _data:
        activities = _data[subject]
        for activity in activities:
            activity_data = activities[activity]
            flatten_data.extend(activity_data)
            flatten_labels.extend([activity for i in range(len(activity_data))])

    dct_acw = dct([f[0] for f in flatten_data])
    dct_acw = np.array(dct_acw)
    pm = [f[1] for f in flatten_data]
    return dct_acw, pm, flatten_labels


def pad(data, length):
    pad_length = []
    if length % 2 == 0:
        pad_length = [int(length / 2), int(length / 2)]
    else:
        pad_length = [int(length / 2) + 1, int(length / 2)]
    new_data = []
    for index in range(pad_length[0]):
        new_data.append(data[0])
    new_data.extend(data)
    for index in range(pad_length[1]):
        new_data.append(data[len(data) - 1])
    return new_data


def reduce(data, length):
    red_length = []
    if length % 2 == 0:
        red_length = [int(length / 2), int(length / 2)]
    else:
        red_length = [int(length / 2) + 1, int(length / 2)]
    new_data = data[red_length[0]:len(data) - red_length[1]]
    return new_data


def pad_features(_features):
    new_features = {}
    for subject in _features:
        new_activities = {}
        activities = _features[subject]
        for act in activities:
            items = activities[act]
            new_items = []
            for item in items:
                new_item = []
                acw_len = len(item[0])
                pm_len = len(item[1])

                if acw_len > ac_max_length:
                    new_item.append(reduce(item[0], acw_len - ac_max_length))
                elif acw_len < ac_max_length:
                    new_item.append(pad(item[0], ac_max_length - acw_len))
                else:
                    new_item.append(item[0])

                if pm_len > pm_max_length:
                    new_item.append(reduce(item[1], pm_len - pm_max_length))
                elif pm_len < pm_max_length:
                    new_item.append(pad(item[1], pm_max_length - pm_len))
                else:
                    new_item.append(item[1])

                new_items.append(new_item)
            new_activities[act] = new_items
        new_features[subject] = new_activities
    return new_features


def build_early_fusion():
    input_pm = Input(shape=(window, pm_frames_per_second*pm_frame_size, 1))
    input_w = Input(shape=(window, feature_length, 1))

    input_wpm = EarlyAttentionLayer(feature_length+(pm_frames_per_second*pm_frame_size))([input_w, input_pm])

    x = TimeDistributed(Conv1D(32, kernel_size=5, activation='relu'))(input_wpm)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Conv1D(64, kernel_size=5, activation='relu'))(x)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Conv1D(128, kernel_size=5, activation='relu'))(x)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Conv1D(256, kernel_size=5, activation='relu'))(x)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = Reshape((K.int_shape(x)[1], K.int_shape(x)[2]*K.int_shape(x)[3]))(x)
    x = LSTM(1200)(x)
    x = BatchNormalization()(x)
    x = Dense(600, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dense(100, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dense(len(activity_list), activation='softmax')(x)

    model = Model(inputs=[input_w, input_pm], outputs=x)
    model.summary()
    return model


def build_mid_fusion():
    input_pm = Input(shape=(window, pm_frames_per_second*pm_frame_size, 1))
    input_w = Input(shape=(window, feature_length, 1))

    x = TimeDistributed(Conv1D(32, kernel_size=5, activation='relu'))(input_pm)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Conv1D(64, kernel_size=5, activation='relu'))(x)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = Reshape((K.int_shape(x)[1], K.int_shape(x)[2]*K.int_shape(x)[3]))(x)
    x = LSTM(1200)(x)
    x = BatchNormalization()(x)

    y = TimeDistributed(Conv1D(32, kernel_size=5, activation='relu'))(input_w)
    y = TimeDistributed(MaxPooling1D(pool_size=2))(y)
    y = TimeDistributed(BatchNormalization())(y)
    y = TimeDistributed(Conv1D(64, kernel_size=5, activation='relu'))(y)
    y = TimeDistributed(MaxPooling1D(pool_size=2))(y)
    y = TimeDistributed(BatchNormalization())(y)
    y = Reshape((K.int_shape(y)[1], K.int_shape(y)[2]*K.int_shape(y)[3]))(y)
    y = LSTM(1200)(y)
    y = BatchNormalization()(y)

    z = AttentionLayer(2400)([x, y])

    z = Dense(600, activation='relu')(z)
    z = BatchNormalization()(z)
    z = Dense(200, activation='relu')(z)
    z = BatchNormalization()(z)

    z = Dense(len(activity_list), activation='softmax')(z)

    model = Model(inputs=[input_w, input_pm], outputs=z)
    model.summary()
    return model


def build_late_fusion():
    input_pm = Input(shape=(window, pm_frames_per_second*pm_frame_size, 1))
    input_w = Input(shape=(window, feature_length, 1))

    x = TimeDistributed(Conv1D(32, kernel_size=5, activation='relu'))(input_pm)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = TimeDistributed(Conv1D(64, kernel_size=5, activation='relu'))(x)
    x = TimeDistributed(MaxPooling1D(pool_size=2))(x)
    x = TimeDistributed(BatchNormalization())(x)
    x = Reshape((K.int_shape(x)[1], K.int_shape(x)[2]*K.int_shape(x)[3]))(x)
    x = LSTM(1200)(x)
    x = BatchNormalization()(x)
    x = Dense(600, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dense(100, activation='relu')(x)
    x = BatchNormalization()(x)

    y = TimeDistributed(Conv1D(32, kernel_size=5, activation='relu'))(input_w)
    y = TimeDistributed(MaxPooling1D(pool_size=2))(y)
    y = TimeDistributed(BatchNormalization())(y)
    y = TimeDistributed(Conv1D(64, kernel_size=5, activation='relu'))(y)
    y = TimeDistributed(MaxPooling1D(pool_size=2))(y)
    y = TimeDistributed(BatchNormalization())(y)
    y = Reshape((K.int_shape(y)[1], K.int_shape(y)[2]*K.int_shape(y)[3]))(y)
    y = LSTM(1200)(y)
    y = BatchNormalization()(y)
    y = Dense(600, activation='relu')(y)
    y = BatchNormalization()(y)
    y = Dense(100, activation='relu')(y)
    y = BatchNormalization()(y)

    z = AttentionLayer(200)([x, y])
    z = Dense(len(activity_list), activation='softmax')(z)

    model = Model(inputs=[input_w, input_pm], outputs=z)
    model.summary()
    return model


def _run_(acw_train_features, pm_train_features, train_labels, acw_test_features, pm_test_features, test_labels):
    pm_train_features = np.array(pm_train_features)
    pm_train_features = np.reshape(pm_train_features, (pm_train_features.shape[0], window, pm_frames_per_second*16*16))
    pm_train_features = np.expand_dims(pm_train_features, 4)
    print(pm_train_features.shape)

    pm_test_features = np.array(pm_test_features)
    pm_test_features = np.reshape(pm_test_features, (pm_test_features.shape[0], window, pm_frames_per_second*16*16))
    pm_test_features = np.expand_dims(pm_test_features, 4)
    print(pm_test_features.shape)

    acw_train_features = np.array(acw_train_features)
    acw_train_features = np.expand_dims(acw_train_features, 3)
    print(acw_train_features.shape)

    acw_test_features = np.array(acw_test_features)
    acw_test_features = np.expand_dims(acw_test_features, 3)
    print(acw_test_features.shape)

    if fusion == 0:
        model = build_early_fusion()
    elif fusion == 1:
        model = build_mid_fusion()
    else:
        model = build_late_fusion()

    model.compile(optimizer='adadelta', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit([acw_train_features, pm_train_features], train_labels, verbose=1, batch_size=32, epochs=30, shuffle=True)
    _predict_labels = model.predict([acw_test_features, pm_test_features], batch_size=64, verbose=0)
    f_score = metrics.f1_score(test_labels.argmax(axis=1), _predict_labels.argmax(axis=1), average='macro')
    accuracy = metrics.accuracy_score(test_labels.argmax(axis=1), _predict_labels.argmax(axis=1))
    results = 'acw_pm' + ',' + str(fusion)+',' + str(sys.argv[2])+',' + str(accuracy)+',' + str(f_score)
    print(results)
    write_data(results_file, str(results))


acw_data = read(acw_path, '_acw')
pm_data = read(pm_path, '_pm')

all_features = extract_features(acw_data, pm_data)

all_features = pad_features(all_features)
all_features = frame_reduce(all_features)

i = '01'
set_random_seed(2)

train_features, test_features = train_test_split(all_features, [i])

_acw_train_features, _pm_train_features, _train_labels = flatten(train_features)
_acw_test_features, _pm_test_features, _test_labels = flatten(test_features)

_train_labels = np_utils.to_categorical(_train_labels, len(activity_list))
_test_labels = np_utils.to_categorical(_test_labels, len(activity_list))

_run_(_acw_train_features, _pm_train_features, _train_labels, _acw_test_features, _pm_test_features, _test_labels)
