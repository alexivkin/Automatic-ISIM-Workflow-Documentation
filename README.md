# Automatic documentation of ISIM Workflows - Jython dependent branch
﻿
*Attention - for the latest version switch to the 'python' branch*

If you worked with the IBM Security Identity Manager's workflows you probably love them and hate them all at the same time. They are quite powerful and flexible, can also be very cumbersome to manage and hard to troubleshoot. This pages shows an elegant solution to keep reigns on your workflows by making them easy to see and analyze.

In other words this page shows you how to visualize ISIM workflows without using ISIM at all.

## How it works
The first thing you need to do is dump SIM and its java applet for workflow editing. They are useless for automation. Instead this process exports ISIMs workflows in their native XML format out of ISIM's LDAP and saves them to a folder.
It does it by using JNDI/LDAP calls directly from the Python script to get to the XMLs.
Now the trick is to convert them from an XML mess into something you can comprehend and turn into a nice network of nodes.

This is where Python, XSLT and GraphViz come into play.
* GraphViz is a visualizaton engine that makes graphics as PDF's, JPG's, PNG', HTML's, you name it, from a simple list of nodes and edges. You give it a graph in its own DOT language and it will draw it out for you.
* XSLT consumes ISIM workflows in the XML format and spits the

## Setup

Requires Java 6, Jython 2.5.1, SAXON v9.0.0.4J+ XSLT processor and GraphViz DOT graph builder v2.20.2+

Usage: ./documentWorkflows.py <name of the folder with exported workflows> [-p|-l]

-p - Produce one pdf per workflow
-l - Leave dot files in place (useful for debugging)

On Windows:
1. ExportOperationalWorkflows and ExportLifecycleWorkflows. One way to  get  it
is to dump the whole ISIM config suffix from the LDAP in  an  LDIF  format  and
feed it to itimcodeextractor.py.  Another  way  is  to  use  specially  crafted
assembly lines that do that (from our other repository)
3. In the command prompt, run the following in succession:
documentWorkflowsToPDF.bat Z:\Data\ISIM\Workflows\Export
documentWorkflowsToPDF.bat Z:\Data\ISIM\GlobalWorkflows\Export
4. The documentation automatically saved to in the WorkflowDocumentation folder where the script is run

On Linux:
python documentWorkflowsToPDF.py Shares/advtimp/Data/ISIM/Workflows/Export
python documentWorkflowsToPDF.py Shares/advtimp/Data/ISIM/GlobalWorkflows/Export

Installation on Ubuntu
jython - on ubuntu 12.04 just get jython from the repo (2.5.1), on previous download and install manually (repo contains 2.2)
sudo aptitude install libsaxonb-java
sudo aptitude install graphviz

Installation on the windows platfor:
1. From the G1\Identity_Management\Media\Tools\ folder
    a. Install graphviz-2.26.3.msi to F:\Program Files\Graphviz2.26.3
    b. Install jython_installer-2.5.1.jar to F:\jython2.5.1 (you may need to install jre such as jre-1_5_0_11-windows-i586-p-iftw first)
    c. Unzip saxonhe9-2-1-1j.zip and copy saxon9he.jar to F:\apiscript\Lib\
4. Copy f:\apiscript\bin\documentWorkflows*, workflow2dot_graph.xslt and workflow2dot_subgraph.xslt files to a desired location
Actual locations are not important as long as you modify documentWorkflowsToPDF.bat to reflect the locations you've used.

## Automating even more?
Sure, why not. Here is an idea:
* Configure the script to work as an HTML server, and configure GraphViz to produce XHTML/PNG pages on demand (with a link to PDFs). This way you have it always available to you in a single place.
