from flask import Flask, render_template, request, session, redirect, url_for
import json
from qbittorrent import Client
import os
from configparser import ConfigParser
import shutil
import patoolib
import re
import time
import requests
from tabulate import tabulate
from bs4 import BeautifulSoup
import sys
import urllib.parse
import threading
import telegram
import string
import random



app = Flask(__name__)
app.config['DEBUG'] = True


# Check if 'config.py' exists in the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(current_directory, 'config.py')
if os.path.isfile(config_file_path):
    import config
else:
    print("Please rename the confi_example.py to config.py and set it up")
    exit()

app.secret_key = config.app_secret_key

download_path = config.download_path
movie_path = config.movie_path
tvshow_path = config.tvshow_path

tsc_user = config.tsc_user
tsc_pass = config.tsc_pass
tsc_pin = config.tsc_pin

telegram_chat_id = config.telegram_chat_id
telegram_bot_token = config.telegram_bot_token

qbit_url = config.qbit_url
qbit_user = config.qbit_user
qbit_pass = config.qbit_pass

emby_api_key = config.emby_api_key
emby_url = config.emby_url




def torrentClient():
    qb = Client(qbit_url)
    qb.login(qbit_user, qbit_pass)
    #torrents = qb.torrents()
    return qb


def getSession(username, password, pin):
    try:
        session = requests.session()
        response = session.get("https://tsctracker.org/")
        content = response.text
        cookies = requests.utils.dict_from_cookiejar(session.cookies)
        phpsessid = cookies['PHPSESSID']


        headers = {
            'Host': 'tsctracker.org',
            'Cookie': 'PHPSESSID='+phpsessid+'',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }
        session2 = requests.session()
        response2 = session.get("https://tsctracker.org/landing.php", headers=headers)
        content2 = response.text
        cookies2 = requests.utils.dict_from_cookiejar(session.cookies)

        soup = BeautifulSoup(content2, 'html.parser')
        token_element = soup.find('input', {'name': 'login_token'})
        token_value = token_element['value']

        #print(token_value)
        #print(phpsessid)

        headers = {
            'Host': 'tsctracker.org',
            'Cookie': 'PHPSESSID='+phpsessid,
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://tsctracker.org',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': 'https://tsctracker.org/landing.php',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
        }

        payload = {
            'login_token': token_value,
            'username': username,
            'password': password,
            'submit': '',
            'pin': pin
        }

        session = requests.session()
        response = session.post("https://tsctracker.org/takelogin.php", headers=headers, data=payload)

        new_cookies = requests.utils.dict_from_cookiejar(session.cookies)
        new_phpsessid = new_cookies['PHPSESSID']

        return new_phpsessid
    except Exception as e:
        return e


