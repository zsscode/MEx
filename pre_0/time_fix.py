import os
import csv
import datetime as dt

subjects = ['01', '16', '27', '28', '29', '30', '26']

transition_times = {'01': '2018-11-08 11:46:40.000000,2018-11-08 11:46:52.000000',
                    '02': '2019-02-20 14:28:35.000000,2019-02-20 14:28:43.000000',
                    '03': '2018-06-06 09:22:38.000000,2018-06-06 09:22:50.000000',
                    '04': '2018-06-06 11:36:37.000000,2018-06-06 11:36:43.000000',
                    '05': '2018-06-12 14:01:30.000000,2018-06-12 14:01:44.000000',
                    '06': '2018-06-13 13:48:25.000000,2018-06-13 13:48:36.000000',
                    '07': '2018-06-13 16:21:23.000000,2018-06-13 16:21:29.000000',
                    '08': '2018-10-11 11:50:07.000000,2018-10-11 11:50:21.000000',
                    '09': '2018-10-11 12:37:37.000000,2018-10-11 12:37:45.000000',
                    '10': '2018-10-11 13:12:32.000000,2018-10-11 13:12:42.000000',
                    '11': '2018-10-11 15:29:00.000000,2018-10-11 15:29:12.000000',
                    '12': '2018-10-11 15:54:00.000000,2018-10-11 15:54:09.000000',
                    '13': '2018-11-08 12:19:40.000000,2018-11-08 12:19:49.000000',
                    '14': '2019-02-11 17:11:34.000000,2019-02-11 17:11:44.000000',
                    '15': '2019-02-12 11:23:41.000000,2019-02-12 11:23:47.000000',
                    '16': '2019-03-26 17:02:32.000000,2019-03-26 17:02:42.000000',
                    '17': '2019-02-14 10:14:36.000000,2019-02-14 10:14:46.000000',
                    '18': '2019-02-14 11:50:48.000000,2019-02-14 11:50:56.000000',
                    '19': '2019-02-20 12:18:55.000000,2019-02-20 12:19:05.000000',
                    '20': '2019-02-20 12:55:29.000000,2019-02-20 12:55:35.000000',
                    '21': '2019-03-05 13:21:47.000000,2019-03-05 13:21:58.000000',
                    '22': '2019-03-07 12:19:59.500000,2019-03-07 12:19:59.500000',
                    '23': '2019-03-07 12:44:09.000000,2019-03-07 12:44:20.000000',
                    '24': '2019-03-07 13:12:33.000000,2019-03-07 13:12:48.000000',
                    '25': '2019-03-07 15:01:37.000000,2019-03-07 15:01:52.000000',
                    '26': '2019-03-25 13:25:16.000000,2019-03-25 13:25:24.000000',
                    '27': '2019-03-25 13:49:11.000000,2019-03-25 13:49:20.000000',
                    '28': '2019-03-25 14:16:44.000000,2019-03-25 14:17:15.000000',
                    '29': '2019-03-26 16:04:06.000000,2019-03-26 16:04:15.000000',
                    '30': '2019-03-26 16:38:29.000000,2019-03-26 16:38:38.000000'}

correction_times = {'01': 5,
                    '02': 28,
                    '03': -15,
                    '04': -16,
                    '05': -13,
                    '06': -15,
                    '07': -16,
                    '08': 0,
                    '09': 0,
                    '10': 0,
                    '11': 0,
                    '12': 0,
                    '13': 6,
                    '14': 23,
                    '15': 24,
                    '16': 34,
                    '17': 30,
                    '18': 29,
                    '19': 27,
                    '20': 29,
                    '21': 16,
                    '22': 30,
                    '23': 31,
                    '24': 31,
                    '25': 29,
                    '26': 33,
                    '27': 36,
                    '28': 34,
                    '29': 32,
                    '30': 31}


def write_data(file_path, data):
    if os.path.isfile(file_path):
        f = open(file_path, 'a')
        f.write(data + '\n')
    else:
        f = open(file_path, 'w')
        f.write(data + '\n')
    f.close()


