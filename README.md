# atw-parser
A simple profile parser for atw (allthingsworn).

**Requirements**
* Python 3
   * urllib (pip install urllib)
   * bs4 (pip install bs4)

**Usage**:
Clone this and run it either supplying a list of URLs or a text file that contains the URLS.


```Bash
python3 ./atw.py (-u | -i) arguments
   
   -u is followed by URLs of the profile pages you want to parse.
   -i is followed by the text file that has the URLs, one line per profile

examples:
    python3 ./atw.py -u https://www.allthingsworn.com/profile/profile1 https://www.allthingsworn.com/profile/profile2
    python3 ./atw.py -i file_containing_urls.txt
```

Have fun
