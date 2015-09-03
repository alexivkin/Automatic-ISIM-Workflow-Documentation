'''
Extract ITIM configuration components from an ldif
Give the name of the ldif

Created on March 23, 2012
@author: Alex Ivkin
'''
import base64,sys,re,traceback,os

class LdifParser:

    def __init__(self,filename):
        self.ratingshash={}
        self.filelist={}
        self.ldif=filename
        #namehash={}

    def parseOut(self):
        print "Loading ldif ...",
        i=0
        try:
            ldiffile = open(self.ldif,'r')
            entry={}
            key=''
            for fullline in ldiffile:
                line=fullline.strip()
                if line=='': # end of an entry
                    if 'objectclass' in entry: # if it is correct
                        self.analyzeEntry(entry)
                    entry={}
                elif line.startswith("#"): # comment
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
                    if len(entry[key]) == 1:
                        entry[key]=[entry[key][0]+line]
                    else:
                        # extend the last value
                        entry[key][-1]+=line
                i+=1
                #if i>60009: break
        except IOError:
            print "file open error"
        finally:
            #print self.ratingshash
            print str(i)+" lines read. "
            ldiffile.close()

    def analyzeEntry(self,entry):
        GlobalWorkflowExportFolder='GlobalWorkflows'
        WorkflowExportFolder = 'Workflows'
        PPExportFolder= 'ProvisioningPolicies'
        filepattern=re.compile(r'[\\/:"*?<>|]+') # invalid filename characters on windows
        try:
            name=None
            data=None
            if 'erWorkflowDefinition' in entry["objectclass"]: # Lifecycle workflows
                #ou=workflow,erglobalid=00000000000000000000,ou=PGE,dc=itim,dc=dom
                # check if the guid has already been seen
                dn=entry["dn"][0]
                guid=dn[dn.find("=")+1:dn.find(",")]
#                if guid in workflowhash:
#                    name=GlobalWorkflowExportFolder+"/"+workflowhash[guid]+".xml"
#                else
                name=GlobalWorkflowExportFolder+"/"+(entry["erprocessname"][0] if "erprocessname" in entry else "") \
                    + "_" + (entry["erobjectprofilename"][0] if "erobjectprofilename" in entry else "") \
                    + "_" + (entry["ercategory"][0] if "ercategory" in entry else "") \
                    + "_" + guid +".xml"
                #if 'erxml' in entry:
                data=base64.b64decode(entry['erxml'][0])
                
            if '!erObjectCategory' in entry["objectclass"]: # Operational workflows
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
                    
                    name=WorkflowExportFolder+"/"+name+"_"+entry["erobjectprofilename"]+"_"+entry["ercategory"]+"_"+oid+".xml";
                    print name
                    '''lookup op
                        ou=operations,ou=itim,ou=PGE,dc=itim,dc=dom
                        (objectclass=*)
                    save erxml'''
            if 'erProvisioningPolicy' in entry["objectclass"]: # Provisioinig Policies
                #ou=policies,erglobalid=00000000000000000000,ou=PGE,dc=itim,dc=dom
                name=PPExportFolder+"/"+filepattern.sub("~",entry["erpolicyitemname"][0])+"_"+entry["erglobalid"][0]+".xml";
                data=base64.b64decode(entry['erentitlements'][0])
            if name is not None:
                print "Saving "+ name
		d = os.path.dirname(name)
		if not os.path.exists(d):
        		os.makedirs(d)
                outfile=open(name,'w')
                print >> outfile, data
                outfile.close()
        except:
            print entry
            print "Failure  %s, %s" % (sys.exc_info()[0],sys.exc_info()[1])
            traceback.print_exc()
            sys.exit(2)

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
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    parser=LdifParser(sys.argv[1])
    parser.parseOut()
