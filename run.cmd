@echo off
 if not exist .git\ (
   git init 
   git config  user.email  "neoandrey@yahoo.com"
   git config  user.name   "neoandrey@yahoo.com"
   echo "logs" >>.gitignore
   echo "venv" >>.gitignore
   echo "proxy.txt" >>.gitignore
   git add . 
   git commit -m "Initial Application Commit" 
)

SET proxy_filepath= %cd%\proxy.txt

 echo "Checking proxy path: %proxy_filepath%"
 IF EXIST %proxy_filepath% (

  SET /p proxy_url=<"%proxy_filepath%"
 )  ELSE (

   echo "Please type proxy URL:"
   set /p proxy_url=   
 
 )

set proxy_reset=

IF ["%proxy_url%"] == [] (
 set proxy_reset="true"
)

IF ["%proxy_url%"] == [""] (
 set proxy_reset="true"
)


IF "%proxy_reset%" == "true" (
 SET proxy_url=""
 type NUL > %cd%\proxy.txt
 echo "removing proxy"
 SET  HTTP_PROXY=
 SET  HTTPS_PROXY=
) 

IF NOT "%proxy_reset%" == "true" (
echo  %proxy_url%>%cd%\proxy.txt
echo "setting proxy as:%proxy_url%"
 SET  HTTP_PROXY=%proxy_url%
 SET  HTTPS_PROXY=%proxy_url%
)

powershell  -File  %cd%\run.ps1
pause