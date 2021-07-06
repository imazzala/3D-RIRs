# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 08:27:57 2021

@author: Yo
"""
import numpy as np
from tkinter import sys
from scipy import signal
from scipy.ndimage import median_filter
from scipy.stats import linregress, zscore
import math
import matplotlib.pyplot as plt
import soundfile as sf
import pandas as pd

"Preparo las señales por un lado el canal mono es W y dejo separado LyR para IACC"
#Corte de la señal
def cut(W,Y,fs):
    """Recorto A partir del pico hasta el final
    In:
    -Canal W formato B ambisonics
    -Canal Y formato B ambisonics 
    -Fs 
    Out:
    -Canal W formato B ambisonics ya recortado a partir del pico
    -Canal Y formato B ambisonics ya recortado a partir del pico
    """
        
    W_max = np.where(abs(W) == np.max(abs(W)))[0]  #Ventana a partir del max
    W_max = int(W_max[0])
    Wcortada = W[(W_max)+5:]
    
    if len(Wcortada) / fs > 10: #Recorto en 10 seg en caso de que sea demasiado largo el archivo
        Wcortada = Wcortada[0:int(10 * fs)] 
    
    Y_max = np.where(abs(Y) == np.max(abs(Y)))[0]  #Ventana a partir del max
    Y_max = int(Y_max[0])
    Ycortada = Y[(Y_max)+5:]
    
    if len(Ycortada) / fs > 10: #Recorto en 10 seg en caso de que sea demasiado largo el archivo
        Ycortada = Ycortada[0:int(10 * fs)]     
     
    if  len(Ycortada)>len(Wcortada):
        Ycortada = Ycortada[0:len(Wcortada)]
    else:
        Wcortada = Wcortada[0:len(Ycortada)]
        
    return Wcortada, Ycortada    

# Señal omnidireccional y estereo
def stereo(Wc,Yc):
    """Obtengo L y R
    In:
        -Canal W formato B ambisonics ya recortado a partir del pico
        -Canal Y formato B ambisonics ya recortado a partir del pico
    Out:
        -R stereo
        -L stereo
    """
    IR_L = np.array(Wc) + np.array(Yc)
    IR_R = np.array(Wc) - np.array(Yc)
    
    return IR_L, IR_R

# Filtro de octava y tercio de octava
def filtroter(Wc, IR_L, IR_R, fs, divi):
    
    """
    Pasabando Butterworth con centros de tercios o octava dado por "divi"
    Wcortada = RIR
    IR_L
    IR_R
    fs = sample rate
    divi = 1 para tercios y = 0 para octava
    
    Devuelve 
    - señal Filtrada (primero los tercios o las octava y ultimo del array el canal w cortado)
    - L para IACC
    - R para IACC
    -array de centros
    
    Basado en la norma: UNE-EN 61260
    """
    

    RIRS = np.vstack((Wc, IR_L, IR_R))
    
    for i in range(len(RIRS)):
       
        W= np.flip(RIRS[i]) #Invierto la rir
        G = 10**(3/10)

        if divi == 1:
            centrosHZ = np.array([25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315,
                                           400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150,
                                           4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000])
               
            fmin = G ** (-1/6)
            fmax = G ** (1/6)
            fil=[]
        else:
            centrosHZ = np.array([31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000])
            
            fmin = G ** (-1/2)
            fmax = G ** (1/2)
            fil=[]
        
        for j,fc in enumerate(centrosHZ):
            sup = fmax*fc/(0.5*fs) #Limite superior de la banda
            
            if sup >= 1:
                    #sup = 0.999999
                    sup = 0.5 * fs - 1    
            inf = fmin * fc / (0.5*fs) #Límite inferior
    
        # Aplico el filtro IIR Butterworth de orden N
            sos = signal.butter(N=2, Wn=np.array([inf,
                                                  sup]), btype='bandpass',output='sos')
            filt = signal.sosfilt(sos, W)  # Filtro W
            fil.append(filt) 
            fil[j] = np.flip(fil[j])
            fil[j]=fil[j][:int(len(fil[j])*0.95)] #Corto el último 5% de la señal para minimiza el efecto de borde
        if i == 0 :
            filtrada = np.vstack((fil, RIRS[i][:len(fil[0])]))
        elif i == 1    :
            filtradaL = np.vstack((fil, RIRS[i][:len(fil[0])]))
        else:
            filtradaR = np.vstack((fil, RIRS[i][:len(fil[0])]))
            
    return filtrada, filtradaL, filtradaR, centrosHZ

# Calculo del tiempo de transición y el EDTt.
def ttyedtt(x,y,fs):
    """Calculo Tt y EDTt
        In:
    -RIR filtrada
    -Fs 
    Out:
    -Tt
    -EDTt
    """ 
    """ Tt se define como el tiempo que tarda una RIR en llegar al 99% de su energia. """
    EDTt = []
    Tt=[]
    for i in range(len(x)):
        ir=x[i]
        ir = ir[int(5e-3 * fs):]  # Descarto 5ms
      
        # ir_max = np.where(abs(ir) == np.max(abs(ir)))[0]  #Ventana a partir del max
        # ir_max = int(ir_max[0])
        # ir = ir[(ir_max)+5:]
        
        index = np.where(np.cumsum(ir ** 2) <= 0.99 * np.sum(ir ** 2))[0][-1]  # Encuentro los indices hasta llagar al 99%
        t_t = index / fs
        Tt.append(t_t)
        #Tt[i] = np.round(Tt,2)
        
        ir2 = y[i]
        #ir2 = 10 * np.log10(ir2 / max(ir2) + sys.float_info.epsilon)
        ir2 = ir2[:index]  # IR despues de filtrar con filtro de mediana movil
    
        t_Tt = np.arange(0, len(ir2) / fs, 1/fs)
        if len(t_Tt) > len(ir2):
            t_Tt = t_Tt[:len(ir2)]
        
        #Cuadrados minimos
        A = np.vstack([t_Tt, np.ones(len(t_Tt))]).T
        m, c = np.linalg.lstsq(A, ir2, rcond=-1)[0]  # Coeficiente m y c
        
        edt_t = -60/m
        EDTt.append(edt_t)
        #EDTt = np.round(EDTt,2)
    EDTt = np.round(EDTt,2)
    Tt = np.round(Tt,2)
    return Tt, EDTt

#Mediana movil a partir de ventana ingresada por el usuario
def mediana_movil(x,vent,fs,p):
    v = int(vent*fs/1000)
    if v % 2 == 0:
        v +=1
    #filt = signal.medfilt(x,v)
    filt = median_filter(x,v)
    if not p == 0:
        filt = np.concatenate((filt, np.zeros(p)))
    else:
        pass
    with np.errstate(divide='ignore', invalid='ignore'):
        filt = 10*np.log10(filt / np.max(filt))
    return filt

#Lundeby
def lundeby(x, fs):
    """Given IR response "y" and samplerate "Fs" function returns upper integration limit of
    Schroeder's integral. Window length in ms "Ts" indicates window sized of the initial averaging of the input signal,
    Luneby recommends this value to be in the 10 - 50 ms range."""

    energia = x
    media = np.zeros(int(len(x) / fs / 0.01))
    eje_tiempo = np.zeros(int(len(x) / fs / 0.01))
    #Divido en intervalos y obtengo la media
    t = math.floor(len(energia) / fs / 0.01)
    v = math.floor(len(energia) / t)

    for i in range(0, t):
        media[i] = np.mean(energia[i * v:(i + 1) * v])
        eje_tiempo[i] = math.ceil(v / 2) + (i * v)

    # Calculo nivel de ruido del ultimo 10% de la señal
    rms_dB = 10 * np.log10(
        np.sum(energia[round(0.9 * len(energia)):]) / (0.1 * len(energia)) / max(energia))
    mediadB = 10 * np.log10(media / max(energia))

    # Se busca la regresión lineal del intervalo de 0dB y la media mas proxima al ruido + 10dB.
    r = int(max(np.argwhere(mediadB > rms_dB + 10)))
    if np.any(mediadB[0:r]<rms_dB+10):
        r = min(min(np.where(mediadB[0:r]<rms_dB+10)))
    if np.all(r==0):
        r=10
    elif r<10:
        r=10
    #Cuadrados minimos
    A = np.vstack([eje_tiempo[0:r], np.ones(len(eje_tiempo[0:r]))]).T
    m, c = np.linalg.lstsq(A, mediadB[0:r], rcond=-1)[0]
    cruce = (rms_dB-c) / m
    #Relacion señal a ruido insuficiente
    if rms_dB > -20:
        punto = len(energia)
        C = None
    else:
        # Comienza proceso iterativo
        error = 1
        INTMAX = 50
        veces = 1
        while error > 0.0001 and veces <= INTMAX:

            #Calcula nuevos intervalos de tiempo para la media, con apro. p cada 10 dB.
            p = 10  # Numero de pasos cada 10dB
            delta = abs(10 / m)  # Numero de muestras por la pendiente de decaimiento de 10dB
            v = math.floor(delta / p)  # Intervalo para obtener la media
            t = math.floor(len(energia[0:round(cruce-delta)])/v)
            if t<2:
                t=2
            elif np.all(t==0):
                t=2

            media = np.zeros(t)
            eje_tiempo = np.zeros(t)
            for i in range(0, t):
                media[i] = sum(energia[i * v:(i + 1) * v]) / len(energia[i * v:(i + 1) * v])
                eje_tiempo[i] = math.ceil(v / 2) + (i * v)
            mediadB = 10 * np.log10(media / max(energia))
            A = np.vstack([eje_tiempo, np.ones(len(eje_tiempo))]).T
            m, c = np.linalg.lstsq(A, mediadB, rcond=-1)[0]

            #Nueva media de energia de ruido, comenzando desde desde el punto de la linea de 
            #decaimiento, 10 dB por debajo del punto de cruce
            noise = energia[(round(abs(cruce + delta))):]
            if len(noise) < round(0.1 * len(energia)):
                noise = energia[round(0.9 * len(energia)):]
            rms_dB = 10 * np.log10(sum(noise)/ len(noise) / max(energia))

            # Nuevo punto de cruce
            error = abs(cruce - (rms_dB - c) / m) / cruce
            cruce = round((rms_dB - c) / m)
            veces += 1
    # output
    if cruce > len(energia):
        punto = len(energia)
    else:
        punto = cruce
    C = max(energia) * 10 ** (c / 10) * np.exp(m / 10 / np.log10(np.exp(1)) * cruce) / (
                -m / 10 / np.log10(np.exp(1)))
    return punto, C

#EDT, T20, T30
def RT_parameters(x,fs):
    """Calculo EDT T20 T30 C50 C80, Normalizo La RIR y calculo filtro de mediana movil 
        In:
    -RIR filtrada
    -Fs 
    Out:
    -EDT
    -T20
    -T30
    
    """
    EDT = []
    T20 = []
    T30 = []
    for i in range(len(x)):
        ir = x[i]
        t = np.arange(0, len(ir) / fs, 1 / fs)
        # Busco maximo
        i_max = np.where(ir == max(ir))               
        y = ir[int(i_max[0][0]):]
        # Valores entre -1 y -10dB
        i_edt = np.where((y <= max(y) - 1) & (y > (max(y) - 10)))
        # Valores entre -5 y -25dB
        i_20 = np.where((y <= max(y) - 5) & (y > (max(y) - 25)))    
        # Valores entre -5 y -35dB
        i_30 = np.where((y <= max(y) - 5) & (y > (max(y) - 35)))    
        
        # Regresión lineal
        t_edt = np.vstack([t[i_edt], np.ones(len(t[i_edt]))]).T
        t_20 = np.vstack([t[i_20], np.ones(len(t[i_20]))]).T
        t_30 = np.vstack([t[i_30], np.ones(len(t[i_30]))]).T
    
        y_edt = y[i_edt]
        y_t20 = y[i_20]
        y_t30 = y[i_30]
    
        m_edt, c_edt = np.linalg.lstsq(t_edt, y_edt, rcond=-1)[0]       
        m_t20, c_t20 = np.linalg.lstsq(t_20, y_t20, rcond=-1)[0] 
        m_t30, c_t30 = np.linalg.lstsq(t_30, y_t30, rcond=-1)[0] 
        #Parametros
        edt = -60 / m_edt                              
        t20 = -60 / m_t20
        t30 = -60 / m_t30
        
        EDT.append(edt)
        T20.append(t20)
        T30.append(t30)
    EDT = np.round(EDT,2)
    T20 = np.round(T20,2)
    T30 = np.round(T30,2)
    
    return EDT, T20, T30

#Claridad    
def C_parameters(x,fs,lb):
    C50 = []
    C80 = []   
    for i in range(len(x)):
        y = x[i]
        z = lb[i]
        t50 = np.int64(0.05*fs)  # Index of signal value at 50 ms
        t80 = np.int64(0.08*fs)  # Index of signal value at 80 ms
        
        y50_num = y[0:t50]
        y50_den = y[t50:z]
        y80_num = y[0:t80]
        y80_den = y[t80:z]
    
        c50 = 10*np.log10(np.sum(y50_num) / np.sum(y50_den))
        c80 = 10*np.log10(np.sum(y80_num) / np.sum(y80_den))
        C50.append(c50)
        C80.append(c80)
    C50 = np.round(C50,2)
    C80 = np.round(C80,2)
    return C50, C80

# Shroeder
def schroeder(x,p):
    z = x
    sch = np.cumsum(x[::-1])[::-1]
    if not p == 0:
        sch = np.concatenate((sch, np.zeros(p)))
    else:
        pass
    with np.errstate(divide='ignore', invalid='ignore'):
        sch_db = 10.0 * np.log10(sch / np.max(sch))
    return sch_db

#Energia y normalización
def E_norm(x):
    #Eneria y normalización
    norm = np.zeros((len(x),len(x[0])))  # Normalization of signal
    for i in range(len(x)):
        E=x[i]**2
        norm[i] = E/np.max(E)
    return norm

#IACCe
def IACC_e(L, R, fs):
    
    """Calculo la IACC de mi RIR estereo segun ISO 3382:2001. 
    Inputs:
    - IR_L: Impulse response in left channel.
    - IR_R: Impulse response in right channel.
    - fs: Sampling frequency of IR signals.
    Outputs:
    - IACCearly: 0 - 80 ms.    
    """

    IACCe =[]
    for i in range(len(L)):
        
        ir_L = L[i]
        ir_R = R[i]
        
        t80 = np.int64(0.08*fs)
        I = np.correlate(ir_L[0:t80], ir_R[0:t80])/(np.sqrt(np.sum(ir_L[0:t80]**2)*np.sum(ir_R[0:t80]**2)))
        iacce = np.max(np.abs(I))
        IACCe.append(iacce)
    IACCe = np.round(IACCe,2)
        
    return IACCe

#Graficos

# def graphs(ir,sm,fs,smooth):
#     fig = plt.figure(figsize=(6.4, 4.8))
#     ax = fig.add_subplot()
#     t = np.arange(0, len(ir) / fs, 1 / fs)
#     t = t[:len(ir)]
#     ax.plot(t, ir, label='Impulse Response')
#     if smooth == 0:
#         ax.plot(t, sm, label='Schroeder Decay')
#     elif smooth == 1:
#         ax.plot(t, sm, label='Mov. Median Filter Decay ')
#     ax.set_xlabel('Time [s]')
#     ax.set_ylabel('Level [dB]')
#     ax.set_ylim([-100, 3])
#     ax.legend()
#     return fig, ax

def ac_parameters(divi,trunc,smooth,vent,W, Y, fs):
    #data, fs = sf.read(path)
    #ir = np.transpose(data)
    #W,Y = cut(ir[0],ir[1],fs)
    W,Y = cut(W, Y, fs)
    IR_L, IR_R = stereo(W,Y)
    # Filtro de octava y tercio
    mono, L, R, cen = filtroter(W, IR_L, IR_R, fs, divi)
    # Guardo variables
    ir_f = mono
    # Energía y normalización
    mono = E_norm(mono)
    mono_dB = 10 * np.log10(np.abs(mono) + sys.float_info.epsilon)
    #Calculo de parámetros
        # Truncamiento de la RI
    ir_tr =[]
    ir_sm=[]
    lb=[]
    for i in range(len(mono)):
        if trunc == 0: #Lundeby
            punto_cruce,c=lundeby(mono[i],fs)
            lb.append(punto_cruce)
            ir_tr.append(mono[i][:punto_cruce])
            p = mono[i].size-punto_cruce
        else:
            ir_tr.append(mono[i])
            punto_cruce = mono.size
            lb.append(punto_cruce)
            p = 0
        # Suavizado
        if smooth == 0:
            sch = schroeder(ir_tr[i],p)
            ir_sm.append(sch)
        elif smooth == 1:
            mmf = mediana_movil(ir_tr[i],vent,fs,p)
            ir_sm.append(mmf)
    
    Tt,EDTt = ttyedtt(ir_tr,ir_sm,fs)
    EDT,T20,T30 = RT_parameters(ir_sm,fs)
    C50,C80 = C_parameters(mono,fs,lb)
    IACCe = IACC_e(L, R, fs)
    #fig,ax=graphs(mono_dB[-1],ir_sm[-1],fs,smooth)
    return (Tt, EDTt, C50,C80,EDT,T20,T30,IACCe, mono_dB, ir_sm)

def table(Tt, EDTt, C50,C80,EDT,T20,T30,IACCe,divi):
    import pandas as pd
    import numpy as np
    # intialise data of lists.
    data = np.array([EDT[:-1],T20[:-1],T30[:-1],Tt[:-1], EDTt[:-1], C50[:-1],C80[:-1],IACCe[:-1]]).T
    data = np.transpose(data)
    # Create DataFrame
    if divi == 0:
        df = pd.DataFrame(data,index = ['EDT [s]','T20 [s]','T30 [s]','Tt [s]','EDTt [s]','C50[dB]','C80[dB]','IACCe'],
                      columns=['31.5', '63', '125', '250', '500', '1000', '2000', '4000', '8000', '16000'])
        # df.index.name = 'Acoustic Parameters'
        # df.columns.name = 'Frequency [Hz]'
    else:
        df = pd.DataFrame(data,index = ['EDT [s]','T20 [s]','T30 [s]','Tt [s]','EDTt [s]','C50[dB]','C80[dB]','IACCe'],
                      columns=['25', '31.5', '40', '50', '63', '80', '100', '125', '160','200', '250', '315', '400', '500',
                               '630', '800', '1k','1.3k', '1.6k', '2k', '2.5k', '3.2k', '4k', '5k', '6.3k', '8k', '10k', 
                               '12.5k', '16k', '20k'])
        # df.index.name = 'Acoustic Parameters'
        # df.columns.name = 'Frequency [Hz]'
    print(df)
     
    return df

#Prueba
#Definición de variables
#path = r'D:\\Documents\\Python Scripts\\IMA\\Análisis Rirs\\stalbans_b_ortf.wav'
#path = "/Users/ivan/Desktop/3DRirs/RI_soundfield/stalbans_b_ortf.wav"
#divi=0 #Filtro de octava
#divi=1 #Filtro de tercio de octava
#trunc = 0 #Lundeby
#trunc = 1 #None
#smooth = 0 #Schroeder
#smooth = 1 #mmf
#vent = 20 #Tamaño de ventana mmf
#Tt, EDTt, C50,C80,EDT,T20,T30,IACCe,fig = ac_parameters(divi,trunc,smooth,vent,path)
#data = table(Tt, EDTt, C50,C80,EDT,T20,T30,IACCe,divi)



        
        
    
