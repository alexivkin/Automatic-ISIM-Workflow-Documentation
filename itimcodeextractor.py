#!/usr/bin/python
'''
Extract ITIM configuration components from an ldif
Give the name of the ldif

There are three options to extract the ITIM config data:

1. Dump the whole ldap (preferable):

/opt/IBM/ldap/[version]/sbin/db2ldif -o f:\temp\ldapdump.ldif

This file can get big, but it compresses well.
2. Use ldapsearch to export specific entries (limits the size of the export, but will miss some details)

ldapsearch -h host -D cn=admin -w password -s sub (objectclass=erServiceItem) > ldapexport-services.ldif
ldapsearch -h host -D cn=admin -w password -s sub (objectclass=erProvisioningPolicy) > ldapexport-pp.ldif
ldapsearch -h host -D cn=admin -w password -s sub (objectclass=erWorkflowDefinition) > ldapexport-workflows.ldif
ldapsearch -h host -D cn=admin -w password -s sub (objectclass=erRole) > ldapexport-roles.ldif
ldapsearch -h host -D cn=admin -w password -s sub (objectclass=*) -b ou=itim,ou=[company],dc=itim,dc=dom > ldapexport-conf.ldif

(the last item includes erServiceProfile, erObjectCategory from ou=category,ou=itim,ou=[company],dc=itim,dc=dom,  erTemplate from ou=config,ou=itim,ou=[company],dc=itim,dc=dom, erFormTemplate from ou=formTemplates,ou=itim,ou=[company],dc=itim,dc=dom and many other)

3. Use your preferred LDAP browser's export ability to save the following (note that dc=itim,dc=dom is a root suffix and may be different depending on how ITIM was set up initially):

    (objectclass=erServiceItem) from ou=services,erglobalid=00000000000000000000,ou=[company],dc=itim,dc=dom
    (objectclass=erProvisioningPolicy) from ou=policies,erglobalid=00000000000000000000,ou=[company],dc=itim,dc=dom
    (objectclass=erWorkflowDefinition) from ou=workflow,erglobalid=00000000000000000000,ou=[company],dc=itim,dc=dom
    (objectclass=erRole) from ou=roles,erglobalid=00000000000000000000,ou=[company],dc=itim,dc=dom
    (objectclass=*) from ou=itim,ou=[company],dc=itim,dc=dom

Todo: add PrettyTable
from prettytable import PrettyTable
sudo apt-get install python-prettytable

2012-2016
@author: Alex Ivkin
'''
import base64,sys,re,traceback,os, pprint, operator

