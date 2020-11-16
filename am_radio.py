# Import
import csv
import time
import numpy as np
import sounddevice as sd
from ctypes import *
from scipy.io.wavfile import write


def init():    
    # Try opening the device    
    try:
        print("Opening device...")
        dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))
    except:
        print("Failed to open device...")
        exit()

def setup_adc(sam_freq=800000.0):
    # Get the device buffer size.
    cBufMax = c_int()
    dwf.FDwfAnalogInBufferSizeInfo(hdwf, 0, byref(cBufMax))
    print("Device buffer size: "+str(cBufMax.value)) 
    # Set sampling frequency
    dwf.FDwfAnalogInFrequencySet(hdwf, c_double(sam_freq))
    # Set buffer size
    dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(buf_size))
    # Enable all channels
    dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(-1), c_bool(True))
    # Setting voltage range to 10mV
    dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(0.001))
    # Setting filter to decimate
    dwf.FDwfAnalogInChannelFilterSet(hdwf, c_int(-1), 0)
    # Waiting for setting to reflect
    time.sleep(2)
    print("Completed setting up ADC")

def acquire_demod(buf_size, num_samples=300):
    print("Starting radio...")
    sts = c_byte() # Device status
    dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))
    while True:
        try:
            long_sample = []
            # Collect all samples
            for i in range(num_samples):
                while True:
                    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
                    if sts.value == 2:
                        break
                rgdSamples = (c_double*buf_size)()
                dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, c_int(buf_size))
                long_sample.append(rgdSamples)
            # Convert into numpy array and flatten it
            am_mod_data = np.asarray(long_sample)
            am_mod_flat = np.reshape(am_mod_data, -1)
            # Amplify by multiplication
            am_mod_amp = 100 * am_mod_flat
            # Square law detector
            # 1. Square the signal to invert negative side
            am_data_sq = am_mod_amp ** 2
            # 2. Downsample by reshaping and averaging
            am_dwn_sam = am_data_sq.reshape(-1, 16).mean(axis=1)
            # 3. Recover audio by square root
            am_aud = np.sqrt(am_dwn_sam)
            # Convert into wav array
            aud = np.int16(am_aud / np.max(np.abs(am_aud)) * 32767)
            # Play it with sound device
            sd.play(aud, 44100)
        except KeyboardInterrupt:
            print("Stopping radio...")
            dwf.FDwfDeviceCloseAll()
            exit()       


if __name__ == "__main__":
    # Set the library
    dwf = cdll.LoadLibrary("libdwf.so")
    hdwf = c_int()  # Device handle
    buf_size = 8192 # Buffer size
    sam_freq = 850000.0
    init()
    setup_adc(sam_freq=sam_freq)    
    acquire_demod(buf_size)
        
