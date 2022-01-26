from urllib.request import urlopen as uReq, Request
from bs4 import BeautifulSoup as soup
import mysql.connector 
import re
import os
import requests
import sys
import unicodedata

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def create_html(fullpath,title,body):
    header='<!DOCTYPE html><html lang="en-US"><head>\n\t<title>'+title+'</title>\n\t<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n\t<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-F3w7mX95PdgyTmZZMECAngseQB83DfGTowi0iMjiWaeVhAn4FJkqJByhZMI3AhiU" crossorigin="anonymous">\n\t<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-/bQdsTh/da6pkI1MST/rWKFNjaCP5gBSY4sEBT38Q/9RBh9AH40zEOg7Hlq2THRZ" crossorigin="anonymous"></script>\n</head>\n<body>'
    footer="</body>\n</html>"
    contents = header+body+footer
    create_file(fullpath,contents)
    
def get_pages_with_photos(url,pageno):
    #recursive counting of pages with photos
    photos_url = url+'?tab=photos&page='+str(pageno)
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(photos_url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    #are there any photos in this page?
    photos_num=page_soup.findAll('h3')
   
    photos_present = False
    pattern=r'(\d{1,3})\s*images'
    for pn in photos_num:
        if len(pn.contents)>1:
            text=pn.contents[1].get_text()
            d=re.findall(pattern,text, re.IGNORECASE)
            if d!=[] and int(d[0])!=0:
                photos_present = True
    if photos_present == False:
        return 0
    #else
    #is there a next page?
    pages = page_soup.findAll('a',rel="next")
    if pages == []:
        return pageno
    else:
        pageno +=1
        return get_pages_with_photos(url,pageno)

def get_photos(url):
    pages_with_photos = get_pages_with_photos(url,1)
    html=[]
    if pages_with_photos > 0:
        gal = extract_username(url)
        create_dir('atw/'+gal+'/p/')
        for i in range(pages_with_photos):
            photos_url = url+'?tab=photos&page='+str(i+1)
            html.append(download_photos(photos_url,gal))
        flat_list = [item for sublist in html for item in sublist]
        body='\n<h2>Photos</h2>\n<div class="container">\n\t<div class="row">\n'

        for i in range(len(flat_list)):
            body+='\t\t<div class="col">'+str(flat_list[i])+'</div>\n'
            if (i+1) % 5 == 0 and i<(len(flat_list)-1):
                body+='\t</div>\n\t<div class="row">\n'
            elif i==len(flat_list)-1:
                body+='\t</div>\n'
        body+="</div>"
        return body
    else:
        return('')

def download_photos(url,username):
    #print("\tWill download photos from "+url)
    html=[]
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    photos_b = page_soup.findAll('div',{"class":"col-lg-4 col-12 col-md-6 mb-4 px-3 px-md-4 activity-item mb-4"})
    for p in photos_b:
        desc=p.find('p')
        descr=desc.get_text()
        purl=p.find('a').get('href')
        if purl !='':
            html.append('<a href="p/'+extract_username(purl)+'"><img width="150" class="" src="p/'+extract_username(purl)+'"></a><br><p>'+descr+'</p>')
            filename = 'atw/'+username+'/p/'+extract_username(purl)
            download_file(filename,purl)
    return(html)

def get_profile(url):
    username = extract_username(url)
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    
    #profile pic
    profile_pic=page_soup.find("img",{"class":"rounded-circle border"})
    profile_pic = profile_pic.get('src')
    download_file('atw/'+username+'/'+username+'.jpg',profile_pic)
    html='<h2>Profile</h2><div class="container-fluid"><div class="row">\n\t<div class="col">'
    html+='<img src="'+username+'.jpg" width="300" class="rounded">\n\t</div>\n'

    #About
    info=page_soup.find("div",{"class":"border p-4 my-4"})
    info=info.findNext('div')
    info_bits=info.find_all('p')
    ln=''
    for x in info_bits:
    	y =x.get_text()
    	i=0
    	for line in y.splitlines():
    		if i%2==0:
    			ln+=line+":"
    		else:
    			ln+=line+"<br>"
    		i+=1
    ln=ln.replace("::",":")
    profile_candidates=page_soup.find_all('h3')
    pattern=r'About'
    profile_text=ln
    for x in profile_candidates:
         d=re.findall(pattern,x.get_text(),re.IGNORECASE)
         if d!=[]:
             profile_text=x.findNext('div')
    html+='\t<div class="col">About:\n\t'
    if profile_text !="":
    	html+=str(profile_text)
    html+='\t</div>'
    
    #What I offer
    profile_candidates=page_soup.find_all('h4')
    pattern=r'What I Offer'
    what_i_offer=''
    for x in profile_candidates:
         d=re.findall(pattern,x.get_text(),re.IGNORECASE)
         if d!=[]:
             what_i_offer=x.findNext('p').get_text()
    offer_text='\t<div class="col">Offers:\n\t<ol>'
    offers_present=False
    for line in what_i_offer.splitlines():
    	if len(line.strip()) !=0:
    		offers_present=True
    		offer_text+='\n\t<li>'+line.strip()+'</li>'
    offer_text+='</ol>'
    if offers_present:
    	html+='\t<div class="col"'
    	html+=str(offer_text)
    	html+='\t</div>'
    html+='</div>'
    return(html)

def get_pages_with_listings(url,pageno):
    #counts the number of pages with listings
    listings_url = url+'?tab=shop&page='+str(pageno)
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(listings_url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    #are there any listings in this page?
    listings_num=page_soup.findAll('h3')
   
    listings_present = False
    pattern=r'(\d{1,3})\s*listings'
    for pn in listings_num:
        if len(pn.contents)>1:
            text=pn.contents[1].get_text()
            d=re.findall(pattern,text, re.IGNORECASE)
            if d!=[] and int(d[0])!=0:
                listings_present = True
    if listings_present == False:
        return 0
    #else
    #is there a next page?
    pages = page_soup.findAll('a',rel="next")
    if pages == []:
        return pageno
    else:
        pageno +=1
        return get_pages_with_listings(url,pageno)

def download_listings(url,username):
    #print("\tWill download listings from "+url)
    html=[]
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    listings_b = page_soup.findAll('div',{"class":"col-lg-4 col-md-6 col-12 mb-4 listing"})
    for l in listings_b:
        desc=l.find('a')
        lurl=desc.get('href')
        if lurl !='':
            ldesc=l.find("p",{"class":"small listing-description"}).getText()
            ltitle=desc.find('img').attrs['alt']
            lthumb=desc.find('img').attrs['data-src']
            lprice=l.select_one('p[class*="brand"]')
            filename = slugify(ltitle)
            create_dir('atw/'+username+'/l/'+filename)
            download_file('atw/'+username+'/l/'+filename+'/'+extract_username(lthumb),lthumb)
            html.append('<a href="l/'+filename+'/'+filename+'.html"><img width="150" class="" src="l/'+filename+'/'+extract_username(lthumb)+'"><br><b>'+str(ltitle)+'</b></a><br>'+str(ldesc)+''+str(lprice))
            download_listing(username,'atw/'+username+'/l/'+filename,filename,lurl,ltitle)
    return(html)
    
def download_listing(username,directory,filename,url,title):
    headers =  {'User-Agent': 'Mozilla/5.0'}
    page_html = requests.get(url, headers=headers).content
    page_soup = soup(page_html, "html.parser")
    description = page_soup.find('p',{"class":"font-size-16 expanding-text"})
    price = page_soup.find('p',{"class":"brand h3 mb-3 mt-3 font-weight-bold"})
    tags=''
    all_tags = page_soup.findAll('a',{"class":"mr-1 mb-2 btn btn-sm btn-outline-primary p-1 px-2"})
    for tag in all_tags:
        tags +=tag.contents[0]+", "
    tags = tags[:-2]
    photos=[]
    photoz = page_soup.findAll('a',{"class":"image-gallery"})
    for p in photoz:
        photos.append(p.get('href'))
    title = username+": "+title
    body='<div class="container">\n\t<div class="row">\n\t\t<div class="col">'+'<h2><a href="'+str(url)+'">'+title+'</a></h2><br>'+description.get_text()+'<br><p>'+tags+'</p>'+str(price)+'</div><div class="col"><a href="https://www.allthingsworn.com/profile/'+username+'">'+username+'</a><br><a href="../../'+username+'.html"><img src="../../'+username+'.jpg" width="150"></a></div>'
    body +='</div><div class="row">'
    for p in photos:
        download_file(directory+'/'+extract_username(p),p)
        body+='<div class="col"><a href="'+extract_username(p)+'"><img src="'+extract_username(p)+'" width="300"></a></div>'
    body +='</div>'
    fullpath=directory+'/'+filename+'.html'
    create_html(fullpath,title,body)

def get_listings(url):
    pages_with_listings = get_pages_with_listings(url,1)
    html=[]
    if pages_with_listings > 0:
        gal = extract_username(url)
        create_dir('atw/'+gal+'/l/')
        for i in range(pages_with_listings):
            listings_url = url+'?tab=shop&page='+str(i+1)
            html.append(download_listings(listings_url,gal))
        flat_list = [item for sublist in html for item in sublist]
        body='\n<h2>Listings</h2>\n<div class="container-fluid">\n\t<div class="row">\n'
        for i in range(len(flat_list)):
            body+='\t\t<div class="col">'+str(flat_list[i])+'</div>\n'
            if (i+1)%5 ==0 and (i+1)<len(flat_list):
                body+='\t</div>\n\t<div class="row">\n'
            elif i==len(flat_list)-1:
                body +='\t</div>'
        body+='\t</div>'
        return body
    else:
        return('')
    
def scrap(url):
    username = extract_username(url)
    print("\ti) Getting profile info")
    profile = get_profile(url)
    print("\tii) Getting photos")
    photos = get_photos(url)
    print("\tiii) Getting listings")  
    listings = get_listings(url)
    fullpath = 'atw/'+username+'/'+username+".html"
    print("\tiv) Creating HTML file")
    create_html(fullpath,'atw: '+username,'<h1>'+username+'</h1>'+profile+photos+listings)

def download_file(filename,url):
    if os.path.isfile(filename) == False:
        img = requests.get(url, allow_redirects=True)
        open(filename, 'wb').write(img.content)

def create_file(filename,contents):
    if os.path.isfile(filename) == False:
        my_file = open(filename,'w',encoding='utf-8')
        my_file.write(contents)
        my_file.close()

def extract_username(url):
    gal=''
    chars = 0
    for i in range(len(url)-1,0,-1):
        if url[i] !='/':
            gal = url[i]+gal
            chars +=1
        elif url[i] =='/' and chars==0:
            continue
        else:
            break
    return gal

def create_dir(dir):
    try:
        os.mkdir(dir)
        #print("Directory '%s' created" %dir)
    except OSError as error:
        pass   #print(error)

def process_url(url,no):
    page_to_scrap = url
    print("Processing profile #"+str(no)+": "+url)
    gal=extract_username(page_to_scrap)
    create_dir('atw/'+gal)
    scrap(page_to_scrap)
    return 1

def main():
    #arguments are either a list of space-separated profile URLS 
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    if "-i" in opts:
        #print(" ".join(arg.capitalize() for arg in args))
        filename = args[0]
        try:
            with open(filename, 'r') as reader:
                line = reader.readline()
                i=1
                successes = 0
                while line != '':
                    if process_url(line.strip(),i) == 1:
                        successes +=1
                    i+=1
                    line = reader.readline()
                print("Job done, "+str(successes)+" profiles scraped successfully!")
        except FileNotFoundError:
            print("Error: File '"+filename+"' not found!")
    elif "-u" in opts:
        i=1
        successes = 0
        for p in args:
            if process_url(p.strip(),i) == 1:
                successes +=1
            i+=1
        print("Job done, "+str(successes)+" profiles scraped successfully!")
    else:
        raise SystemExit(f"Usage: {sys.argv[0]} (-i | -u) <arguments>...")

if __name__ == "__main__":
    main()
