<?php
defined('BASEPATH') OR exit('No direct script access allowed');

echo "\nAn uncaught Exception was encountered\n\n";
echo "\tType:        ", get_class($exception), "\n";
echo "\tMessage:     ", $message, "\n";
echo "\tFilename:    ", $exception->getFile(), "\n";
echo "\tLine Number: ", $exception->getLine(), "\n";

if (defined('SHOW_DEBUG_BACKTRACE') && SHOW_DEBUG_BACKTRACE === TRUE)
{
	echo "\n\tBacktrace:\n";
	foreach ($exception->getTrace() as $error)
	{
		if (isset($error['file']) && strpos($error['file'], realpath(BASEPATH)) !== 0)
		{
			echo "\t\tFile: ", $error['file'], "\n";
			echo "\t\tLine: ", $error['line'], "\n";
			echo "\t\tFunction: ", $error['function'], "\n\n";
		}
	}
}
