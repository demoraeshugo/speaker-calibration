import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from scipy.fft import fft, fftfreq
from scipy import signal
from statsmodels.graphics.tsaplots import plot_acf as plt_acf

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), r'data')
SAMPLE_RATE = 96000

N = 18
P = (1 << N) - 1
mls = np.zeros(P, dtype=np.bool_)
tagL = np.empty(P, dtype=np.int_)
tagS = np.empty(P, dtype=np.int_)

generatedSignal = np.empty(P, dtype=np.double)
recordedSignal = np.empty(P, dtype=np.double)
perm = np.empty(P + 1, dtype=np.double)
resp = np.empty(P + 1, dtype=np.double)


def generateMls():
    MAX_NO_TAPS = 18
    TAPS_TABLE = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ], dtype=np.bool_)
    taps = np.empty(MAX_NO_TAPS, np.bool_)
    i = 0
    j = 0
    delayLine = np.zeros(MAX_NO_TAPS, np.bool_)
    sum = 0
    for i in range(N):  # copy the N’th taps table
        taps[i] = TAPS_TABLE[MAX_NO_TAPS - N][i]
        delayLine[i] = 1
    for i in range(P):  # Generate an MLS by summing the taps mod 2
        sum = 0
        for j in range(N):
            sum += taps[j] * delayLine[j]
        sum = sum & 1  # mod 2
        mls[i] = delayLine[N - 1]
        for j in range(N - 2, -1, -1):
            delayLine[j + 1] = delayLine[j]
        delayLine[0] = sum


def getMLS():
    print("Generating MLS...")
    if mls[0] == 0:
        generateMls()
    for i in range(P):
        val = -2 * mls[i] + 1
        generatedSignal[i] = val


def fastHadamard():
    print("Fast Hadamard...")
    i, i1, j, k, k1, k2, P1 = 0, 0, 0, 0, 0, 0, 0
    P1 = P + 1
    k1 = P1
    for k in range(N):
        k2 = k1 >> 1
        for j in range(k2):
            for i in range(j, P1, k1):
                i1 = i + k2
                temp = perm[i] + perm[i1]
                perm[i1] = perm[i] - perm[i1]
                perm[i] = temp
        k1 = k1 >> 1


def permuteSignal():
    print("Permuting signal...")
    dc = 0
    for i in range(P):
        dc += recordedSignal[i]
    perm[0] = -1 * dc
    for i in range(P):
        perm[tagS[i]] = recordedSignal[i]


def permuteResponse():
    print("Permuting response...")
    FACT = 1 / (P + 1)
    for i in range(P):
        resp[i] = perm[tagL[i]] * FACT
    resp[P] = 0


def generateTagL():
    colSum = np.empty(P, dtype=np.int_)
    index = np.empty(P, dtype=np.int_)
    for i in range(P):
        colSum[i] = 0
        for j in range(N):
            colSum[i] += mls[(P + i - j) % P] << (N - 1 - j)
        for j in range(N):
            if colSum[i] == (1 << j):
                index[j] = i
    for i in range(P):
        tagL[i] = 0
        for j in range(N):
            tagL[i] += mls[(P + index[j] - i) % P] * (1 << j)


def generateTagS():
    for i in range(P):
        tagS[i] = 0
        for j in range(N):
            tagS[i] += mls[(P + i - j) % P] * (1 << (N - 1 - j))


def saveBufferToCSV(buffer, pathToFile):
    df = pd.DataFrame(buffer)
    df.to_csv(pathToFile)


def readCSVData(pathToFile):
    df = pd.read_csv(pathToFile)
    df.dropna(inplace=True)
    return df.to_numpy()[:, 1]


def generateAndSaveMLS():
    path = os.path.join(dir_path, r'MLS.csv')
    generateMls()
    saveBufferToCSV(mls, path)


def generateAndSaveMLSSignal():
    path = os.path.join(dir_path, r'generatedMLSSignal.csv')
    getMLS()
    saveBufferToCSV(generatedSignal, path)


def generateTestRecordedSignal():
    print("Generating test recorded signal...")
    for i in range(P):
        recordedSignal[i] = 2.0 * generatedSignal[(P + i - 0) % P] + 0.4 * generatedSignal[(P + i - 1) % P] + 0.2 * generatedSignal[(
            P + i - 2) % P] - 0.1 * generatedSignal[(P + i - 3) % P] - 0.8 * generatedSignal[(P + i - 4) % P]


def generateAndSaveTestRecordedSignal():
    loadMLSSequence()
    print("Generating test recorded signal...")
    generateTestRecordedSignal()
    path = os.path.join(dir_path, r'testRecordedSignal.csv')
    saveBufferToCSV(recordedSignal, path)


def loadTestRecordedSignal():
    print("Loading the test recorded signal...")
    path = os.path.join(dir_path, r'testRecordedSignal.csv')
    globals()['recordedSignal'] = readCSVData(path)


