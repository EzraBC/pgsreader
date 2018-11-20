# pgsreader
Read Presentation Graphic Stream (.SUP) files and provide python objects for parsing through the data


Example:

    from pgsreader import PGSReader
    from imagemaker import make_image
    
    pgs = PGSReader('mysubtitles.sup')
    
    # get the first display set (list of segment objects) that contains a palette
    # if it contains a palette display segment, it will likely also contain an
    # object display segment
    display_set = next((ds for ds in pgs.iter_displaysets() if 'PDS' in [s.type for s in ds]))
    
    # get Palette Display Segment
    pds = next((s for s in display_set if s.type == 'PDS'))
    # get Object Display Segment
    ods = next((s for s in display_set if s.type == 'ODS'))
    
    # get the image!
    img = make_image(ods, pds)
    img.save('my_subtitle_image.png')
    img.show()
    
    # get time when image would have been displayed on screen in milliseconds:
    timestamp_ms = ods.presentation_timestamp
    
Extremely alpha, issues and suggestions welcome!
