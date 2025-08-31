import numpy as np


def interpolate_data(data):
    prev = ''
    previ = 0
    for i in range(len(data)):
        if data[i] != '':
            prev = float(data[i])
            previ = i
        elif prev == '':
            data[i] = 0
        else:
            for j in range(i+1, len(data)):
                if data[j] !='':
                    next = float(data[j])
                    data[i] = float(((next - prev)*i +(prev*j - next*previ))/(j-previ))
                    break
                #Setting the rest to constant last value if the rest is empty
                if j ==(len(data)-1):
                    data[i] = float(prev)
                    data[j] = float(prev)
    
    return data

def interpolate_data_wconstant_start(data,start=150,startval=0):
    if startval == 0:
        startval = data[start]
        #print(startval)

    if all(d == '' for d in data[0:start]) and data[start] != '':
        for i in range(start):
            data[i] = startval
    #print(data)
    return interpolate_data(data)

if __name__ == "__main__":
    test_data = ['','','','',1.5,'','',4.5,5.5,6.5,7.5,'','',4]

    print(interpolate_data(test_data))
