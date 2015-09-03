#!/bin/bash
# Runs the PDF builder. Set approrpiate paths here
# 2012 (c) Alex Ivkin
# v2.0
#set JAVA_HOME="F:\Program Files\ibm\itim\jre\jre"
export CLASSPATH=$CLASSPATH:/usr/share/java/saxonb.jar
#set PATH=%JAVA_HOME%\bin\;%PATH%;F:\Program Files\Graphviz2.26.3\bin
#set SAXON-XSLT=java net.sf.saxon.Transform
# assume all components are in the same folder
/usr/bin/jython $(dirname $0)/documentWorkflowsToPDF.py $1 $2
