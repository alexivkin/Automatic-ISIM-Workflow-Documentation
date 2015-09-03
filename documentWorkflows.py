#!/usr/bin/python
""" Automatic documentation for all workflows
2015 (c) Alex Ivkin
v3.0
Requires GraphViz DOT graph builder, the lxml (python interface to libxml2) and saxonb (XSLT2 subgrph processing)

Installing:
On ubuntu run
sudo aptitude install graphviz python-lxml libsaxonb-java

Usage: python documentWorkflows.py <name of the folder with exported workflows> [-p|-l]

-p - Produce one pdf per workflow
-l - Keep intermediate dot files (useful for debugging)

Use PowerTools, or the bundled export script to export workflows from the LDAP/LDIF in an xml format

"""
import sys,os,datetime,traceback, time
from lxml import etree
import re

def main():
    if not os.path.isdir(sys.argv[1]):
        print "No such directory - "+sys.argv[1]
        sys.exit(2)
    scriptdir=sys.path[0]
    xmldir=sys.argv[1]
    destdir='WorkflowDocumentation' #scriptdir+'/WorkflowDocumentation' #xmldir+'/../../
    if not os.path.isdir(destdir):
        os.mkdir(destdir)
        #print destdir+" does not exit!"
        #sys.exit(2)
        print "Created "+destdir
    if len(sys.argv)>2 and sys.argv[2]=='-p':
        oneper=1
    else:
        oneper=0
    if len(sys.argv)>2 and sys.argv[2]=='-l':
        leavefiles=1
    else:
        leavefiles=0
    count=0
    workflowcount=len(os.listdir(xmldir))
    # prep the XSLT
    #sys.stdout.write("Loading stylesheets...")
    #sys.stdout.flush()

    #tfactory=TransformerFactory.newInstance("net.sf.saxon.TransformerFactoryImpl",None) # force Saxon over Xalan
    #xslt=tfactory.getConfiguration().buildDocument(StreamSource(scriptdir+"/workflow2dot_subgraph.xslt")) #new File(xslID)
    #transformer=tfactory.newTemplates(xslt).newTransformer()
    #try:
    #    l=etree.parse(scriptdir+"/workflow2dot_subgraph.xslt")
    #    transformer=etree.XSLT(l)
    #except etree.XSLTParseError, e:
    #    print e.error_log
    #    exit(10)
    #posttfactory=TransformerFactory.newInstance("net.sf.saxon.TransformerFactoryImpl",None)
    #postxslt=posttfactory.getConfiguration().buildDocument(StreamSource(scriptdir+"/workflow2dot_subgraph_postprocessor.xslt"))
    #posttransformer=posttfactory.newTemplates(postxslt).newTransformer()
    #posttransformer=etree.XSLT(etree.parse(open(scriptdir+"/workflow2dot_subgraph_postprocessor.xslt",'rb')))
    #print "done"

    # locate all files and group into sets
    fullname={}
    shortname={}
    category={}
    rootcategory={}
    refwftitle={'unknown':'dynamic reference'} # keeps track of referenced workflows by an XSLT key. A generic reference for an unknown state
    reference={} # all workflows referenced from this one
    #propertitle={}
    for xmlfile in [f for f in os.listdir(xmldir) if os.path.isfile(xmldir+"/"+f)]:
        count+=1
        sys.stdout.write("\rAnalyzing workflows...%d%%"%(int(count*100/workflowcount)))
        sys.stdout.flush()
        #name=os.path.splitext(os.path.normcase(xmlfile))[0]
        name=os.path.splitext(xmlfile)[0]
        wfname=name.split('_')
        if len(wfname)==1:
            wfname.append('ITIM')
            wfname.append('Global')
        elif wfname[1]=='' or wfname[1] is None:
            wfname[1]='Generic'
        #wftitle="Type: %s Entity: %s Operation: %s" % (wfname[2],wfname[1],wfname[0])
        wftype="%s-%s"%(wfname[1],wfname[2])
        wftitle="%s %s %s"%(wfname[1],wfname[2],wfname[0])
        fullname[wftitle]="%s/%s"%(xmldir,xmlfile)
        shortname[wftitle]=name
        #print "Native category for "+wftitle+" is "+wftype
        #category[wftitle]={wftype:True} # linking the native workflow category
        rootcategory[wftitle]=wftype # linking the native workflow category
        #propertitle[name]=wftitle
        # process workflow content to find all referenced workflows
        #xmldoc=(DocumentBuilderFactory.newInstance()).newDocumentBuilder()
        try:
            doc=etree.parse(open(fullname[wftitle],'r'))
            objs=doc.findall("ACTIVITY")
            # find all referenced workflows and add them to the proper group
            for obj in objs:
                imptypes=obj.findall("IMPLEMENTATION_TYPE")
                for imptype in imptypes:
                    ops=imptype.findall("OPERATION")
                    for op in ops:
                        opname=op.get("OPERATION_NAME")
                        #refname=opname+"_"
                        entityref=''
                        entitytype=''
                        static=op.findall("STATIC_OPERATION")
                        if len(static) > 0:
                            entityname=static[0].get("ENTITY_NAME")
                            entitytype=static[0].get("ENTITY_TYPE")
                            if entityname=='' or entityname is None:
                                entityname='Generic'
                        else: # entity operationis not so easy - we need to get the type of the referenced data object
                            entityname='Generic'
                            entityop=op.findall("ENTITY_OPERATION")
                            entityref=entityop[0].get("ENTITY_REF")
                            if entityref is None or entityref=='':
                                entitytype=entityop[0].get("ENTITY_TYPE")
                                if entitytype is None or entitytype=='': # this is then a rarely used ENTITY_EXP thingy
                                    continue # just skip it
                            else:
                                relevantitems=doc.findall("RELEVANT_DATA")
                                for rd in relevantitems:
                                    if rd.get("RELEVANT_DATA_ID")==entityref:
                                        entitytype=rd.get("TYPE")
                                        break
                                if entitytype=='':
                                    print "Wrong reference to %s in %s"%(entityref,name)
                            #refname="_"+entitytype
                        #reftype="%s-%s"%(entityname,entitytype)
                        reftitle="%s %s %s"%(entityname,entitytype,opname)
                        #print "Referencing "+reftitle+" to "+wftype + " from "+wftitle
                        if wftitle in reference:
                            reference[wftitle][reftitle]=True # add the reference
                        else:
                            reference[wftitle]={reftitle:True} # hash of hashes to weed out dupes
                        # remember the proper name of the workflow
                        # the key is intentionaly botched up to mimic what is happening inside of the XSLT
                        refwftitle[('' if entityref is None else entityref)+"-"+('' if entityname=='Generic' else entityname)+"-"+('' if (entityref is not None and entityref !='') else entitytype)+"-"+opname]=reftitle # hash proper name from a rough XSLT abbreviation
        except Exception,  e:
            print "can not parse %s "%name
            #print etree.tostring(op)
            traceback.print_exc()
            print e
            exit(1)
    print "\rAnalyzing workflows...100%%...done"

    # process the linked list to add parent categories to all referenced worflows (for them to show up in the same graph)
    #print str(reference)
    def categorize_chain(parentwf,parentwftype):
        #print "Walking down "+parentwf+" for "+parentwftype
        # first add the native category
        if wf in category:
            category[wf][parentwftype]=True
            category[wf]['Everything']=True
        else:
            category[wf]={parentwftype:True,'Everything':True}
        if parentwf in reference: # if it references something
            for ref in reference[parentwf].keys(): # for all referenced workflows
                #for parentwftype in parentwftypes.keys(): # add all possible parent types
                if ref in category:
                    category[ref][parentwftype]=True # linking the non native workflow into a parent category
                else:
                    category[ref]={parentwftype:True} # hash of hashes to weed out dupes
                # todo check for loops in wf references
                categorize_chain(ref,parentwftype) # recurse into children nodes
    count=0
    for wf in rootcategory.keys():
        count+=1
        #print "Linking %s" % wf
        percent=int(count*100/len(rootcategory.keys()))
        sys.stdout.write("\rLinking workflows...%d%%"%(percent))
        sys.stdout.flush()
        categorize_chain(wf, rootcategory[wf])
    print "...done"

    #print str(category)
    #print str(shortname)
    #print "Categories: " + str(category.values())
    #print refwftitle

    # print warnings first
    for wftitle in category.keys():
        if wftitle not in shortname:
            print "The %s workflow is referenced, but one of the files in the %s folder. Skipping." % (wftitle,xmldir)
    # process files
    count=0
    wfout={} # a hash of file handles
    postbuilder={} # hash to track file endings
    for wftitle in category.keys():
        if wftitle not in shortname:
            continue
        name=shortname[wftitle]
        # process all types a wf can belong do
        count+=1
        percent=int(count*100/len(category.keys()))
        if not oneper: #os.path.isfile("WorkflowDocumentation/%s.dot" % wftype):
            for wftype in category[wftitle].keys():
                #print "adding "+wftitle+" to "+wftype
                if wftype not in wfout: # create file if needed
                    wfout[wftype]=open('%s/%s.dot' % (destdir,wftype),'w')
                    #page="11,8.5";\n  size="10,7.5!";\n
                    dotheader='digraph g {\n  size="100.0,35.0"; fontsize="10.0"; rankdir=LR; splines=polyline; node [shape=box, style=filled];\n'  #aspect="1.0"; size="11.0,17.0";orientation=landscape;ratio=auto;page="8,10.5";
                    dotlegend="""
  subgraph "cluster_Legend" {
    label="Node color legend"; labelloc="t";
    node [fontname="Sans",fontsize=7,width=0.7,height=0.2]
    Script [fillcolor=plum]
    "Start/Stop"  [fillcolor=peachpuff]
    Operation [fillcolor=khaki]
    Function [fillcolor=darkorange]
    Loop [fillcolor=red]
    "Manual activity" [fillcolor=greenyellow]
    Other [fillcolor=white]
    Script -> "Start/Stop" -> Operation -> Function -> Loop -> "Manual activity" -> Other [color=transparent]
  }
"""
                    print>>wfout[wftype],dotheader
                    print>>wfout[wftype],dotlegend
                    postbuilder[wftype]=""
                sys.stdout.write("\rTransforming workflows to DOT graphs...%d%%"%(percent))
                sys.stdout.flush()
                # build a subgraph using the XSLT 2.0 processor
                #print "Processing %s - %s (%s) " % (wftype, wftitle,fullname[wftitle])
                os.system('saxonb-xslt -s:"%s" -o:"WorkflowDocumentation/%s.dot" -xsl:"%s/workflow2dot_subgraph.xslt" WorkflowName="%s"' % (fullname[wftitle],name,scriptdir,wftitle))
                print>>wfout[wftype],open("WorkflowDocumentation/%s.dot" % name,'r').read()
                if not leavefiles:
                    os.remove('%s/%s.dot' % (destdir,name))
                # build a link between subgraphs (may be empty)
                os.system('saxonb-xslt -s:"%s" -o:"WorkflowDocumentation/%s.link" -xsl:"%s/workflow2dot_subgraph_postprocessor.xslt" WorkflowName="%s"' % (fullname[wftitle],name,scriptdir,wftitle))
                # convert the xslt $$...$$ parameter into the actual subgraph name using the awesome python string/list slicing [3:-3] and the lamba function
                postbuilder[wftype]+=re.sub(r'"\$\$.*\$\$"',lambda match:'"'+refwftitle[(match.group(0)[3:-3] if (match.group(0)[3:-3] in refwftitle) else 'unknown')]+'-START"',open("WorkflowDocumentation/%s.link" % name).read())
                if not leavefiles:
                    os.remove('WorkflowDocumentation/%s.link' % name)
        else:
            print "Processing %s"%wftitle
            # could use the normal XSLT v1 processor as it is faster than Saxon. XSLT 2.0 is not required in this step
            os.system('xsltproc -o "WorkflowDocumentation/%s.dot" --stringparam WorkflowName "%s" "%s/workflow2dot_graph.xslt" "%s/%s"' % (name,wftitle,scriptdir,xmldir,xmlfile))
            #os.system('java net.sf.saxon.Transform -o "%s/%s.dot" "%s/%s" "%s/workflow2dot_graph.xslt" WorkflowName="%s"'%(destdir,name,xmldir,xmlfile,scriptdir,wftitle))
            os.system('dot -Tpdf -o "%s/%s.pdf" "%s/%s.dot"'%(destdir,name,destdir,name))
            if not leavefiles:
                os.remove(destdir+'/%s.dot'%name)
    if not oneper:
        # close out all open files and run the dot
        count=0
        print "...done"
        for (wftype,f) in wfout.items():
            count+=1
            sys.stdout.write("\rConverting DOT graphs to PDFs...%d%%"%(int(count*100/len(wfout.items()))))
            sys.stdout.flush()
            # terminate and close out all files
            print>>f,"\n" + postbuilder[wftype]
            print>>f,'  label="%s Workflows - %s";\n  labelloc="t";\n}'%(wftype,datetime.date.today())# added to the bottom because of a known bug http://www.graphviz.org/mywiki/FaqGraphLabel
            f.close()
            os.system('dot -Tpdf -o "%s/%s.pdf" "%s/%s.dot"'%(destdir,wftype,destdir,wftype))
            if not leavefiles:
                os.remove('%s/%s.dot' % (destdir,wftype))
        print "...done"
        #
        #nodecount=$(grep node "$i.dot" | wc -l)
        #widthlimit=$(($nodecount*100))
        #if widthlimit > 1000:
        #    widthlimit=1000
        #name=$(echo $i | sed s/_[0-9]*\.xml//)
        #echo "<p align=center><object data=\"$i.svg\" width="$widthlimit" type="image/svg+xml"></p><p align=center><b>$name</b></p>">>workflows_documentation.html
        #echo "</body></html>">>workflows_documentation.html
        #timestamp=`date`
        #echo "<html><head><title>ITIM Workflow documentation - $timestamp</title></head><body>">workflows_documentation.html

#=========================================================================================================
if __name__=="main" or __name__=="__main__":
    if len(sys.argv)==1:
        print __doc__
        sys.exit(1)
    main()
