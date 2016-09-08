<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="2.0"  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="http://www.w3.org/1999/xhtml" xmlns:this="http://somenamespace">
<!-- 
Translates ITIM workflow documents into a native dot syntax.
2010 (C) Alex Ivkin 
v2.1
Needs a worlflows as a parameter
Uses XSLT v2.0 syntax that requires SAXON
-->
<xsl:output method="text"/>
<xsl:param name="WorkflowName">ITIM Workflow</xsl:param>
<xsl:template match="@*|node()">
	<xsl:copy>
		<xsl:apply-templates select="@*|node()"/>
	</xsl:copy>
</xsl:template>
<xsl:template match="*" priority="-1000">
	<xsl:apply-templates/>
</xsl:template>
<!-- swallow comments -->
<xsl:template match="text()" priority="2"/>
<!-- main process template -->
<xsl:template match="PROCESSDEFINITION">  subgraph "cluster_<xsl:value-of select="$WorkflowName"/>" {
	label="<xsl:value-of select="$WorkflowName"/>";
	labelloc="t";
	color="grey";
	nodesep=0.1
	ranksep=0.1
	graph [fontname="Sans Bold",fontsize=10]
	edge  [fontname="Sans Italic",fontsize=7,weight=1.5]
	node  [fontname="Sans",fontsize=7,width=0.7,height=0.2,label=""]
<xsl:apply-templates/>  }
<!-- old code, now in the  post processor <xsl:apply-templates select="ACTIVITY/IMPLEMENTATION_TYPE/OPERATION"/> -->
</xsl:template>

<!-- build nodes 
 old code to show a full name of an operation:
	<xsl:if test="IMPLEMENTATION_TYPE/OPERATION">\n(Call <xsl:value-of select="IMPLEMENTATION_TYPE/OPERATION/ENTITY_OPERATION/@ENTITY_REF"/>-<xsl:value-of select="IMPLEMENTATION_TYPE/OPERATION/STATIC_OPERATION/@ENTITY_NAME"/>-<xsl:value-of select="IMPLEMENTATION_TYPE/OPERATION/STATIC_OPERATION/@ENTITY_TYPE"/>-<xsl:value-of select="IMPLEMENTATION_TYPE/OPERATION/@OPERATION_NAME"/> workflow)</xsl:if>
 to show labels inside the nodes use this:
	node [label="<xsl:value-of select="@ACTIVITYID"/>",fillcolor=<xsl:choose>
    and remove the self-edge after each node
-->
<xsl:template match="ACTIVITY">	node [fillcolor=<xsl:choose>
<xsl:when test="IMPLEMENTATION_TYPE/ROUTE"><xsl:choose><xsl:when test="SCRIPT">plum</xsl:when><xsl:otherwise>peachpuff</xsl:otherwise></xsl:choose></xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/OPERATION/ENTITY_OPERATION/@ENTITY_EXP">plum</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/OPERATION">khaki</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/APPLICATION">darkorange</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/LOOP">red</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/MANUAL">greenyellow</xsl:when>
<xsl:otherwise>white</xsl:otherwise></xsl:choose>] {"<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="@ACTIVITYID"/>"}
        "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="@ACTIVITYID"/>":s -> "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="@ACTIVITYID"/>":s [headlabel="<xsl:value-of select="@ACTIVITYID"/>",fontname="Sans",color=transparent]
</xsl:template>

<!-- build internal transitions -->
<xsl:template match="TRANSITION"><xsl:choose>
	<xsl:when test="TRANSITION_KIND/LOOP_BEGIN">	"<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/LOOP_BEGIN/@FROM_LOOP"/>" -> "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/LOOP_BEGIN/@TO_LOOP"/>" [style=dotted];
</xsl:when>
	<xsl:when test="TRANSITION_KIND/LOOP_END">	"<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/LOOP_END/@FROM_LOOP"/>" -> "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/LOOP_END/@TO_LOOP"/>" [style=dotted];
</xsl:when>
	<xsl:otherwise>	"<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/REGULAR/@FROM"/>" -> "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="TRANSITION_KIND/REGULAR/@TO"/>" [label=<xsl:choose><xsl:when test="TRANSITION_KIND/REGULAR/@CONDITION"><xsl:call-template name="describeTransition">
		<xsl:with-param name="string"><xsl:value-of select="TRANSITION_KIND/REGULAR/@CONDITION"/></xsl:with-param></xsl:call-template></xsl:when><xsl:otherwise><xsl:call-template name="describeTransition">
		<xsl:with-param name="string"><xsl:value-of select="normalize-space(replace(TRANSITION_KIND/REGULAR/SCRIPT,'.*//.*',''))"/></xsl:with-param>
		</xsl:call-template></xsl:otherwise></xsl:choose>,style=bold,arrowhead=vee,arrowtail=odot];
</xsl:otherwise>
</xsl:choose>
</xsl:template>

