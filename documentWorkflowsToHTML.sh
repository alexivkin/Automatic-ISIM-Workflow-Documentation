#!/bin/bash
# Builds svg's for all workflows and creates an HTTP doc
# 2010 (c) Alex Ivkin
# v2.0
#
# run as $0 infile outfile
#
timestamp=`date`
echo "<html><head><title>ITIM Workflow documentation - $timestamp</title></head><body>">workflows_documentation.html
for i in *.xml ; do
	echo "Processing $i..."
	xsltproc -o "$i.dot" workflow2dot_graph.xslt "$i"
	dot -Tsvg -o "$i.svg" "$i.dot"
	nodecount=$(grep node "$i.dot" | wc -l)
	widthlimit=$(($nodecount*100))
#	if [[ $nodecount -lt 6 ]]; then
#		if [[ $nodecount -lt 4 ]]; then
#			widthlimit=300
#		else
#			widthlimit=500
#		fi
#	else
#		widthlimit=1000
#	fi
	if [[ $widthlimit -gt 1000 ]]; then
		widthlimit=1000
	fi
	#${i:0:${#i}-24}
	name=$(echo $i | sed s/_[0-9]*\.xml//)
	echo "<p align=center><object data=\"$i.svg\" width="$widthlimit" type="image/svg+xml"></p><p align=center><b>$name</b></p>">>workflows_documentation.html
done
echo "</body></html>">>workflows_documentation.html