def searchMedia(searchstring, token):
    try:
        headers = {
            'Host': 'tsctracker.org',
            'Cookie': 'PHPSESSID='+token,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }

        session = requests.session()
        response = session.get("https://tsctracker.org/browse.php?search="+searchstring, headers=headers)
        content = response.text

        soup = BeautifulSoup(content, 'html.parser')
        tr_tags = soup.find_all('tr', style='height: 45px;')

        results = []
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            title = td_tags[2].find('a', class_='thumbnail')['title']
            url = td_tags[2].find('a', class_='thumbnail')['href'].replace("details.php","https://tsctracker.org/details.php").replace("&hit=1","")
            id = re.search(".*?details.php\?id=(.*)", url).group(1)
            a = td_tags[2].find('a', class_='thumbnail')
            span_tag = a.find('span')
            image_url = span_tag.find('img')['src'].replace("./","https://tsctracker.org/")
            date_raw = td_tags[5].text.strip()
            date_raw = re.search("^(\d\d\.\d\d.\d\d\d\d)(\d\d\:\d\d:\d\d)", date_raw)
            date = date_raw.group(1)
            time = date_raw.group(2)
            size_raw = re.search("(.*?) (.*)", td_tags[6].text.strip())
            size = size_raw.group(1)
            size_format = size_raw.group(2).lower()
            seeder = int(td_tags[7].text.strip().replace(" Seeder", ""))
            leecher = int(td_tags[8].text.strip().replace(" Leecher", ""))
            info = td_tags[1].find('a')
            info = re.search("(.*)\|(.*)", info.find('img')['title'])
            quality = info.group(2)
            category_raw = info.group(1)
            if category_raw == "Filme":
                category = "movies"
            elif category_raw == "Serien":
                category = "tvshows"
            else:
                category = "others"
            if re.match("(.*?)\.(\d\d\d\d)\..*", title):
                easy_title = re.search("(.*?)\.(\d\d\d\d)\..*", title)
                easy_title = easy_title.group(1).replace("."," ") + " " + "(" + easy_title.group(2) + ")"
            elif re.match("(.*?)\.German\..*", title):
                easy_title = re.search("(.*?)\.German\..*", title)
                easy_title = easy_title.group(1).replace("."," ")
            else:
                easy_title = title


            result = {
                'title': title,
                'url': url,
                'id': id,
                'image_url': image_url,
                'date': date,
                'time': time,
                'seeder': seeder,
                'leecher': leecher,
                'size': size,
                'size_format': size_format,
                'quality': quality,
                'category': category,
                'easy_title': easy_title
            }
            results.append(result)

        return results
    except Exception as e:
        return e


