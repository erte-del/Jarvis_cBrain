-- Jarvis.app: opens Jarvis in the browser. Quit it (from the Dock) to stop Jarvis.
-- Built by scripts/make_app.sh, which fills in __ROOT__ with the project folder.

property jarvisRoot : "__ROOT__"

on run
	try
		do shell script quoted form of (jarvisRoot & "/scripts/start_jarvis.sh")
	on error message
		display dialog "Jarvis couldn't start:" & return & return & message buttons {"OK"} default button 1 with icon caution
		quit
	end try
end run

-- Clicking the Dock icon again just opens the page again.
on reopen
	do shell script "open http://127.0.0.1:8000"
end reopen

on quit
	try
		do shell script quoted form of (jarvisRoot & "/scripts/stop_jarvis.sh")
	end try
	continue quit
end quit
