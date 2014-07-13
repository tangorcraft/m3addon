#!/usr/bin/python3
# -*- coding: utf-8 -*-

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import m3
import sys

lineEnding = '\r\n'
header="""\
/*
 * This script has been generated via the generateMaxSCript.py file of the m3addon.
 *
 * The m3addon can be found at https://github.com/flo/m3addon/
 *
 * Please do not modify this file. Instead improve the m3addon mentioned above and generate it again.
 */

"""

additionalFunctions = """\
fn ReadTag stream tag =
(
    tag = ""

    for i=1 to 4 do
    (
        b = ReadByte stream
        if b != 0 then
        (
           /* Add bytes to the front to reverse order: */
           tag = (bit.IntAsChar(b)) + tag
        )
    )
    return tag
)
fn SkipBytes stream count =
(
    for i=1 to count do
    (
        ReadByte stream
    )
)
"""


parseSectionFunctionFirstPart="""
/*
 * Parses the section described by indexEntry and
 * returns the freshly loaded section
 */
fn ParseSection stream indexEntry sectionContent =
(
    fSeek stream indexEntry.offset #seek_set
    tag = indexEntry.tag
    repetitions = indexEntry.repetitions
    version = indexEntry.version
    sectionContent = #()
    if (tag =="CHAR" and version == 0) then
    (
        sectionContent = ""
        for i=1 to repetitions do
        (
            b = ReadByte stream
            c = bit.IntAsChar(b)
            /* Add bytes to the front to reverse order: */
            sectionContent = sectionContent + c
        )
    )
    else if (tag =="REAL" and version == 0) then
    (
        for i=1 to repetitions do
        (
            f = ReadFloat stream
            append sectionContent f
        )
    )
    else if (tag =="U8__" and version == 0) then
    (
        for i=1 to repetitions do
        (
            intValue = ReadByte stream #unsigned
            append sectionContent intValue
        )
    )
    else if (tag =="I16_" and version == 0) then
    (
        for i=1 to repetitions do
        (
            intValue = ReadShort stream #signed
            append sectionContent intValue
        )
    )
    else if (tag =="U16_" and version == 0) then
    (
        for i=1 to repetitions do
        (
            intValue = ReadShort stream #unsigned
            append sectionContent intValue
        )
    )
    else if (tag =="I32_" and version == 0) then
    (
        for i=1 to repetitions do
        (
            intValue = ReadLong stream #signed
            append sectionContent intValue
        )
    )
    else if (tag =="U32_" and version == 0) then
    (
        for i=1 to repetitions do
        (
            intValue = ReadLong stream #unsigned
            append sectionContent intValue
        )
    )
"""
parseSectionFunctionElIfPart="""\
    else if (tag=="%(structureName)s" and version == %(structureVersion)s) then
    {
        for i=1 to repetitions do
        (
            value = %(functionName)s stream
            append value
        )
    }
"""
parseSectionFunctionLastPart="""\
    else
    (
        echo "Unsupported section " + tag + "V" + version
        throw "Unsupported section " + tag + "V" + version
    )
)
"""


footer ="""

fn ParseSections file sections =
(
    stream = fOpen file "rb"
    
    header = ParseMD34V11 stream
    
    /* Load index entries */
    fSeek stream header.indexOffset #seek_set
    indexEntries = #()
    for i=1 to header.indexSize do
    (
        indexEntry = ParseMD34IndexEntryV0 stream
        append indexEntries indexEntry
    )
    sections = #()
    for i=1 to header.indexSize do
    (
        indexEntry = indexEntries[i]
        
        section = ParseSection stream indexEntry
        append sections section

    }
    fClose stream
)

fn ResolveSections sections =
(
    for i=1 to (length sections) do
    (
        section = sections[i]
        ResolveSection section sections
    )
)

fn LoadModelTree file modelTree =
(
    sections = ParseSections file
    
    ResolveSections sections

    headerSection = section[0]
    header = headerSection[0]
    
    modelTree = header.model
)

"""

def getMaxStructureName(structureDescription):
    structureName = structureDescription.structureName
    structureVersion = structureDescription.structureVersion
    
    maxStructName = "%sV%s" % (structureName, structureVersion)
    return maxStructName

def getMaxParseFunctionName(structureDescription):
    maxStructName = getMaxStructureName(structureDescription)
    maxFunctionName = "Parse" + maxStructName
    return maxFunctionName

def getMaxResolveFunctionName(structureDescription):
    maxStructName = getMaxStructureName(structureDescription)
    maxFunctionName = "Resolve" + maxStructName
    return maxFunctionName


def writeStructureDefinition(out, structureDescription):
    structureName = structureDescription.structureName
    structureVersion = structureDescription.structureVersion
    
    maxStructName = getMaxStructureName(structureDescription)
    out.write("struct ")
    out.write(maxStructName)
    out.write(lineEnding)
    out.write("( ")
    out.write(lineEnding)
    for fieldIndex, field in enumerate(structureDescription.fields):
        if fieldIndex != 0:
            out.write(",")
            out.write(lineEnding)
        out.write("    ")
        out.write(field.name)
    out.write(lineEnding)
    out.write(")")
    out.write(lineEnding)


