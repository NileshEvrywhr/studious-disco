#!/usr/bin/python3

import requests
import shutil
from bs4 import BeautifulSoup
import os
import subprocess
from icecream import ic

ic.configureOutput(prefix='Debug | ')
#ic.disable()

dir_daily   = "/home/ubuntu/blinkist/en/daily/"			#downloads here, node builds pdf from here
dir_library = "/home/ubuntu/blinkist/en/library/"		#moves a copy here

host = "https://www.blinkist.com"
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"}

dailyBlink = ic(requests.get("https://www.blinkist.com/en/nc/daily", headers=headers))
html = BeautifulSoup(dailyBlink.content, 'html.parser')

headline    = html.find("h3", class_="daily-book__headline").get_text().strip()
author      = html.find("div", class_="daily-book__author").get_text().strip()
tabs        = html.select(".book-tabs__content-inner p")
synopsis    = tabs[0].text
aboutAuthor = tabs[1].text

link = html.find("a", class_="cta cta--play daily-book__cta").get('href')
slug = link.split("/")[-1]

imageUrl = html.find(class_="book-cover__image").get('srcset').split(' ')[0]
imageFile = imageUrl.split('/')[-1]

#clean the daily folder for fresh blink
try:
    shutil.rmtree(dir_daily)
    os.makedirs(dir_daily, exist_ok=True)
except OSError as e:
    ic(e)

#download cover image
r = requests.get(imageUrl, stream = True)
r.raw.decode_content = True
with open(os.path.join(dir_daily, imageFile), 'wb') as img:
    shutil.copyfileobj(r.raw, img)

#find chapters
article = requests.get(host + link, headers=headers)
soup = BeautifulSoup(article.content, 'html.parser')
chapters = soup.find_all('div', class_='chapter')

#write blink in markdown to daily folder
with open(dir_daily + '/' + slug + ".md", 'w') as f:

    f.write('---' + '\n')
    f.write('title: \"' + headline + '\"\n')
    f.write('author: \"' + author + '\"\n')
    f.write('time: ' + '13' + '\n')
    f.write('synopsis: \"' + synopsis + '\"\n')
    f.write('aboutAuthor: \"' + aboutAuthor + '\"\n')
    f.write('description: \"' + author  + '\"\n')
    f.write('layout: default.hbs\n')
    f.write('---' + '\n\n')

    for chapter in chapters:

        heading = chapter.find('h1').get_text()
        f.write('# ' + heading + '\n')

        content = chapter.find_all(class_="chapter__content")
        for paragraph in content:
            f.write(paragraph.text + '\n')

        f.write('\n')

#make daily/format for metalsmith work
try:
    os.makedirs(os.path.join(dir_daily, 'format'), exist_ok = True)
except OSError as e:
    ic(e)

#make PDF here

#call metalsmith to create book formats
output = ic(subprocess.run(['node', 'thedailyblink/index.js'], capture_output = True))
ic(subprocess.run(['rm', 'blinkist/en/daily/format/undefined.pdf'], capture_output = True))
ic(subprocess.run(['rm', 'blinkist/en/daily/format/undefined.epub'], capture_output = True))

#ic(output.returncode)
#ic(output.stdout.decode("utf-8"))

#copy to library folder for cold storage
try:
    shutil.copytree(dir_daily, dir_library + slug)
except FileExistsError as e:
    #ic(e)
    shutil.rmtree(dir_library + slug)
    shutil.copytree(dir_daily, dir_library + slug)
except e:
    ic(e)