class LdifParser:

    def __init__(self,filename):
        self.ratingshash={}
        self.filelist={}
        self.ldif=filename
        if os.path.dirname(filename) == "": # create subfolders under the same dir that the ldif is in or the current dir
            self.GlobalWorkflowExportFolder='GlobalWorkflows'
            self.WorkflowExportFolder = 'Workflows'
            self.PPExportFolder= 'ProvisioningPolicies'
            self.ALExportFolder= 'AssemblyLines'
        else:
            self.GlobalWorkflowExportFolder = os.path.dirname(filename)+'/GlobalWorkflows'
            self.WorkflowExportFolder = os.path.dirname(filename)+'/Workflows'
            self.PPExportFolder = os.path.dirname(filename)+'/ProvisioningPolicies'
            self.ALExportFolder = os.path.dirname(filename)+'/AssemblyLines'
        #DataReport='datareport.txt'
        self.drf=open(os.path.splitext(filename)[0]+".stats",'w')
        self.accounts={}
        self.services={}
        self.people={}
        self.roles={}
        self.ppolicies={}
        self.other={}
        self.serviceprofiles={'eritimservice':'Built-in'} # init in with a default entry
        #self.ALs={}
        #namehash={}

    def parseOut(self):
        print "Parsing ldif",
        i=0
        try:
            ldiffile = open(self.ldif,'r')
            entry={}
            key=''
            plaintext=False;
            try:
                for fullline in ldiffile:
                    line=fullline.rstrip('\n\r') # keep spaces but remove EOLs
                    if not plaintext and not entry and line.startswith("erglobalid="):
                        plaintext=True;
                        print "plaintext format ",
                    if plaintext: # ldapsearch plaintext format
                        if re.match("erglobalid=.*DC=COM$",line): # analyze old and start a new entry
                            if entry:
                                if 'objectclass' in entry and "ou=recycleBin" not in entry['dn'][0] : # if it is a valid entry and not in the trash
                                    self.analyzeEntry(entry)
                                entry={}
                            entry['dn']=[line]
                        elif re.match(r"[a-zA-Z]+=",line):
                            (key,value)=line.split("=",1)
                            key=key.lower() # ldap is case insensitive
                            value=value.strip("=")
                            if key in entry:
                                entry[key].append(value)
                            else:
                              entry[key]=[value]
                        elif len(entry) > 0: # tag line onto the last value
                            #line=line.lstrip(' ') # remove the leading space
                            if len(entry[key]) == 1:
                                entry[key]=[entry[key][0]+line]
                            else:
                                entry[key][-1]+=line # extend the last value
                        else:
                            print "Error: ", line
                    else: # classical format (softerra, db2ldif)
                        if line=='': # end of an entry
                            if 'objectclass' in entry and "ou=recycleBin" not in entry['dn'][0] : # if it is a valid entry and not in the trash
                                self.analyzeEntry(entry)
                            entry={}
                        elif line.startswith("#"): # skip comment
                            continue
                        elif ":" in line:
                            (key,value)=line.split(":",1)
                            key=key.lower() # ldap is case insensitive
                            value=value.strip(": ")
                            if key in entry:
                                # convert to a set
                                entry[key].append(value)
                            else:
                                entry[key]=[value]
                        elif len(entry) > 0: # tag line onto the last value
                            line=line.lstrip(' ') # remove the leading space
                            if len(entry[key]) == 1:
                                entry[key]=[entry[key][0]+line]
                            else:
                                # extend the last value
                                entry[key][-1]+=line
                    i+=1
                    #if i>60009: break
                    if not i%100000:
                        sys.stdout.write(".")
            except:
                print "\nFailure pasing \"%s\" for %s\n%s, %s" % (line, entry, sys.exc_info()[0],sys.exc_info()[1])
                traceback.print_exc()
                sys.exit(2)

            if plaintext: # plaintext parser is backfilling, need to process the last entry
                if 'objectclass' in entry and "ou=recycleBin" not in entry['dn'][0]:
                    self.analyzeEntry(entry)
            # second pass to fill in the values the first pass missed
            print " remapping ...",
            # servicetypes do not backreference well, so we do a second pass and readability conversion right here
            #print self.serviceprofiles
            #print self.services
            for (k,v) in self.services.items():
                if v[1] in self.serviceprofiles:
                    serviceclass=self.serviceprofiles[v[1]]
                    if serviceclass == 'com.ibm.itim.remoteservices.provider.itdiprovider.ItdiServiceProviderFactory':
                        serviceclass='TDI'
                    elif serviceclass == 'com.ibm.itim.remoteservices.provider.feedx.InetOrgPersonToTIMxPersonFactory':
                        serviceclass='LDAPPersonFeed'
                    elif serviceclass == 'com.ibm.itim.remoteservices.provider.manualservice.ManualServiceConnectorFactory':
                        serviceclass='Manual'
                    elif serviceclass == 'com.ibm.itim.remoteservices.provider.feedx.ADToTIMxPersonFactory':
                        serviceclass='ADPersonFeed'
                    elif serviceclass == 'com.ibm.itim.remoteservices.provider.feedx.CSVFileProviderFactory':
                        serviceclass='CSV'
                    self.services[k][6]=serviceclass
            # print collected stats
            print " saving ...",
            # pprint.pprint(self.services,stream=self.drf)
            #for (k,v) in self.services.items():
            #    print >> self.drf, "".join([str(v[0]).ljust(50),str(v[1]).ljust(40),str(v[2]).ljust(10)])
            sorted_services=sorted(self.services.items(),key=operator.itemgetter(1)) # sort by service name
            print >> self.drf, "".join(["Service Name".ljust(50),"Service type (class)".ljust(40),"URL".ljust(50),"Active".ljust(10),"Suspended".ljust(10),"Orphans".ljust(10)])
            for (k,v) in sorted_services:
                print >> self.drf, "".join([str(v[0]).ljust(50),(str(v[1])+' ('+str(v[6])+')').ljust(40),str(v[2]).ljust(50),str(v[3]).ljust(10),str(v[4]).ljust(10),str(v[5]).ljust(10)])
            print >> self.drf
            # print people stats
            pplcount=[0,0,0]
            for (k,v) in self.people.items():
                pplcount[0]+=1
                pplcount[1 if v[1]=='0' else 2]+=1
                # add people counts to roles
                for r in v[2]:
                    if r in self.roles:
                        self.roles[r][2]+=1
            print >> self.drf, "".join(["People".ljust(50),"Active".ljust(10),"Suspended".ljust(10)])
            print >> self.drf, "".join([str(pplcount[0]).ljust(50),str(pplcount[1]).ljust(10),str(pplcount[2]).ljust(10)])
            print >> self.drf
            # print roles
            print >> self.drf, "".join(["Role".ljust(50),"Description".ljust(50),"Members".ljust(10)])
            sorted_roles=sorted(self.roles.items(),key=operator.itemgetter(1)) # sort by service name
            for (k,v) in sorted_roles:
                print >> self.drf, "".join([v[0].ljust(50),v[1].ljust(50),str(v[2]).ljust(10)])
            print >> self.drf
            # print provisioning policies
            for (k,v) in self.ppolicies.items():
                if v[0] is not None: # convert role dns to names
                    rolelist=[]
                    for role in v[0]: # loop over req targets
                        if role[2:].lower() in self.roles:
                            rolelist.append(self.roles[role[2:].lower()][0]) # convert dn to name
                        else:
                            rolelist.append(role[2:])
                    self.ppolicies[k][0]=rolelist
                if v[1] is not None: # convert service dns to service names
                    svclist=[]
                    for service in v[1]: # loop over req targets
                        if service[2:].lower() in self.services:
                            svclist.append(self.services[service[2:].lower()][0]) # convert dn to name
                        else:
                            svclist.append(service[2:])
                    self.ppolicies[k][1]=svclist
                if v[2] is not None: # convert services in target types to service names
                    svclist=[]
                    for service in v[2]: # loop over req targets
                        if service[2:].lower() in self.services:
                            svclist.append(self.services[service[2:].lower()][0]) # convert dn to name
                        else:
                            svclist.append(service[2:])
                    self.ppolicies[k][2]=svclist
            # sort
            sorted_ppolicies=sorted(self.ppolicies.items(),key=operator.itemgetter(0)) # sorted by key
            print >> self.drf, "".join(["Provisioning Policy".ljust(50),"Entitlements".ljust(100),"Targets".ljust(50)])
            for (k,v) in sorted_ppolicies:
                print >> self.drf, "".join([k.ljust(50),str(",".join(v for v in v[0]) if v[0] is not None else '').ljust(100),str(",".join(v for v in v[1]) if v[1] is not None else ",".join(v for v in v[2]) if v[2] is not None else '').ljust(50)])
                # prints either v[2] or v[3] but not both - a shortcut that works 99% of the tame (cause targets are usually either services, or service types but not both, usually)
            print >> self.drf, "\n\nOther entries in the LDIF:"
            pprint.pprint(self.other,stream=self.drf)
        except IOError:
            print "can't open %s!" % self.ldif
        else:
            #print self.ratingshash
            print str(i)+" lines read. "
            ldiffile.close()

    def analyzeEntry(self,entry):
        filepattern=re.compile(r'[\\/:"*?<>|]+') # invalid filename characters on windows
        try:
            name=None
            data=None
            entryObjectclass=[o.lower() for o in entry['objectclass']]
            if 'erWorkflowDefinition'.lower() in entryObjectclass: # Lifecycle workflows
                #ou=workflow,erglobalid=00000000000000000000,ou=PGE,dc=itim,dc=dom
                # check if the guid has already been seen
                dn=entry["dn"][0]
                guid=dn[dn.find("=")+1:dn.find(",")]
