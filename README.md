# Automatic documentation of ISIM Workflows

If you worked with the IBM Security Identity Manager's workflows  you  probably
love them and hate them all at the same time. The workflows are quite  powerful
and flexible, but they can also be  very  cumbersome  to  manage  and  hard  to
troubleshoot. This code is an elegant solution to keep reigns on your workflows
by drawing them in an easy to analyze manner.

In other words this code shows you how to visualize ISIM workflows without using ISIM at all.

Here is an example snapshot of an AD account workflow documentation PDF with the sub workflows (scaled down to fit here).
![](https://github.com/BlueBayTechnologies/Automatic-ISIM-Workflow-Documentation/blob/master/Examples/account-request.png)

Here what a global workflow documentation might look like.
![](https://github.com/BlueBayTechnologies/Automatic-ISIM-Workflow-Documentation/blob/master/Examples/global.png)

## Other features
* itimcodeextractor.py creates a statistics file that shows all services, people, account, role and provisioning policies found in the LDAP
* review_custom_js shows (and potentially patches) old FESI code and old URLs in the custom code

## How it works
The first thing you need know is to avoid ISIM and its workflow editor java applet. They are useless for automation. Instead you need to export ISIM workflows in their native XML format out of ISIM's LDAP.
Then you can run the python script that parses the data, converts it into a graph and produces

## Extracting the data
You can do it in a variaty of ways:
* Use your LDAP browser's export ability to save the following:
	(objectclass=erObjectCategory) from ou=category,ou=itim,ou=[company],dc=itim,dc=dom
	(objectclass=erWorkflowDefinition) from ou=workflow,erglobalid=00000000000000000000,ou=[company],dc=itim,dc=dom
* Run a specially crafted ISDI assembly line that does that (see ISIM PowerTools "extractAll")
* Dump the whole ISIM config suffix from the LDAP in an LDIF format and feed it to itimcodeextractor.py.
	/opt/IBM/ldap/[version]/sbin/db2ldif -o /tmp/ldapdump.ldif
	./itimcodeextractor.py /tmp/ldapdump.ldif
* Write a script to use JNDI/LDAP calls directly to get to the worlkflow XMLs

The next step is to convert them from an XML mess into something you can comprehend and turn into a nice graph. This is where Python, XSLT and GraphViz come into play.

* XSLT processor consumes ISIM workflows in the XML format and spits out the "dot" format for GraphViz
* GraphViz is a visualizaton engine that makes graphics from a simple  list  of
nodes and edges. You give it a graph in its own DOT language and it  will  draw
it out for you as a PDF's, JPG's, PNG', HTML's or many other formats

## Setup

This script requires GraphViz DOT graph builder v2.20 or higher, the lxml (python interface to libxml2) and saxonb XSLT v2 processor

To get the dependancies on ubuntu/debian run
sudo aptitude install graphviz python-lxml libsaxonb-java

*Note:* that this repo also includes a Jython branch that works on the *jython*
engine, rather than python, and uses Java saxon and XML libraries

## Usage

./documentWorkflows.py {name of the folder with exported workflows} [-p|-l]

-p - Produce one pdf per workflow, instead of grouping similar  worflows  on  a
same pdf
-l - Leave dot files in place (useful for debugging)

The documentation automatically saved to in  the  WorkflowDocumentation  folder
where the script is run.

## Automating even more?
Sure, why not. Here is an idea:
* Build workflow extraction routine into the documentation script so you always
get the freshest workflows.
* Configure the script to work as an HTML server, and configure GraphViz to produce XHTML/PNG pages on demand (with a link to PDFs). This way you have it always available to you in a single place.
