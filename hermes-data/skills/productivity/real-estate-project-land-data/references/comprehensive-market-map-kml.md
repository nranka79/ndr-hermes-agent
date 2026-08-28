================================================================================
 COMPREHENSIVE MARKET MAP KML — CREATION & MY MAPS IMPORT
================================================================================
For development proposals, a companion KML (Keyhole Markup Language) file with
all competitor projects, economic drivers, and social infrastructure organized
in layers is a powerful supplement to the written feasibility report.

SOURCE TRIGGERS
  "Add Bidadi My Maps link as interactive map"
  "Update My Maps with all projects"
  "Create a map with..."


WHEN TO CREATE
  • The user asks to "update My Maps" or "add to the map"
  • The development proposal includes competitor/project research that would
    benefit from geospatial visualization
  • You've compiled a list of projects with coordinates and want them
    displayed on an interactive map


WORKFLOW

  1. COLLECT PLACEMARK DATA
     Gather for each entry: name, description (key stats), coordinates (lng,lat).
     Keep descriptions plain-text and under 200 chars — My Maps balloon styles
     work best with simple text. No HTML or CDATA needed.

  2. BUILD THE KML
     Use Python string concat or template (NOT nested functions — avoids
     Python scoping issues with `nonlocal`). Structure:
     ```
     <kml><Document>
       <name>...</name>
       ...styles...
       <Folder><name>Layer Name</name>
         <Placemark>
           <name>Project Name</name>
           <description>Short description</description>
           <styleUrl>#style-id</styleUrl>
           <Point><coordinates>lng,lat,0</coordinates></Point>
         </Placemark>
         ...
       </Folder>
       ...
     </Document></kml>
     ```

  3. VALIDATE XML
     ```
     import xml.etree.ElementTree as ET
     tree = ET.parse('/path/to/file.kml')
     ```
     Fix any well-formedness errors before uploading. Common issues:
     • Unclosed CDATA sections (use plain <description> instead)
     • Unescaped &amp; characters (use xml.sax.saxutils.escape())
     • Emoji characters in element names (strip them for reliability)

  4. CREATE KMZ (preferred for My Maps import)
     ```
     cd /tmp && zip -j output.kmz input.kml
     ```
     My Maps handles KMZ (zipped KML) more reliably than raw KML.

  5. UPLOAD TO DRIVE
     Upload both .kml and .kmz to the user's Drive. Set anyone-with-link
     permission. Delete old versions first to avoid confusion.

  6. DELIVER IMPORT INSTRUCTIONS
     Tell the user to:
     a) Open their My Maps edit URL
     b) Click "⋮ → Import"
     c) Download and select the KMZ/KML file
     d) New layers appear alongside existing data


PITFALLS

  • KML format: My Maps is picky about invalid XML. Always validate before
    uploading. Strip CDATA sections — use plain <description> tags instead.
  • Emojis in names: Some My Maps versions choke on emoji characters in
    folder/placemark names. Use plain-text layer names.
  • Coordinate order: KML uses <coordinates>lng,lat,0</coordinates> (longitude
    FIRST), not the lat,lng order used in Google Maps URLs.
  • File size: My Maps has a 5MB import limit for KML/KMZ. With 50+ simple
    placemarks, file size is typically ~18-25KB — well within limits.
  • Cannot programmatically edit My Maps: There is no public API to add
    placemarks to an existing My Maps layer. The KML import via browser UI
    is the only reliable path.
  • Merging vs replacing: KML import adds NEW layers to the existing map.
    It does not replace or merge into the user's existing layers. The user
    can reorder layers by dragging in the layer panel after import.
  • HTML descriptions: Complex <![CDATA[<b>HTML</b>]]> descriptions in KML
    often fail to render in My Maps balloons. Use plain text descriptions
    for reliability.
