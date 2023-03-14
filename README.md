# AdjustableWiFi


This project was created in order to test black-box optimization strategies on a real piece of 
radio-frequency hardware. 

It seems like such a problem may be relevant to modern communication systems with many parameters to vary
and many unpredictable agents sharing the same communication medium.
The software controls the exchange between two SDRs (HackRF software defined radios) working in transmitter and receiver mode respectively.
It chooses between different WiFi channel frequencies, amplification values and demodulator sensitivities. 
As most packets are lost in actual configuration of SDR, WiFi (de)modulator and host PC, the channel rate measurements
are noisy and expensive. So we take advantage of Bayesian Gaussian Process Optimization.  

The project basically consists of 2 parts. 
First part is SDR. GNU radio project for IEEE 802.11 from Bastibl was adapted to control it's parameters externally.
The second part is sequential algorithm which optimizes GNU radio project parameters to reach lowest package loss rate.
Here the 'gp_minimize' function from the 'scikit-optimize' package is employed.

In order to launch the code one needs to take two steps:
1. Start 'wifi_transceiver_patched.grc' in GNU radio. It requires GNU radio 3.10, Bastibl project gr-802.11 installed,
and two Hackrf devices attached to the host PC (or it might be reconfigured to single USRP-device supporting simultaneous reception and transmission).  
2. Execute 'main.py'.  
