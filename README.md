# pgsreader
Read Presentation Graphic Stream (.SUP) files and provide python objects for parsing through the data


Example:

    from pgsreader import PGSReader, ObjectDefinitionSegment
    
    pgs = PGSReader('mysubtitles.sup')
    
    rle_bmps = [s.img_data for s in pgs.segments if isinstance(s, ObjectDefinitionSegment)]
    
rle_bmps will be a list of bytestrings containing the RLE-encoded bitmap bytes of images defined in the file.

Extremely alpha, issues and suggestions welcome!