<!-- switch select template to provide descriptive transition names -->
<xsl:template name="describeTransition">
<xsl:param name="string" />
<xsl:choose>
<xsl:when test="$string='true'">""</xsl:when>
<xsl:when test="$string='false'">inactive,color="gray"</xsl:when> <!-- for the latest versions you can use html markup for italicizing like this &lt;&lt;I&gt;inactive&lt;/I&gt;&gt; -->
<xsl:when test="matches($string,'[!=]=','i')">"<xsl:call-template name="decode"><xsl:with-param name="code"><xsl:value-of select="lower-case($string)"/></xsl:with-param></xsl:call-template>"</xsl:when>
<xsl:otherwise><!-- clean the quotes first, passing on string as string -->"<xsl:call-template name="cleanQuote">
<xsl:with-param name="string">
<xsl:value-of select="$string"/>
</xsl:with-param>
</xsl:call-template>"</xsl:otherwise>
</xsl:choose></xsl:template>

<!-- convert javascript to English -->
<xsl:template name="decode">
<xsl:param name="code" />
<xsl:value-of select="this:color-code(this:replace-multi($code,(
	'process.*?type.*?\s*==\s*&quot;ua&quot;','process.*?type.*?\s*!=\s*&quot;ua&quot;',
	'\.get\(\)\s*==\s*&quot;*([0-9_a-z]+)&quot;*','\.get\(\)\s*!=\s*&quot;*([0-9_a-z]+)&quot;*',
	'activity\.resultsummary\s*==\s*activity\.(\w+)','activity\.resultsummary\s*!=\s*activity\.(\w+)',
	'((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))==&quot;sf&quot;','((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))!=&quot;sf&quot;',
	'((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))==&quot;aa&quot;','((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))!=&quot;aa&quot;',
	'((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))==&quot;ss&quot;','((activity|process)\.resultsummary|workflowruntimecontext\.getactivityresult\(\))!=&quot;ss&quot;',
	'\.get\(\)(;|\s|$)','\.get\(\)\.dn','\.get\(\)\.tolower\(\)\s*==\s*&quot;([0-9_a-z]+)&quot;','\.get\(\)\.tolower\(\)\s*!=\s*&quot;([0-9_a-z]+)&quot;',
	'\.get\(\)\.indexof\(&quot;([0-9_a-z]+)&quot;\)\s*==\s*0','\.get\(\)\.indexof\(&quot;([0-9_a-z]+)&quot;\)\s*!=\s*0',
	'\.get\(\)\.length\s*==\s*0','\.get\(\)\.length\s*>\s*0',
	'&quot;','&amp;&amp;','\|\|'
	),(
	'doing person add','not doing person add',
	' is $1',' is not $1',
	'$1','not $1',
	'failed','not failed',
	'approved','not approved',
	'successful','not successful',
	'','dn',' is $1',' is not $1',
	' starts with $1',' does not start with $1',
	' empty',' not empty',
	'\\&quot;','\\nand','\\nor'
	)))"/>
</xsl:template>

<!-- recursive template that escapes the quotes (the replace function has problems with inner quotes) -->
<xsl:template name="cleanQuote">
<xsl:param name="string" />
<xsl:if test="contains($string, '&#x22;')"><xsl:value-of select="substring-before($string, '&#x22;')" />\"<xsl:call-template name="cleanQuote">
	<xsl:with-param name="string"><xsl:value-of select="substring-after($string, '&#x22;')" /></xsl:with-param></xsl:call-template>
</xsl:if>
<xsl:if test="not(contains($string, '&#x22;'))"><xsl:value-of select="$string" />
</xsl:if>
</xsl:template>

<!-- xslt function to preform multiple replaces -->
<xsl:function name="this:replace-multi" as="xs:string?" >
  <xsl:param name="arg" as="xs:string?"/> 
  <xsl:param name="changeFrom" as="xs:string*"/> 
  <xsl:param name="changeTo" as="xs:string*"/> 
  <xsl:sequence select=" 
   if (count($changeFrom) > 0)
   then this:replace-multi(replace($arg, $changeFrom[1],if (exists($changeTo[1])) then $changeTo[1] else ''),$changeFrom[position() > 1],$changeTo[position() > 1])
   else $arg
 "/>
</xsl:function>

<!-- xslt function to add a color based on an action -->
<xsl:function name="this:color-code" as="xs:string?" >
  <xsl:param name="arg" as="xs:string?"/>
  <!-- The order is important here because of the overlapping match substring. Do not join the ifs -->
  <xsl:sequence select="
	if (matches($arg,'(not submitted|not approved)'))   then concat($arg,'&quot;,color=&quot;brown')
	else if (matches($arg,'(not rejected|not failed)')) then concat($arg,'&quot;,color=&quot;darkgreen')
	else if (matches($arg,'(submitted|approved)'))      then concat($arg,'&quot;,color=&quot;darkgreen')
	else if (matches($arg,'(rejected|failed)'))         then concat($arg,'&quot;,color=&quot;brown')
	else $arg
  "/>
</xsl:function>

</xsl:stylesheet>