def embyUpdate():
    url = emby_url+"/emby/Library/Refresh?api_key="+emby_api_key

    payload = {}
    headers = {
        'accept': '*/*'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response:
        print("Successfully updated the Emby library")
    else:
        print("there was an error while updating emby library: " + str(response.content))

    
def updateState():
    torrents = torrentClient()
    for torrent in torrents.torrents():
        name = torrent['name']
        category = torrent['category']
        progress = '{:.2f}'.format(torrent['progress'] * 100)  # Format progress to x.xx format
        if float(progress) > 0:
            path = torrent['content_path']
            state = "downloading" if float(progress) < 100 else "downloaded"

            if re.match("(/downloads/.*?)/", path):
                path = re.search("(/downloads/.*?)/", path).group(1)
            path = path.lstrip("/downloads")

            path = os.path.join(download_path, path)

            state_file = os.path.join(path, 'state.ini')


            config = ConfigParser()
            config.read(state_file)
            current_state = config.get('State', 'state', fallback=None)
            if current_state is None or current_state == "downloading":
                config['State'] = {
                    'name': name,
                    'category': category,
                    'progress': progress,
                    'state': state
                }

            with open(state_file, 'w') as f:
                config.write(f)
        else:
            print(name + " failed to start")

def nameParser(title):
    print(title)


def getState():
    data = []

    for entry in os.scandir(download_path):
        if entry.is_dir():
            dir_path = os.path.join(download_path, entry.name)
            state_file = os.path.join(dir_path, 'state.ini')

            if os.path.exists(state_file):
                config = ConfigParser()
                config.read(state_file)
                name = config.get('State', 'name', fallback='')
                state = config.get('State', 'state', fallback='')
                progress = config.get('State', 'progress', fallback='') + "%"
                category = config.get('State', 'category', fallback='')

                data.append([name, state, progress, category])

    return data


def getTorrentUrl(id, token):
    headers = {
        'Host': 'tsctracker.org',
        'Cookie': 'PHPSESSID='+token,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    }

    session = requests.session()
    response = session.get("https://tsctracker.org/details.php?id="+id, headers=headers)
    content = response.text

    soup = BeautifulSoup(content, 'html.parser')

    url = re.search("wget '(.*?)' ", content).group(1)

    return url


def xrelsearch(searchstring):
    searchstring = searchstring+"+german"
    url = "https://www.xrel.to/search.html?mode=full"
    payload = {'xrel_search_query': searchstring}
    headers = {
        'Cookie': 'ANON_LOCALE=de_DE; anonRlsFlt=6; ANON_LOCALE=de_DE',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)
    #print(response.content)
    soup = BeautifulSoup(response.content, 'html.parser')
    #print(response.content)

    results = []

    release_items = soup.find_all('div', class_='release_item')
    for item in release_items:
        try:
            if item.find('div', class_='release_title'):
                main = item.find('div', class_='release_title')
            else:
                main = item.find('div', class_='release_title_p2p')
            title = main.find('a').getText()
            #print(title)
            #print(main.find('a', class_='sub'))
            elements = main.findAll('a')
            for element in elements:
                if element.has_attr('class'):
                    if element.has_attr('title'):
                        release_name = element['title']
                    else:
                        release_name = element.getText()
            if main.find('span', class_="sub"):
                subtitle = main.find('span', class_="sub").getText()
                title = title + subtitle


            if not re.match(".*?\(\d\d\d\d\).*", title):
                if re.match("^.*?\.(\d\d\d\d)\..*", release_name):
                    title = title + " (" + str(re.search("^.*?\.(\d\d\d\d)\..*",release_name).group(1)) + ")"
            print(title)
            # find type from release name
            if re.match('^.*?\.S\d{1,2}\.', release_name, re.IGNORECASE):
                objecttype = "tvshow-season"
            elif re.match('^.*?\.S\d{1,2}E\d{1,2}\.', release_name, re.IGNORECASE):
                objecttype = "tvshow-episode"
            else:
                objecttype = "movie"
            

            
            # grep quality
            if re.match('^.*?\.1080p\..*', release_name, re.IGNORECASE):
                quality = "1080"
            elif re.match('^.*?\.720p\..*', release_name, re.IGNORECASE):
                quality = "720"
            elif re.match('^.*?\.2160p\..*', release_name, re.IGNORECASE):
                quality = "2160"
            elif re.match('^.*\.COMPLETE\.BLURAY.*', release_name):
                quality = "complete-bluray"
            elif re.match('^.*\.COMPLETE\.PAL.*', release_name):
                quality = "complete-dvd"
            else:
                if re.match('^.*\.DVDRip\..*', release_name, re.IGNORECASE) or re.match('^.*\.WEBRip\..*', release_name, re.IGNORECASE) or re.match('^.*\.BDRip\..*', release_name, re.IGNORECASE):
                    quality = "sd"
                else:
                    quality = "sd"

            url = "https://xrel.to" + main.find('a', class_='sub')['href']
            size = item.find('div', class_='release_grp').find('span', class_='sub').getText()
            try:
                group = item.find('div', class_='release_grp').find('a')['title']
            except:
                group = item.find('div', class_='release_grp').find('a').getText()

            entry_dict = {
                'title': title,
                'release_name': release_name,
                'url': url,
                'size': size,
                'group': group,
                'quality': quality,
                'objecttype': objecttype
            }

            

            if not re.match(".*\.3D\..*", release_name) and not re.match(".*\.TS\..*", release_name):
                results.append(entry_dict)
        except Exception as e:
            print(e)

    return results


def requestTSCTorrent(token, title, url, description, type, quality):
    category_raw = type+"-"+str(quality)
    options = [
                {"movie-1080": "54"},
                {"movie-2160": "121"},
                {"movie-720": "55"},
                {"movie-complete-bluray": "43"},
                {"movie-complete-dvd": "20"},
                {"movie-sd": "36"},

                {"tvshow-episode-complete-bluray": "128"},
                {"tvshow-episode-complete-dvd": "129"},
                {"tvshow-episode-1080": "140"},
                {"tvshow-episode-720": "141"},
                {"tvshow-episode-sd": "66"},
                {"tvshow-episode-2160": "127"},
                {"tvshow-season-1080": "125"},
                {"tvshow-season-720": "125"},
                {"tvshow-season-2160": "126"},
                {"tvshow-season-sd": "68"},
                {"tvshow-season-complete-bluray": "125"},
                {"tvshow-season-complete-dvd": "125"}
            ]

    category = False
    for option in options:
            for key, value in option.items():
                if category_raw == key:
                    category = value
    if category == False:
        return ("There was an error with the category")
    

    headers = {
        'Host': 'tsctracker.org',
        'Cookie': 'PHPSESSID='+token,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://tsctracker.org/req.php?action=add'
    }
    #payload = {
    #    'title': urllib.parse.quote(title).replace("%20","+"),
    #    'infourl': urllib.parse.quote(url).replace("%20","+"),
    #    'category': category,
    #    'description': urllib.parse.quote(description).replace("%20","+")
    #}
    payload = {
        'title': title,
        'infourl': url,
        'category': category,
        'description': description
    }

    session = requests.session()
    response = session.post("https://tsctracker.org/req.php?action=takeadd", headers=headers, data=payload)

    #return(str(response.status_code)+": " + str(response.content))
    return("Request placed")


def randomString(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def find_movie(directory):
    target_extensions = ['.mkv', '.mp4', '.avi']
    large_files = []
    available_file = False

    conloop = 1
    track_file = []
    while conloop == 1:
        conloop = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in target_extensions and os.path.getsize(file_path) >= 0.8 * 1024 * 1024 * 1024:
                    large_files.append(file_path)
                    available_file = True
                elif os.path.isfile(file_path) and os.path.splitext(file)[1].lower() == ".rar" and str(file_path) not in track_file:
                    extraction_path = os.path.dirname(file_path)
                    state_file = os.path.join(directory, 'state.ini')
                    config = ConfigParser()
                    config.read(state_file)
                    config.set('State', 'state', 'extracting')
                    with open(state_file, 'w') as f:
                        config.write(f)
                    patoolib.extract_archive(file_path, outdir=os.path.join(extraction_path, 'extracted-'+randomString(3)), verbosity=3)
                    track_file.append(str(file_path))
                    config.set('State', 'state', 'extracted')
                    with open(state_file, 'w') as f:
                        config.write(f)
                    conloop = 1
    
    if len(large_files) != 1:
        print("Error finding movie in '" + directory + "'")
        state_file = os.path.join(directory, 'state.ini')
        config = ConfigParser()
        config.read(state_file)
        config.set('State', 'state', 'error finding movie')
        with open(state_file, 'w') as f:
            config.write(f)
        return False
    else:
        movie_file = large_files[0]

        state_file = os.path.join(directory, 'state.ini')
        config = ConfigParser()
        config.read(state_file)

        movie_name = config.get('State', 'name', fallback='')
        movie_extension = os.path.splitext(movie_file)[1]  # Get the file extension

        destination_path = os.path.join(movie_path, movie_name + movie_extension)  # Include the extension in the destination path

        try:
            print("Copying movie from '" + movie_file + "' to '" + destination_path + "'...")
            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'copying')
            with open(state_file, 'w') as f:
                config.write(f)
            #shutil.copy(movie_file, destination_path)
            shutil.move(movie_file, destination_path)
            print("Movie copied successfully.")

            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'copied')
            with open(state_file, 'w') as f:
                config.write(f)

            #print("update emby database. performing scan...")
            #embyUpdate()

            return True
        except Exception as e:
            print("Error occurred while copying the movie: " + str(e))

            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'error copying')
            with open(state_file, 'w') as f:
                config.write(f)

            return False


