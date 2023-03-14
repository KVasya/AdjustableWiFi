# AdjustableWiFi


This project was created in order to test black-box optimization strategies on a real piece of 
radio-frequency hardware. 
It seems like such a problem may be relevant to modern communication systems with many parameters to vary
and many unpredictable agents sharing the same communication medium.
The software controls the exchange between two SDRs (HackRF) working in transmitter and receiver mode respectively.
It chooses between different WiFi channel frequencies, amplification values and demodulator sensitivities. 
As most packets are lost in actual configuration of SDR, WiFi (de)modulator and host PC, the channel rate measurements
are noisy and expensive. So we take advantage of Bayesian Gaussian Process Optimization.   
