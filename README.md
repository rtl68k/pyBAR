This branch adds an ILA core to the "mmc3_8chip_eth" firmware in order to help 
understanding details about the interaction between the hardware and the 
STcontrol MMC3-eth branch (STcontrol with Ethernet communication support), 
which can be found at: https://gitlab.cern.ch/rgoncalv/USBpix/tree/MMC3-eth

After adding an ILA core implementation failed during DRC due to "[DRC MDRV-1] 
Multiple Driver Nets". The issue is related with the bidirectional "BUS_DATA" 
nets which with the addition of the ILA core don't get inferred as a MUX anymore. 
The solution was inserting this MUX manually in the code. To control the MUX 
selection all the basil modules that are connected to "BUS_DATA" were modified 
to output a "chip select" signal, as a function of the original bus addressing 
scheme. These modified modules are in the "v2.4.12-ILA" branch of my forked 
basil repository.

There was NO modification to the behavior of the firmware. 
The idea was just to allow the ILA insertion.

This branch was added to my forked version of the repository for backup purposes.