def tv_shows(directory):
    target_extensions = ['.mkv', '.mp4', '.avi']
    large_files = []
    available_file = False

    conloop = 1
    track_file = []
    while conloop == 1:
        conloop = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in target_extensions and os.path.getsize(file_path) >= 0.8 * 1024 * 1024 * 1024:
                    large_files.append(file_path)
                    available_file = True
                elif os.path.isfile(file_path) and os.path.splitext(file)[1].lower() == ".rar" and str(file_path) not in track_file:
                    extraction_path = os.path.dirname(file_path)
                    state_file = os.path.join(directory, 'state.ini')
                    config = ConfigParser()
                    config.read(state_file)
                    config.set('State', 'state', 'extracting')
                    with open(state_file, 'w') as f:
                        config.write(f)
                    patoolib.extract_archive(file_path, outdir=os.path.join(extraction_path, 'extracted-'+randomString(3)), verbosity=3)
                    track_file.append(str(file_path))
                    config.set('State', 'state', 'extracted')
                    with open(state_file, 'w') as f:
                        config.write(f)
                    conloop = 1
    
    if len(large_files) != 1:
        print("Error finding movie in '" + directory + "'")
        state_file = os.path.join(directory, 'state.ini')
        config = ConfigParser()
        config.read(state_file)
        config.set('State', 'state', 'error finding movie')
        with open(state_file, 'w') as f:
            config.write(f)
        return False
    else:
        movie_file = large_files[0]

        state_file = os.path.join(directory, 'state.ini')
        config = ConfigParser()
        config.read(state_file)

        movie_name = config.get('State', 'name', fallback='')
        movie_extension = os.path.splitext(movie_file)[1]  # Get the file extension

        destination_path = os.path.join(movie_path, movie_name + movie_extension)  # Include the extension in the destination path

        try:
            print("Copying movie from '" + movie_file + "' to '" + destination_path + "'...")
            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'copying')
            with open(state_file, 'w') as f:
                config.write(f)
            #shutil.copy(movie_file, destination_path)
            shutil.move(movie_file, destination_path)
            print("Movie copied successfully.")

            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'copied')
            with open(state_file, 'w') as f:
                config.write(f)

            #print("update emby database. performing scan...")
            #embyUpdate()

            return True
        except Exception as e:
            print("Error occurred while copying the movie: " + str(e))

            state_file = os.path.join(directory, 'state.ini')
            config = ConfigParser()
            config.read(state_file)
            config.set('State', 'state', 'error copying')
            with open(state_file, 'w') as f:
                config.write(f)

            return False