#                if guid in workflowhash:
#                    name=GlobalWorkflowExportFolder+"/"+workflowhash[guid]+".xml"
#                else
                name=self.GlobalWorkflowExportFolder+"/"+(entry["erprocessname"][0] if "erprocessname" in entry else "") \
                    + "_" + (entry["erobjectprofilename"][0] if "erobjectprofilename" in entry else "") \
                    + "_" + (entry["ercategory"][0] if "ercategory" in entry else "") \
                    + "_" + guid +".xml"
                #if 'erxml' in entry:
                data=base64.b64decode(entry['erxml'][0])
                self.save(name,data)
            #if 'erServiceProfile' in entry["objectclass"]: # service profile
            #    'eraccountclass'
            #    'ercustomclass'
            elif 'erALOperation'.lower() in entryObjectclass:
                filename="%s-%s-%s" % (re.search('ou=(.+),ou=assembly',entry["dn"][0]).group(1),entry['eroperationnames'][0],entry['cn'][0])
                name=self.ALExportFolder+"/"+filepattern.sub("~", filename)+".cfg"
                data=base64.b64decode(entry['eralconfig'][0])
                self.save(name,data)
                name=self.ALExportFolder+"/"+filepattern.sub("~", filename)+".xml"
                data=base64.b64decode(entry['erassemblyline'][0])
                self.save(name,data)
            elif 'erServiceProfile'.lower() in entryObjectclass: # service
                serviceprofilename=entry['ercustomclass'][0]
                serviceclass=entry['erserviceproviderfactory'][0] if 'erserviceproviderfactory' in entry else 'Native/DAML' # '''','.join(entry['erproperties'])
                self.serviceprofiles[serviceprofilename.lower()]=serviceclass
            elif 'erServiceItem'.lower() in entryObjectclass: # service
                servicetype=",".join([t for t in entryObjectclass if t != "erServiceItem".lower() and t != "top" and t != "erManagedItem".lower() and t != "erAccessItem".lower() and t != "erRemoteServiceItem".lower()])
                servicedn=entry['dn'][0].lower()
                serviceurl=entry['erurl'][0] if 'erurl' in entry else entry['host'][0] if 'host' in entry else entry['ersapnwlhostname'][0] if 'ersapnwlhostname' in entry else entry['eroraservicehost'][0] if 'eroraservicehost' in entry else ''
                serviceclass=self.serviceprofiles[servicetype] if servicetype in self.serviceprofiles else ''
                #print servicedn
                if servicedn not in self.services:
                    self.services[servicedn]=[entry["erservicename"][0],servicetype,serviceurl,0,0,0,serviceclass] # name, type, active,  suspended ,  orphan
                else: # overwrite the guessed name and service type, but keep the account counters
                    self.services[servicedn][0]=entry["erservicename"][0]
                    self.services[servicedn][1]=servicetype
                    self.services[servicedn][2]=serviceurl
                    self.services[servicedn][6]=serviceclass
            elif 'erAccountItem'.lower() in entryObjectclass: # service
                #accounttype="+".join([t for t in entry["objectclass"] if t != "erAccountItem" and t!="top" and t!="erManagedItem" and t!="erRemoteServiceItem"])
                #if accounttype not in self.accounts:
                #    self.accounts[accounttype]=1
                #else:
                #    self.accounts[accounttype]+=1
                #print >> self.drf, "Account "+entry["eruid"][0]+" type "+",".join([t for t in entry["objectclass"] if t != "erAccountItem" and t!="top" and t!="erManagedItem" and t!="erRemoteServiceItem"])
                if 'erservice' not in entry:
                    print "Missing erservice in "+entry['eruid'][0]
                    return
                servicedn=entry['erservice'][0].lower()
                #if 'eraccountstatus' not in entry: # this is probably an orphan - ignore for now
                #    return # can further check if thats an oprhan by doing
                accountstatus=entry['eraccountstatus'][0] if 'eraccountstatus' in entry else ''
                if servicedn not in self.services: # we found an account before we found a serveice
                    serviceuid=re.search('erglobalid=(.+),ou=services',servicedn).group(1)
                    # blank type
                    servicetype='--' # ''",".join([t for t in entryObjectclass if t != "erManagedItem".lower() and t!="top" and t!="erAccountItem".lower()])
                    # get the service uid for now
                    if "ou=orphans," in entry['dn'][0]:
                        self.services[servicedn]=[serviceuid,servicetype,'',0,0,1,'']
                    elif accountstatus=='0': # active if 0
                        self.services[servicedn]=[serviceuid,servicetype,'',1,0,0,'']
                    else:
                        self.services[servicedn]=[serviceuid,servicetype,'',0,1,0,'']
                    #print "unmapped account " + entry["eruid"][0]
                else:
                    if "ou=orphans," in entry['dn'][0]:
                        self.services[servicedn][5]+=1
                    elif accountstatus=='0': # active if 0, suspended if 1
                        self.services[servicedn][3]+=1
                    else:
                        self.services[servicedn][4]+=1
            elif '---erObjectCategory'.lower() in entryObjectclass: # Operational workflows
                #ou=category,ou=itim,ou=PGE,dc=itim,dc=dom
                #ou=objectProfile,ou=itim,ou=PGE,dc=itim,dc=dom
                #ou=serviceProfile,ou=itim,ou=PGE,dc=itim,dc=dom - (objectclass=*)
                for erxml in entry['erxml']:
                    name = None
                    dn = None
                    decodederxml=base64.b64decode(entry['erxml'][0])
                    bitsnpieces=decodederxml.split("\"")
                    for i in range(len(bitsnpieces)):
                        if name is None and bitsnpieces[i].find(" name=")!=-1:
                            name=bitsnpieces[i+1]
                        if dn is None and bitsnpieces[i].find(" definitionDN=")!=-1:
                            dn=bitsnpieces[i+1]
                        if name is not None and dn is not None:
                            break
                    #if name is None or dn is None:
                    #    raise AssertionError("Missing name or DN")
                    oid=dn[dn.find("=")+1:dn.find(",")]

                    name=self.WorkflowExportFolder+"/"+name+"_"+entry["erobjectprofilename"]+"_"+entry["ercategory"]+"_"+oid+".xml";
                    print name
                    '''lookup op
                        ou=operations,ou=itim,ou=PGE,dc=itim,dc=dom
                        (objectclass=*)
                    save erxml'''
            elif 'erProvisioningPolicy'.lower() in entryObjectclass: # Provisioinig Policies
                #ou=policies,erglobalid=00000000000000000000,ou=PGE,dc=itim,dc=dom
                name=self.PPExportFolder+"/"+filepattern.sub("~",entry["erpolicyitemname"][0])+"_"+entry["erglobalid"][0]+".xml";
                data=base64.b64decode(entry['erentitlements'][0])
                self.ppolicies[entry["erpolicyitemname"][0]]=[entry["erpolicymembership"],entry["erreqpolicytarget"] if 'erreqpolicytarget' in entry else None,
                                                                entry["erpolicytarget"] if 'erpolicytarget' in entry else None]
                ''' for erpolicymembership:

                    for erpolicytarget:
                    If a service instance is targeted, the value is the string representing the service instance's DN. Format: 1;<value>
                    If a service profile is targeted, the value is the name of the service profile. Format: 0;<value>
                    If all services are targeted, the value is * . Format: 2;<*>
                    If a service selection policy is targeted, the value is the name of the service profile affected by the service selection policy. Format: 3;<value>

                    erreqpolicytarget contains prerequisites in the same format
                '''
                self.save(name,data)
            elif 'erPersonItem'.lower() in entryObjectclass: # person
                person=[entry['cn'][0], entry['erpersonstatus'][0],[]]
                if 'erroles' in entry:
                    person[2]=[r.lower() for r in entry['erroles']]
                self.people[entry['dn'][0].lower()]=person
            elif 'erRole'.lower() in entryObjectclass: # role
                self.roles[entry['dn'][0].lower()]=[entry['errolename'][0],entry['description'][0] if 'description' in entry else '',0] # last item is a membership counter to be filled later
            else:
                key=", ".join([o for o in sorted(entryObjectclass) if o <> "top" and o <> "ermanageditem"]) # a key to count all other object classes
                if key in self.other:
                    self.other[key]+=1
                else:
                    self.other[key]=1
        except:
            print entry
            print "Failure  %s, %s" % (sys.exc_info()[0],sys.exc_info()[1])
            traceback.print_exc()
            sys.exit(2)

    def save(self,name,data):
        #if name is not None:
        #print "Saving "+ name
        d = os.path.dirname(name)
        if not os.path.exists(d):
            os.makedirs(d)
        outfile=open(name,'w')
        print >> outfile, data
        outfile.close()