def loadRecordedMLSSignal():
    print("Loading the recorded MLS signal...")
    numExamples = 5
    recordedSignals = []
    for i in range(numExamples):
        fileName = rf'captures/recordedMLSignal_{i}.csv'
        path = os.path.join(dir_path, fileName)
        recordedSignals.append(readCSVData(path))
        print(len(recordedSignals[i]))

    globals()['recordedSignal'] = np.mean(recordedSignals, axis = 0)


def loadMLSSequence():
    print("Loading the saved MLS sequence...")
    path = os.path.join(dir_path, r'mls.csv')
    globals()['mls'] = readCSVData(path)


def loadGeneratedSignal():
    print("Loading the saved generated signal...")
    path = os.path.join(dir_path, r'generatedMLSSignal.csv')
    globals()['generatedSignal'] = readCSVData(path)


def generateAndSaveTagL():
    loadMLSSequence()

    print("Generating the tagL matrix...")
    generateTagL()
    path = os.path.join(dir_path, r'tagL.csv')

    print("Saving the tagL matrix...")
    saveBufferToCSV(tagL, path)


def generateAndSaveTagS():
    loadMLSSequence()

    print("Generating the tagS matrix...")
    generateTagS()
    path = os.path.join(dir_path, r'tagS.csv')

    print("Saving the tagS matrix...")
    saveBufferToCSV(tagS, path)


def loadTagL():
    print("Loading the saved tagL matrix...")
    path = os.path.join(dir_path, r'tagL.csv')
    globals()['tagL'] = readCSVData(path)


def loadTagS():
    print("Loading the saved tagS matrix...")
    path = os.path.join(dir_path, r'tagS.csv')
    globals()['tagS'] = readCSVData(path)


def generateAndSaveAllData():
    generateAndSaveMLS()
    generateAndSaveMLSSignal()
    generateAndSaveTagL()
    generateAndSaveTagS()
    generateAndSaveTestRecordedSignal()


def loadAllData():
    loadMLSSequence()
    loadGeneratedSignal()
    loadTagL()
    loadTagS()
    #loadTestRecordedSignal()
    loadRecordedMLSSignal()


def plotBuffer(buffer, subsample=False):
    plt.style.use('seaborn')

    if subsample == False:
        subsample = len(buffer)

    max_time = len(buffer) / SAMPLE_RATE
    time_steps = np.linspace(0, max_time, len(buffer))

    # make data
    x = [i for i in range(subsample)]
    y = buffer[:subsample]

    # plot
    fig, ax = plt.subplots()

    fig.suptitle('Impulse response')
    plt.xlabel('Time')
    plt.ylabel('amplitude')

    ax.plot(x, y, linewidth=1.0)

    plt.show()


def plotPerm(buffer, subsample=False):
    plt.style.use('seaborn')

    if subsample == False:
        subsample = len(buffer)

    max_time = len(buffer) / SAMPLE_RATE
    time_steps = np.linspace(0, max_time, len(buffer))

    yf = fft(generatedSignal)
    xf = fftfreq(P, 1/SAMPLE_RATE)

    plt.plot(xf, np.abs(yf), linewidth=1.0)
    plt.show()

def autocorr(x, t=1):
    return np.corrcoef(np.array([x[:-t], x[t:]]))

def plotAutoCorrelation(subsample=False):
    max_time = len(generatedSignal) / SAMPLE_RATE
    time_steps = np.linspace(0, max_time, len(generatedSignal))
    
    # if len(recordedSignal) > len(generatedSignal):
    #     start = 250000
    #     end = start + len(generatedSignal)
    #     # truncate the recorded signal to the length of the generated signal
    #     globals()['recordedSignal'] = recordedSignal[start:end]
    
    globals()['recordedSignal'] = recordedSignal[0: len(generatedSignal)]

    corr = signal.correlate(recordedSignal, recordedSignal, mode='same', method='fft')
    lags = signal.correlation_lags(len(recordedSignal), len(generatedSignal), mode='same')
    corr /= P
    
    fig, (ax_orig, ax_noise, ax_corr, ax_wf) = plt.subplots(4, 1, figsize=(10, 6))
    
    ax_orig.plot(generatedSignal)
    ax_orig.set_title('Original signal')
    ax_orig.set_xlabel('Sample Number')
    
    ax_noise.plot(recordedSignal)
    ax_noise.set_title('Signal with noise')
    ax_noise.set_xlabel('Sample Number')
    

    midPoint = np.where(lags == 0)[0][0]
    rang = 100
    left = midPoint-rang
    right = midPoint+rang
    lags = lags[left:right]
    corr = corr[left:right]
    # print(midPoint)
    # print(lags[midPoint], corr[midPoint])
    # print(lags, corr)
    # plt_acf(corr, ax=ax_corr, use_vlines=True, fft=False, lags=lags)
    ax_corr.stem(lags, corr)
    # ax_corr.setp(markerline, markersize = .01)
    ax_corr.set_title('Cross-Correlation')
    ax_corr.set_xlabel('Lag')
    
    left = 0
    right = 10
    ax_wf.plot(resp[left:right])
    ax_wf.set_title('Impulse Response (FWH)')
    ax_wf.set_xlabel('Samples')
    
    ax_orig.margins(0, 0.1)
    ax_noise.margins(0, 0.1)
    ax_corr.margins(0, 0.1)
    ax_wf.margins(0, 0.1)
    fig.tight_layout()
    
    plt.show()