def organizingMedia():
    for entry in os.scandir(download_path):
        if entry.is_dir():
            dir_path = os.path.join(download_path, entry.name)
            state_file = os.path.join(dir_path, 'state.ini')

            if os.path.exists(state_file):
                config = ConfigParser()
                config.read(state_file)
                category = config.get('State', 'category', fallback='')
                state = config.get('State', 'state', fallback='')

                if category == "movies" and (state == "downloaded" or state == "extracted"):
                    print("Looking through '" + entry.name + "'")
                    find_movie(dir_path)
    print("update emby database. performing scan...")
    embyUpdate()


def telegramMessage(message):
    request = requests.post("https://api.telegram.org/bot"+telegram_bot_token+"/sendMessage", json={'chat_id': telegram_chat_id, 'text': message})
    return request


def getRequestState(token):
    pass


@app.route('/')
def home():
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'access_token' not in session:
        return redirect(url_for('home'))

    # Get the state data
    updateState()
    #state_data = getState()

    return render_template('dashboard.html', state_data=getState())


@app.route('/login', methods=['POST'])
def login():
    emby_username = request.form['username']
    emby_password = request.form['password']
    
    url = emby_url + "/emby/Users/AuthenticateByName"

    payload = json.dumps({
        "Username": emby_username,
        "Pw": emby_password
    })
    headers = {
        'X-Emby-Authorization': 'Emby UserId="", Client="clientus", Device="test", DeviceId="1", Version="1.0.0"',
        'Content-Type': 'application/json'
    }

    auth_response = requests.request("POST", url, headers=headers, data=payload)

    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        access_token = auth_data['AccessToken']
        session['access_token'] = access_token
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Authentication failed!')


