import numpy as np
import os
import librosa as lr
import numpy as np
import pandas as pd
from sklearn import preprocessing
from scipy import signal
from glob import glob
from numpy import absolute, arange, log10,pi,convolve,fft
from scipy.signal import kaiserord, lfilter, firwin, freqz,filtfilt


class MainProcessing: 

    def __init__(self, BLD, FLU, BRU, FRD, time, Fs, integration_time):

        self.BLD = BLD
        self.FLU = FLU
        self.BRU = BRU
        self.FRD = FRD
        self.time = time
        self.Fs = Fs
        self.integration_time = integration_time
 

    def A_to_B(self):

        W = self.FLU + self.FRD + self.BLD + self.BRU
        X = self.FLU + self.FRD - self.BLD - self.BRU
        Y = self.FLU - self.FRD + self.BLD - self.BRU
        Z = self.FLU - self.FRD - self.BLD + self.BRU
    
        return W, X, Y, Z


    def intensity(self, W, X, Y, Z):
        
        Fc = 5000
        W_filt,X_filt,Y_filt,Z_filt = self.filter(Fc, W, X, Y, Z)
 
        #W_filt,X_filt,Y_filt,Z_filt = W,X,Y,Z
        #Calculate intensity from directions
        Ix_filt = W_filt*X_filt
        Iy_filt = W_filt*Y_filt
        Iz_filt = W_filt*Z_filt
        Ixv,Iyv,Izv = self.vent_ham(Ix_filt,Iy_filt,Iz_filt,dur = self.integration_time)

        #Cálculo del valor de la Intensidad Total, Azimut y Elevación para obtener
        #las coordenadas esféricas de cada vector

        I = np.sqrt(Ixv**2+Iyv**2+Izv**2)
        az = np.arctan(Iyv/Ixv)
        el = np.arctan(Izv/I)

        #From rad to degrees
        az2 = np.rad2deg(az)
        el2 = np.rad2deg(el)

        return I, az2, el2 

    
    def vent_ham(self, Ix, Iy, Iz, dur):
        
        #Tiempo de integración en ms
        vent = np.round(dur * self.Fs)
        vent = vent.astype(np.int64)
       
        #Busqueda de picos para que venteanee desde allí
        Ix=Ix[np.argmax(Ix):]
        Iy=Iy[np.argmax(Iy):]
        Iz=Iz[np.argmax(Iz):]
        if len(Ix)<len(Iy) and len(Ix)<len(Iz):
            Iy,Iz=Iy[:len(Ix)],Iz[:len(Ix)]
        elif len(Iy)<len(Ix) and len(Iy)<len(Iz):
            Ix,Iz=Ix[:len(Iy)],Iz[:len(Iy)]
        else: 
            Ix,Iy=Ix[:len(Iz)],Iy[:len(Iz)]
        
        # Ventaneo y suma de amplitudes
        Ix_vent=[]
        for i in range(0,len(Ix)-vent):
            Ix_sep = Ix[i:i+vent]
            ham = np.hamming(len(Ix_sep))
            Ix_ham = Ix_sep*ham
            Ix_ham = sum(Ix_ham)
            Ix_vent.append(Ix_ham)
        Ix_vent=np.array(Ix_vent)

        Iy_vent=[]
        for i in range(0,len(Iy)-vent):
            Iy_sep = Iy[i:i+vent]
            ham = np.hamming(len(Iy_sep))
            Iy_ham = Iy_sep*ham
            Iy_ham = sum(Iy_ham)
            Iy_vent.append(Iy_ham)
        Iy_vent=np.array(Iy_vent)    
    
        Iz_vent=[]
        for i in range(0,len(Iz)-vent):
            Iz_sep = Iz[i:i+vent]
            ham = np.hamming(len(Iz_sep))
            Iz_ham = Iz_sep*ham
            Iz_ham = sum(Iz_ham)
            Iz_vent.append(Iz_ham)
        Iz_vent=np.array(Iz_vent)  
        return Ix_vent,Iy_vent,Iz_vent


    def find_peaks(self, I, az, el):

        I_peak = signal.find_peaks(I)#,threshold=0.4)#,prominence=)
        I_peak = I_peak[0]

        #Busco que muestra es la de mayor amplitud
        I_max_amp = np.argmax(I)
        
        # Busco esa muestra dentro de los picos
        I_max_peak= np.where(I_peak == I_max_amp)
        I_max_peak = I_max_peak[0]
        I_max_peak = I_max_peak.item()
        I_peak = I_peak[I_max_peak:]
        
        # Calculo el sonido directo
        #I_direct = I[I_peak[I_max_peak]]

        I_gr = []
        az_gr = []
        el_gr = []
        time_p = []
        time_tr = []
    
        for i in range(0,len(I_peak)):
            A = I[I_peak[i]]
            B = az[I_peak[i]]
            C = el[I_peak[i]]
            D = self.time[I_peak[i]]
    
            I_gr.append(A)
            az_gr.append(B)
            el_gr.append(C)
            time_p.append(D)
        
        for i in range(0,len(time_p)):
            E = time_p[i]
            F = E-time_p[0]
            time_tr.append(F)
         
        I_gr = np.array(I_gr)
        az_gr=np.array(az_gr)
        el_gr=np.array(el_gr)
        time_tr = np.array(time_tr) * (10 ** 3)

        return I_gr, az_gr, el_gr, time_tr    


    @staticmethod
    def intensity2dB(I):
    
        I_dB = []

        for i in range(0,len(I)):
            G = 10*np.log10(I[i]/(10**(-12)))
            I_dB.append(G)
    
        I_dB = np.array(I_dB)

        dbmax = max(I_dB)
        I_dB2=[]

        for i in range(0,len(I_dB)):
            H = I_dB[i]-dbmax
            I_dB2.append(H)
        
        I_dB = I_dB2
        I_dB = np.array(I_dB)
        
        return I_dB


    @staticmethod
    def normalization(I_dB):
        I_norm = []
        Imax = max(I_dB)
        Imin = min(I_dB)
        for i in range(0,len(I_dB)):
            norm = (I_dB[i]-Imin)/(Imax-Imin)
            I_norm.append(norm)
        
        I_norm = np.array(I_norm)

        return I_norm


    def filter(self, Fc, W, X, Y, Z):
        #------------------------------------------------
        # Parameters of the siganl
        #------------------------------------------------
        sample_rate = self.Fs
        nsamples = 400
        t = arange(nsamples) / sample_rate
    
        #------------------------------------------------
        # Create a FIR filter and apply it to x.
        #------------------------------------------------

        # The Nyquist rate of the signal.
        nyq_rate = sample_rate / 2.0

        # The desired width of the transition from pass to stop,
        # relative to the Nyquist rate.  We'll design the filter
        # with a 5 Hz transition width.
        width = 5.0/nyq_rate

        # The desired attenuation in the stop band, in dB.
        ripple_db = 60.0

        # Compute the order and Kaiser parameter for the FIR filter.
        N, beta = kaiserord(ripple_db, width)

        # The cutoff frequency of the filter.
        cutoff_hz = Fc

        # Use firwin with a Kaiser window to create a lowpass FIR filter.
        taps = firwin(N, cutoff_hz/nyq_rate, window=('kaiser', beta))#"hann")

        # Use lfilter to filter x with the FIR filter.
        filtered_w = lfilter(taps, 1.0, W)
        filtered_x = lfilter(taps, 1.0, X)
        filtered_y = lfilter(taps, 1.0, Y)
        filtered_z = lfilter(taps, 1.0, Z)
    
        return filtered_w,filtered_x,filtered_y,filtered_z


    @staticmethod
    def threshold(I,th):

        I_dB=[]

        for i in range(0,len(I)):
            
            if I[i] >= -th:
                a = I[i]
                I_dB.append(a)
            else:
                pass

        I_dB = np.array(I_dB)
        
        return (I_dB)


    @staticmethod
    def polar2cart(I,az,el):

        x = I * np.sin(el) * np.cos(az)
        y = I * np.sin(el) * np.sin(az)
        z = I * np.cos(el)

        return x,y,z

    
    @staticmethod
    def table(time_tr,I_dB,az,el):

        # intialise data of lists.
        data = np.array([time_tr,I_dB,az,el])
        data = np.transpose(data)
        # Create DataFrame
        df = pd.DataFrame(data,columns=['Time [ms]','Magnitude [dB]','Azimuth[°]','Elevation[°]'])
        print(df)
     
        return df