# How to add filters to the application?



For now, adding a filter is a manual operation. 

1. Get the data file from the vendor.  It will likely be a file with at least two columns of data: `wavelength` and `transmission/reflection`

2. Copy it to the folder `filter_data`

3. Open the file `filters.json` in a text editor. You will see that each filter is described. Add your filter at the end of the file and don't forget to add a comma to separate the entry from the previous entry:

   ```json
   [
       {
           "part_number": "FF596-Di01",
           "description": "Dichroic 596 nm",
           "supplier": "Semrock",
           "filename": "FF596-Di01_Spectrum.txt",
           "dimensions": "25 mm x 36 mm",
           "data":"transmission"
       }, <----- don't forget this
       {
           "part_number": "the part",
           "description": "the description",
           "supplier": "the supplier",
           "filename": "the file you just added",
           "dimensions": "the dimensions",
           "data":"transmission or reflection"
       }
   
   ]
   ```

   