'''
-------
forms
ou=formTemplates,ou=itim,ou=PGE,dc=itim,dc=dom
(objectclass=erFormTemplate)
var name=getExternalProperty("FormTemplatesExportFolder")+"\\"+work.getString("erFormName")+".xml";
//if ((new java.io.File(name)).exists()){
//  task.logmsg("ERROR","Workflow was exported already");
//  system.shutdown();
//}
SaveData_blob.connector.setParam("filePath",name);
erxml
-----
mail templates
ou=config,ou=itim,ou=PGE,dc=itim,dc=dom
(objectclass=erTemplate)
var templatename=work.getString("erTemplateName");
var name=getExternalProperty("MailTemplatesExportFolder")+"\\"+work.getString("cn")+(templatename!=null&&templatename.length>0?"_"+templatename:"")+".xml";
//if ((new java.io.File(name)).exists()){
//  task.logmsg("ERROR","Workflow was exported already");
//  system.shutdown();
//}
SaveData_xml.connector.setParam("filePath",name);
task.logmsg("INFO","Saving snapshot to "+name);

erxtml
ersubject
ertext
ertemplatename
erenabled
-------
acls

(eracl=*)
foreach eracl  atribute
convert dns into  names
// cut the pieces off xml and stick them into a multivalued attribute
var roles="";
work.newAttribute("SysRoleDNs").clear();
var bitsnpieces=work.getString("acl").split("<systemRole>");
for(var i=0; i<bitsnpieces.length;i++){
  cutout=bitsnpieces[i].indexOf("</systemRole");
  if (cutout !=-1){
    roledn=bitsnpieces[i].substring(0,cutout);
    // check with the hash first to see if we had encountered the role earlier
    if (hsh.get(roledn) == null){
        hsh.put(roledn, "known");
        work.getAttribute("SysRoleDNs").addValue(roledn);
    }
  }
}
for each SysRoleDNs
lookup the name  dc=itim,dc=dom - (objectclass=erSystemRole)


var containername=null;
var contents=work.getString("acl");
var name=contents.substring(contents.indexOf(" name=")+7,contents.indexOf(" scope=")-1);
var ou=work.getString("containerou");
var o=work.getString("containero");
var dn=work.getString("containerdn");
if (o == null){
    if (ou==null) {
        containername=dn;
        containertype="dn";
    } else {
        containername=ou;
        containertype="ou";
    }
} else {
    containername=o;
    containertype="o";
}
filename=name.replace(/[\\\/\[\]:;\|=,\+\*\?<>\_"]/g,"~"); // sanitize the name
var filename=getExternalProperty("ACLExportFolder")+"\\"+filename+"_"+containertype+"_"+containername+".xml";
//if ((new java.io.File(filename)).exists())
//  system.shutdownAL();
SaveACLAsBlob.connector.setParam("filePath",filename);
task.logmsg("INFO","Saving ACL to "+filename);
save eracl
----------
'''


if __name__ == '__main__':
    # reopen stdout file descriptor with write mode and 0 as the buffer size (unbuffered output)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    sys.argv[1]
    parser=LdifParser(sys.argv[1])
    parser.parseOut()
