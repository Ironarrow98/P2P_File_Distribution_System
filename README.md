CS 456 A3: Peer-to-peer File Sharing System

Name:
Chenxi Zhang

Introduction:
This application is a P2P file sharing system with a centralized tracker.

Setup:
Each peer require an individual session
Make sure there is a folder called "Shared" with the peer.py, this folder will be the upload and download folder
Make sure the folder called "Shared" is at the same level with the peer.sh

How to run it:
1) Make sure you know your tracker's IP address
   Example Command: curl ifconfig.me
2) Start the tracker first, tracker will produce a file called "port.txt" that contains the tracker's port number
   Example Command: ./tracker.sh
3) Start peers on other sessions (8 peer would be recommend)
   Peer has 3 arguments: tracker's IP, tracker's port number and minimum alive time(in seconds)
   Example Command: ./peer.sh 129.97.167.27 57543 30

Known Error:
1) This program run with "pickle module" and "socket module", in Python 2.x, when used on a TCP socket,
   might return different amount of data from what you might have expected, as they are sliced at packet boundaries.
   Thus may cause an Error from pickle called "raise EOFError".
   This problem happens randomly, thus can be resolved by terminate the current program and re-run the program one more time.
2) The ideal outcome is that every peer gets every other files other than its own file, but it may happen that other peer shutdown before one peer starts the download process
   thus may result one or more peer(s) missing files