@app.route('/add_torrent', methods=['GET', 'POST'])
def add_torrent():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        url = request.form['url']
        category = request.form['category']
        if url.startswith("wget"):
            url = re.match(r'^wget \'(.*?)\' -O', url).group(1)
        qb.download_from_link(link=url, category=category)
        print("Added download " + url)
        
        # Code for adding the torrent here
        # You can use the addTorrent function you already have
        
        return "Request was successfull"
    else:
        # Handle other HTTP methods (e.g., GET) if necessary
        return render_template('add_torrent.html')

@app.route('/add_auto_torrent', methods=['POST'])
def add_auto_torrent():
    if request.method == "POST":
        torrent_id = request.form.get('id')
        torrent_category= request.form.get('category')

        token = getSession(tsc_user,tsc_pass,tsc_pin)
        torrent_url = getTorrentUrl(torrent_id, token)
        torrentClient().download_from_link(link=torrent_url, category=torrent_category)
        return render_template('dashboard.html', state_data=getState(), message="Successfully added download. It could take a few minutes to show up in the Dashboard!")


@app.route('/add_auto_torrent_by_id', methods=['POST'])
def add_auto_torrent_by_id():
    print("to be done")



@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        query = request.form.get('query')
        session_token = getSession(tsc_user,tsc_pass,tsc_pin)
        search_results = searchMedia(query, session_token)
        #return search_results

        return render_template('search.html', search_results=search_results, query=query)
    
    return render_template('search.html')

@app.route('/requesttorrent', methods=['GET', 'POST'])
def requesttorrent():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        query = request.form.get('query')
        search_results = xrelsearch(query)
        # search xrel and return the information

        return render_template('request.html', search_results=search_results)
        #return search_results

    
    return render_template('request.html')


@app.route('/auto_requesttorrent', methods=['GET', 'POST'])
def auto_requesttorrent():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        request_title = request.form.get('title')
        request_url= request.form.get('url')
        request_description= request.form.get('description')
        request_objecttype= request.form.get('objecttype')
        request_quality= request.form.get('quality')

        #return render_template('request.html', search_results=search_results)
        token = getSession(tsc_user,tsc_pass,tsc_pin)
        dorequest = requestTSCTorrent(token, request_title, request_url, request_description, request_objecttype, request_quality)
        return render_template('dashboard.html', state_data=getState(), message=dorequest)

    #return render_template('request')
    return redirect(url_for('request'))


@app.route('/request_manually', methods=['GET', 'POST'])
def request_manually():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        request_title = request.form.get('title')
        request_url= request.form.get('imdb')
        request_description= request.form.get('description')
        request_objecttype= request.form.get('type')
        request_quality= request.form.get('quality')

        #return render_template('request.html', search_results=search_results)
        token = getSession(tsc_user,tsc_pass,tsc_pin)
        dorequest = requestTSCTorrent(token, request_title, request_url, request_description, request_objecttype, request_quality)
        return render_template('dashboard.html', state_data=getState(), message=dorequest)

    #return render_template('request')
    return render_template('request_manually.html')


@app.route('/organize', methods=['GET', 'POST'])
def organize():
    if 'access_token' not in session:
        return redirect(url_for('home'))
    
    #if request.method == 'POST':
    #    #organizingMedia()
    #    threading.Thread(target=organizingMedia).start()
    #    return render_template('dashboard.html', state_data=getState(), message="Reorganizing started. This could take a few minutes. Please refresh the page to check the current state...")

    #return render_template('organize.html')
    threading.Thread(target=organizingMedia).start()
    time.sleep(1)
    return render_template('dashboard.html', state_data=getState(), message="Reorganizing started. This could take a few minutes. Please refresh the page to check the current state...")



@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'access_token' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
            return render_template('account.html', error='POST not allowed, have to implement the feature first...')

    return render_template('account.html')


@app.route('/logout')
def logout():
    session.pop('access_token', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
