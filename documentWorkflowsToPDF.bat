@echo off
rem Runs the PDF builder. Set approrpiate paths here
rem 2010 (c) Alex Ivkin
rem v2.0
SETLOCAL
rem set JAVA_HOME="c:\Program Files\Java\jre1.5.0"
set JAVA_HOME="F:\Program Files\ibm\itim\jre\jre"
rem set CLASSPATH=%CLASSPATH%;F:\install\saxonb9-1-0-8j\
set CLASSPATH=%CLASSPATH%;F:\apiscript\Lib\saxon9he.jar
set PATH=%JAVA_HOME%\bin\;%PATH%;F:\Program Files\Graphviz2.26.3\bin
rem set SAXON-XSLT=java net.sf.saxon.Transform
F:\jython2.5.1\bin\jython.bat documentWorkflowsToPDF.py %1 %2
