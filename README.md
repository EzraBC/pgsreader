# pgsreader
Read Presentation Graphic Stream (.SUP) files and provide python objects for parsing through the data


Example:

    from pgsreader import PGSReader
    from imagemaker import make_image
    
    pgs = PGSReader('mysubtitles.sup')
    
    # get the first display set (list of segment objects) that contains an image
    display_set = next(ds for ds in pgs.iter_displaysets() if ds.has_image)
    
    # get Palette Display Segment
    pds = display_set.pds[0]
    # get Object Display Segment
    ods = display_sey.ods[0]
    
    # get the image!
    img = make_image(ods, pds)
    img.save('my_subtitle_image.png')
    img.show()
    
    # get time when image would have been displayed on screen in milliseconds:
    timestamp_ms = ods.presentation_timestamp
    
Extremely alpha, issues and suggestions welcome!
