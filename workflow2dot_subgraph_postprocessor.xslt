<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="2.0"  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="http://www.w3.org/1999/xhtml" xmlns:this="http://somenamespace">
<!-- 
Post processor for adding cross-cluster links to help translate ITIM workflow documents into a native dot syntax.
2010 (c) Alex Ivkin
v2.1

Needs a worlflows as a parameter. Uses a $$...$$ notation to be later replaced by a python postprocessor
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
<xsl:template match="text()" priority="2"/>

<xsl:template match="PROCESSDEFINITION"><xsl:apply-templates select="ACTIVITY/IMPLEMENTATION_TYPE/OPERATION"/></xsl:template>

<!-- Lists cross-cluster links go over the nodes to link clusters together -->
<xsl:template match="OPERATION">  "<xsl:value-of select="$WorkflowName"/>-<xsl:value-of select="../../@ACTIVITYID"/>" -> "$$<xsl:value-of select="ENTITY_OPERATION/@ENTITY_REF"/>-<xsl:value-of select="STATIC_OPERATION/@ENTITY_NAME"/>-<xsl:if test="ENTITY_OPERATION/@ENTITY_TYPE"><xsl:value-of select="ENTITY_OPERATION/@ENTITY_TYPE"/></xsl:if><xsl:if test="STATIC_OPERATION/@ENTITY_TYPE"><xsl:value-of select="STATIC_OPERATION/@ENTITY_TYPE"/></xsl:if>-<xsl:value-of select="@OPERATION_NAME"/>$$" [style=dashed,arrowhead=vee];
</xsl:template>

</xsl:stylesheet>

