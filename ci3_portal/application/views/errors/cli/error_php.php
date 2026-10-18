<?php
defined('BASEPATH') OR exit('No direct script access allowed');

echo "\nA PHP Error was encountered\n\n";
echo "\tSeverity: ", $severity, "\n";
echo "\tMessage:  ", $message, "\n";
echo "\tFilename: ", $filepath, "\n";
echo "\tLine Number: ", $line, "\n";

if (defined('SHOW_DEBUG_BACKTRACE') && SHOW_DEBUG_BACKTRACE === TRUE)
{
	echo "\n\tBacktrace:\n";
	foreach (debug_backtrace() as $error)
	{
		if (isset($error['file']) && strpos($error['file'], realpath(BASEPATH)) !== 0)
		{
			echo "\t\tFile: ", $error['file'], "\n";
			echo "\t\tLine: ", $error['line'], "\n";
			echo "\t\tFunction: ", $error['function'], "\n\n";
		}
	}
}
