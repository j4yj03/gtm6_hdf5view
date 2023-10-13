import numpy as np
from scipy.signal import welch, spectrogram, convolve, fftconvolve, find_peaks, freqz, butter, lfilter, lfilter_zi

############################
#### Linear Regression Helper
def _extend_matrix(X: np.ndarray) -> np.ndarray:

    X_ext = np.c_[np.ones((np.size(X,0),1)),X]

    return X_ext
# LR_fit
def LR_fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:

    X_ext = _extend_matrix(X)

    theta = np.linalg.solve(X_ext.T.dot(X_ext),X_ext.T.dot(y))

    return theta
# LR_predict
def LR_predict(X: np.ndarray, theta: np.ndarray)-> np.ndarray:

    y = _extend_matrix(X).dot(theta)

    return y


##############################
### Signal Processing Helper
def _butter_bandpass(lowcut:float, highcut:float, fs:float, order:int):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data:np.ndarray, lowcut:float, highcut:float, fs:float, order:int=5):
    b, a = _butter_bandpass(lowcut, highcut, fs, order=order)
    zi = lfilter_zi(b, a)
    y,_ = lfilter(b, a, data, zi=zi*data[0])
    
    y = y[::-1]
    
    y,_ = lfilter(b, a, y, zi=zi*y[0]) # cascade for lag compensation https://dsp.stackexchange.com/questions/26299/zero-lag-butterworth-filtering
    
    return y[::-1]



