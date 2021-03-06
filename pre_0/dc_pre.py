import os
import numpy as np
import datetime as dt
# import matplotlib.pyplot as plt

subjects = ['19']
#['21', '22', '23', '24', '25', '26', '27', '28', '29', '30']
#['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18','19', '20'

activities = ['01', '02', '03', '05', '06', '07']

folder = 'E:/MEx/Data/raw/dc/'
target_folder = 'E:/MEx/Data/pre_1/dc/'

data_file = 'this.bin'
time_file = 'time.bin'
full_file = '.csv'


def write_data(file_path, data):
    if os.path.isfile(file_path):
        f = open(file_path, 'a')
        f.write(data + '\n')
    else:
        f = open(file_path, 'w')
        f.write(data + '\n')
    f.close()


for subject in subjects:
    if not os.path.exists(target_folder+subject):
        os.makedirs(target_folder+subject)

    for activity in activities:
        print(activity)
        fd = open(folder+subject+'_'+activity+'_1_'+data_file, "rb")
        data = np.fromfile(fd, dtype=np.uint32)
        ft = open(folder+subject+'_'+activity+'_1_'+time_file, "rb")
        timeData = np.loadtxt(ft, dtype=np.unicode)

        length = int(len(data)/(640*480))
        data = np.reshape(data, (length,480,640))
        data = data[:,:240,:320]
        data = np.reshape(data, (length, 240*320))
        #_data = np.reshape(data, (length*240*320))
        #_data.sort()
        #print(_data[0])
        #print(str(_data[len(_data)-1])+','+str(_data[len(_data)-2])+','+str(_data[len(_data)-3]))

        # minmax normalisation
        _data = np.reshape(data, (length*240*320))
        _data = _data / max(_data)
        _data = np.reshape(_data, (length,240*320))

        # write to pre-process step 1 folder
        target_file = target_folder+subject+'/'+subject+'_'+activity+'.csv'
        for itime, idata in zip(timeData, _data):
            timee = itime[1].split('.')
            if len(timee[1]) == 1:
               timee[1] = '00'+timee[1]
            elif len(timee[1]) == 2:
                timee[1] = '0'+timee[1]

            itime[1] = '.'.join(timee)
            tt = dt.datetime.strptime(' '.join(itime), '%Y-%m-%d %H:%M:%S.%f')
            write_data(target_file, str(tt)+','+','.join([str(float("{0:.4f}".format(f))) for f in idata]))

        # visualise
        #for i in range(len(_data)):
        #    if i % 2000:
        #        plt.imshow(_data[i])
        #        plt.show()


