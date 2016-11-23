Collaborative Text Editor - "Colted"

Team members: Ayobami Ephraim Adewale, Tanel Kiis, Markus Kängsepp

Our project aim was to create basic text editor that enables concurrent editing. Constraints only one user can edit certain line at same time and user can only open his/her own files or available files.


RUNNING THE APPLICATION !!!!!!


1. Running server and then client calling help message
 (assuming your current directory is "DSHomework1")
	python2.7 src/editor_server.py
	python2.7 src/editor_client.py
	(in order to get help use -h)

2. Running unit tests for server and client
 (assuming your current directory is "DSHomework1/tests"). Note while testing make sure that there are no active servers on local host.
	python2.7 -m unittest test_server
	python2.7 -m unittest test_client