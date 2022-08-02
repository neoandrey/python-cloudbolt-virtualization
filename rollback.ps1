cd %cd%
$git = $(git log);
 $gitInfo = $git[0..$git.length]|foreach{$entry=$_.toString().Trim(); if(![string]::isNullOrEmpty($entry)){$entry}};  
$gitInfo