def plotHardamardAutoCorrelation(subsample=False):
    corr = perm
    lags = signal.correlation_lags(len(corr), len(perm), mode='same')

    fig, (ax_orig, ax_noise, ax_corr) = plt.subplots(3, 1, figsize=(4.8, 4.8))
    ax_orig.plot(generatedSignal)
    ax_orig.set_title('Original signal')
    ax_orig.set_xlabel('Sample Number')
    ax_noise.plot(corr)
    ax_noise.set_title('Permuted Signal with noise')
    ax_noise.set_xlabel('Sample Number')
    # ax_corr.plot(lags, corr[0:len(corr)-1])
    ax_corr.plot(lags, corr)
    ax_corr.set_title('Cross-correlated signal')
    ax_corr.set_xlabel('Lag')
    ax_orig.margins(0, 0.1)
    ax_noise.margins(0, 0.1)
    ax_corr.margins(0, 0.1)
    fig.tight_layout()
    plt.show()


def plotImpulseResponse(subsample=False):
    imp = resp

    fig, ax = plt.subplots()

    fig.suptitle('Estimated Impulse Response')
    plt.xlabel('Sample Number')

    # ax.plot(imp, linewidth=1.0)
    ax.plot(fft(imp), linewidth=1.0)

    plt.show()

def butter_lowpass(cutoff, fs, order=5):
    return signal.butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.lfilter(b, a, data)
    return y

def butter_highpass(cutoff, fs, order=5):
    return signal.butter(order, cutoff, fs=fs, btype='high', analog=False)

def butter_high_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.lfilter(b, a, data)
    return y

def plotRecordedSignals(subsample=False):
    # create a sliding window view (50% overlap)
    max_time = len(recordedSignal) / SAMPLE_RATE
    time_steps = np.linspace(0, max_time, len(recordedSignal))
    

    fs = SAMPLE_RATE
    analytic_signal = signal.hilbert(recordedSignal)
    amplitude_envelope = np.abs(analytic_signal)
    low_filtered = butter_high_filter(amplitude_envelope, 0.001, None, 2)

    _, ax = plt.subplots()
    ax.plot(recordedSignal, label='Recorded Signal')
    ax.plot(amplitude_envelope, c='r', label='envelope')
    ax.plot(low_filtered, c='g', label='low pass')
    plt.show()
    # plot
    # fig, ax = plt.subplots()

    # fig.suptitle('Recorded Signals')
    # plt.xlabel('Samples')
    # plt.ylabel('amplitude')

    # ax.plot(recordedSignal, linewidth=1.0)

    # plt.show()

def compareToGeneratedSignal():
    gen_max_time = len(generatedSignal) / SAMPLE_RATE
    gen_time_steps = np.linspace(0, gen_max_time, len(generatedSignal))
    
    rec_max_time = len(recordedSignal) / SAMPLE_RATE
    rec_time_steps = np.linspace(0, rec_max_time, len(recordedSignal))
    
    fig, (ax_gen, ax_rec) = plt.subplots(2, 1, figsize=(4.8, 4.8))
    ax_gen.plot(gen_time_steps, generatedSignal)
    ax_gen.set_title('Original signal')
    ax_gen.set_xlabel('Time')
    
    ax_rec.plot(rec_time_steps, recordedSignal)
    ax_rec.set_title('Recorded Signal with noise')
    ax_rec.set_xlabel('Time')
    
    ax_gen.margins(0, 0.1)
    ax_rec.margins(0, 0.1)
    fig.tight_layout()
    plt.show()

def testRun():
    loadAllData()
    # generateAndSaveTestRecordedSignal()
    # generateAndSaveAllData()
    # plotRecordedSignals()
    # print(len(generatedSignal))
    th = 0.001 #np.average(recordedSignal[recordedSignal > 0]) / 2 # looking for ~ .00157
    th_neg = -1 * th
    print(th, th_neg)
    first = recordedSignal[(recordedSignal > th) | (recordedSignal < th_neg)]
    globals()['recordedSignal'] = first
    
    #compareToGeneratedSignal()

    # permuteSignal()
    # fastHadamard()
    # permuteResponse()

    # plotHardamardAutoCorrelation()

    # plotPerm(perm, subsample=False)

    # plotBuffer(resp, subsample=10)
    # plotImpulseResponse()
    plotAutoCorrelation()


if __name__ == '__main__':
    testRun()
