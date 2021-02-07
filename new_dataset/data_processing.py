import numpy as np
import matplotlib.pyplot as plt
import copy
from pathlib import Path
import os


def process_csv(title):
    path = str(Path().absolute())
    file_name = path+'/new_dataset/'+title +'.csv'
    dataset = np.genfromtxt(file_name, delimiter = ',', skip_header=1)

    series = dataset[:,4]   

    ans = []

    for index in range(len(series)-5):
        start = index
        end = index + 6
        ans.append(series[start:end].tolist())
    
    train_rows = round(0.8 * len(series))
    test_rows = len(series) - train_rows

    new_dataset = np.array(ans)

    train_set = new_dataset[:train_rows]
    test_set = new_dataset[train_rows:]

    os.mkdir(path+'/new_dataset/'+title)

    np.savetxt(path+'/new_dataset/'+title+'/'+'train.csv', train_set,delimiter = ',',fmt='%f')
    np.savetxt(path+'/new_dataset/'+title+'/'+'test.csv', test_set,delimiter = ',',fmt='%f')


process_csv('STI')
process_csv('DJI')
process_csv('FTSE')
process_csv('GSPC')
process_csv('HSI')
process_csv('IXIC')
process_csv('N225')




