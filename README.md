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
First part is GNU Radio project 'wifi_transceiver_patched.grc'. This project is based on IEEE 802.11 implementation https://github.com/bastibl/gr-ieee802-11 by Bastibl, it  was adapted from the example 'wifi_transceiver.grc' of the project. What I did was connecting Bastibl's example with external Python script. The connection provided control over hardware parameters, and message receive/transmit functionality from external script. 
The second part is external Python script which sequentially  optimizes GNU radio project parameters to reach lowest package loss rate.
Here the 'gp_minimize' function from the 'scikit-optimize' package is employed.

PREREQUISITES

Prerequisites are mainly due to GNU Radio project.
The installation instructions from the base project https://github.com/bastibl/gr-ieee802-11 should be followed. 
The 'gr-ieee802-11' project implies USRP hardware, which was changed by me to UHD (two HackRF devices). Thus also you may need to install UHD.
Optimization part needs Python 3 with 'scikit-optimize' installed.

The code operates in two independent scripts communicating through zmq interface. It was tested on an i5 core machine. It's important for the operation of gr-ieee802-11 that real-time scheduling is
 enabled (it's a project option, it's on by default, but for weaker configurations it might lead to errors). The default 20MHz bandwidth of  gr-ieee802-11
leads to receiver overflow, so it's switched to 5MHz by 'main.py' at it's start.

To launch the project:
0. In 'wifi_transceiver_patched.grc' change serial numbers for UHD devices to those of your devices.
1. Start 'wifi_transceiver_patched.grc' in GNU radio. It requires two Hackrf (UHD) devices attached to the host PC (or it might be reconfigured to single USRP-device supporting simultaneous reception and transmission).  
2. Execute 'main.py'.  
