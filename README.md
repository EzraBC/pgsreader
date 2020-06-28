# pgsreader
Read Presentation Graphic Stream (.SUP) files and provide python objects for parsing through the data


Example:

    from pgsreader import PGSReader
    from imagemaker import make_image
    
    # Load a Blu-Ray PGS/SUP file.
    pgs = PGSReader('mysubtitles.sup')
    
    # Get the first DisplaySet that contains a bitmap image
    display_set = next(ds for ds in pgs.iter_displaysets() if ds.has_image)
    
    # Get Palette Display Segment
    pds = display_set.pds[0]
    # Get Object Display Segment
    ods = display_set.ods[0]
    
    # Create and show the bitmap image
    img = make_image(ods, pds)
    img.save('my_subtitle_image.png')
    img.show()
    
    # Create and show the bitmap image with swapped YCbCr channels 
    img = make_image(ods, pds, swap=True)
    img.save('my_subtitle_image.png')
    img.show()
  
    # Retrieve time when image would have been displayed on screen in milliseconds:
    timestamp_ms = ods.presentation_timestamp
    
Extremely alpha, issues and suggestions welcome!
