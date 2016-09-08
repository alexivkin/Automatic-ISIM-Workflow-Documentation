<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- 
Translates ISIM workflow XML documents into the native GraphViz dot syntax.
(C) 2015 Alex Ivkin
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" >
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
	<xsl:template match="text()" priority="2"/>
	<xsl:template match="PROCESSDEFINITION">digraph g {page="11,8.5";size="10,7.5!";splines=polyline; rankdir=LR;
label="<xsl:value-of select="$WorkflowName"/>"; labelloc="t"; 
		<xsl:apply-templates/>}</xsl:template>
	<xsl:template match="ACTIVITY">node [shape=box, style=filled,label="<xsl:value-of select="@ACTIVITYID"/>",fillcolor=<xsl:choose>
<xsl:when test="IMPLEMENTATION_TYPE/ROUTE"><xsl:choose><xsl:when test="SCRIPT">plum</xsl:when><xsl:otherwise>peachpuff</xsl:otherwise></xsl:choose></xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/OPERATION/ENTITY_OPERATION/@ENTITY_EXP">plum</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/OPERATION">khaki</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/APPLICATION">darkorange</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/LOOP">red</xsl:when>
<xsl:when test="IMPLEMENTATION_TYPE/MANUAL">greenyellow</xsl:when>
<xsl:otherwise>white</xsl:otherwise></xsl:choose>] {<xsl:value-of select="@ACTIVITYID"/>}; 
	</xsl:template>
	<xsl:template match="TRANSITION">
<xsl:choose>
<xsl:when test="TRANSITION_KIND/LOOP_BEGIN"><xsl:value-of select="TRANSITION_KIND/LOOP_BEGIN/@FROM_LOOP"/> -> <xsl:value-of select="TRANSITION_KIND/LOOP_BEGIN/@TO_LOOP"/> [style=dotted];</xsl:when>
<xsl:when test="TRANSITION_KIND/LOOP_END"><xsl:value-of select="TRANSITION_KIND/LOOP_END/@FROM_LOOP"/> -> <xsl:value-of select="TRANSITION_KIND/LOOP_END/@TO_LOOP"/> [style=dotted];</xsl:when>
<xsl:otherwise><xsl:value-of select="TRANSITION_KIND/REGULAR/@FROM"/> -> <xsl:value-of select="TRANSITION_KIND/REGULAR/@TO"/> [headport=w, tailport=e, style=bold,arrowhead=vee, arrowtail=odot];</xsl:otherwise>
</xsl:choose>
	</xsl:template>
</xsl:stylesheet>