def writeParseStructureFunction(out, structureDescription):
    structureName = structureDescription.structureName
    structureVersion = structureDescription.structureVersion
    
    maxFunctionName = getMaxParseFunctionName(structureDescription)
    maxStructName = getMaxStructureName(structureDescription)
    out.write("fn %s stream result =  " % maxFunctionName)
    out.write(lineEnding)
    out.write("(")
    out.write(lineEnding)
    out.write("    result = %s()" % maxStructName)
    out.write(lineEnding)
    
    for field in structureDescription.fields:
        if isinstance(field, m3.TagField):
            out.write("result.%s = ReadTag stream" % field.name)
        elif isinstance(field,m3.PrimitiveField):
            typeString = field.typeString
            if typeString == "float":
                out.write("    result.%s = ReadFloat stream" % field.name)
            elif typeString == "uint32":
                out.write("    result.%s = ReadLong stream #unsigned" % field.name)
            elif typeString == "uint16":
                out.write("    result.%s = ReadShort stream #unsigned" % field.name)
            elif typeString == "uint8":
                out.write("    result.%s = ReadByte stream #unsigned" % field.name)
            elif typeString == "int32":
                out.write("    result.%s = ReadLong stream #signed" % field.name)
            elif typeString == "int16":
                out.write("    result.%s = ReadShort stream #signed" % field.name)
            elif typeString == "int8":
                out.write("    result.%s = ReadByte stream #signed" % field.name)
            elif typeString == "fixed8":
                out.write("    result.%s = ((ReadByte stream #unsigned) / 255.0 * 2.0) -1 " % field.name)
            else:
                raise Exception("Unsupported primitive type %s")
        elif isinstance(field, m3.UnknownBytesField):
            out.write("    SkipBytes stream %d /* Skip unknown field %s */" %(field.size, field.name))
        elif isinstance(field, m3.ReferenceField):
            parseFunctionName = getMaxParseFunctionName(field.referenceStructureDescription)
            out.write("    result.%s =  %s stream" % (field.name,parseFunctionName))
        elif isinstance(field, m3.EmbeddedStructureField):
            parseFunctionName = getMaxParseFunctionName(field.structureDescription)
            out.write("    result.%s = %s stream" % (field.name,  parseFunctionName))
        else:
            raise Exception("Unsupported field type: %s" % type())
        out.write(lineEnding)

    out.write(" )")
    out.write(lineEnding)
    out.write(lineEnding)

"""
Return a list of all field paths that need to be resolved
"""
def findPropertiesToResolve(structureDescription):
    for field in structureDescription.fields:
        if isinstance(field, m3.ReferenceField):
            yield field.name

        if isinstance(field, m3.EmbeddedStructureField):
            fieldPathPrefix = field.name + "."
            for subProp in findPropertiesToResolve(field.structureDescription):
                yield fieldPathPrefix + subProp

def writeResolveSectionFunction(out, structureDescriptionList):
    
    out.write("fn ResolveSection section sections =")
    out.write(lineEnding)
    out.write("(")
    out.write(lineEnding)
    firstIf = True
    for structureDescription in structureDescriptionList:
        propPathList = list(findPropertiesToResolve(structureDescription))
        if len(propPathList) > 0:
            out.write('    ')
            if not firstIf:
                out.write('else ')
            out.write('if (tag == "%s" and version == %s) then' % (structureDescription.structureName, structureDescription.structureVersion))
            out.write(lineEnding)
            out.write("    (")
            out.write(lineEnding)
            out.write("        for i=1 to (length section) do")
            out.write(lineEnding)
            out.write("        (")
            out.write(lineEnding)
            out.write("            obj = section[i]")
            out.write(lineEnding)
            for propPath in propPathList:
                out.write("            obj.%(propPath)s = sections[obj.%(propPath)s.index]" %{"propPath":propPath})
                out.write(lineEnding)
            out.write("        )")
            out.write(lineEnding)
            out.write("    )")
            out.write(lineEnding)
            firstIf = False
  
    out.write(")")
    out.write(lineEnding)
    out.write(lineEnding)


def iterateStructureDescriptions():
    for structureName, structureHistory in  m3.structures.items():
        for structureDescription in structureHistory.getAllVersions():
            yield structureDescription


def generateParseSectionFunction(out, structureDescriptionList):
    out.write(parseSectionFunctionFirstPart)
    for structureDescription in structureDescriptionList:
        structureName = structureDescription.structureName
        structureVersion = structureDescription.structureVersion
        functionName = getMaxParseFunctionName(structureDescription)
        out.write(parseSectionFunctionElIfPart %  {"structureName":structureName, "structureVersion":structureVersion, "functionName":functionName})
    out.write(parseSectionFunctionLastPart)
    

def generateMaxScript(out):
    
    out.write(header)
    
    structureDescriptionList = list(iterateStructureDescriptions())
    for structureDescription in structureDescriptionList:
        writeStructureDefinition(out, structureDescription)

    out.write(lineEnding)
    out.write(lineEnding)
    
    out.write(additionalFunctions)

    for structureDescription in structureDescriptionList:
        writeParseStructureFunction(out, structureDescription)
    
    generateParseSectionFunction(out, structureDescriptionList)
    
    writeResolveSectionFunction(out, structureDescriptionList)
    
    out.write(footer)



if __name__ == "__main__":
   generateMaxScript(sys.stdout)