def remove_transition():
    # subjects = os.listdir('/Volumes/1708903/MEx/Data/1/dc/')
    for subject in subjects:
        subject_files = os.path.join('E:/MEx/Data/pre_1/dc/', subject)
        activities = os.listdir(subject_files)
        transitions = transition_times[subject].split(',')
        start = dt.datetime.strptime(transitions[0], '%Y-%m-%d %H:%M:%S.%f')
        end = dt.datetime.strptime(transitions[1], '%Y-%m-%d %H:%M:%S.%f')
        target_folder = os.path.join('E:/MEx/Data/pre_2/dc/', subject)
        correction = correction_times[subject]
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        for activity in activities:
            data_file = os.path.join(subject_files, activity)
            activity_id = activity.split('_')[1].replace('.csv', '')
            if activity_id == '04':
                file_1 = os.path.join(target_folder, subject + '_' + activity_id + '_1.csv')
                file_2 = os.path.join(target_folder, subject + '_' + activity_id + '_2.csv')
                reader = csv.reader(open(data_file, "r"), delimiter=",")
                for row in reader:
                    if len(row) == 76801:
                        if len(row[0]) == 19 and '.' not in row[0]:
                            row[0] = row[0]+'.000000'
                        # print(row[0])
                        tt = dt.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                        if tt <= start:
                            tt = tt + dt.timedelta(seconds=correction)
                            write_data(file_1, str(tt) + ',' + ','.join([str(f) for f in row[1:]]))
                        elif tt >= end:
                            tt = tt + dt.timedelta(seconds=correction)
                            write_data(file_2, str(tt) + ',' + ','.join([str(f) for f in row[1:]]))
            else:
                file = os.path.join(target_folder, subject + '_' + activity_id + '_1.csv')
                reader = csv.reader(open(data_file, "r"), delimiter=",")
                for row in reader:
                    if len(row) == 76801:
                        if len(row[0]) == 19 and '.' not in row[0]:
                            row[0] = row[0]+'.000000'
                        # print(row[0])
                        tt = dt.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                        tt = tt + dt.timedelta(seconds=correction)
                        write_data(file, str(tt) + ',' + ','.join([str(f) for f in row[1:]]))


def ac_time_fix():
    wrist_files = os.listdir('E:/MEx/Data/pre_1/acw/')
    target_folder = 'E:/MEx/Data/pre_2/acw/'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    for w in wrist_files:
        subject = w.split('_')[0]
        correction = correction_times[subject]
        target_file = os.path.join(target_folder, w)
        data_file = os.path.join('E:/MEx/Data/pre_1/acw/', w)
        reader = csv.reader(open(data_file, "r"), delimiter=",")
        for row in reader:
            if len(row) == 4:
                if len(row[0]) == 19 and '.' not in row[0]:
                    row[0] = row[0]+'.000000'
                # print(row[0])
                tt = dt.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                tt = tt + dt.timedelta(seconds=correction)
                write_data(target_file, str(tt) + ',' + ','.join([str(f) for f in row[1:]]))

    thigh_files = os.listdir('E:/MEx/Data/pre_1/act/')
    target_folder = 'E:/MEx/Data/pre_2/act/'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    for t in thigh_files:
        subject = t.split('_')[0]
        correction = correction_times[subject]
        target_file = os.path.join(target_folder, t)
        data_file = os.path.join('E:/MEx/Data/pre_1/act/', t)
        reader = csv.reader(open(data_file, "r"), delimiter=",")
        for row in reader:
            if len(row) == 4:
                if len(row[0]) == 19 and '.' not in row[0]:
                    row[0] = row[0]+'.000000'
                # print(row[0])
                tt = dt.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                tt = tt + dt.timedelta(seconds=correction)
                write_data(target_file, str(tt) + ',' + ','.join([str(f) for f in row[1:]]))


remove_transition()
#ac_time_fix()
