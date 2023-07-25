
<h1 align="left">tscbot</h1>

<p>
<a href="https://github.com/eliasthecactus/tscbot#readme" target="_blank">
<img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
</a>
<a href="https://github.com/eliasthecactus/tscbot/graphs/commit-activity" target="_blank">
<img alt="Maintenance" src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" />
</a>
<img alt="Version: v1.0.0-alpha1" src="https://img.shields.io/badge/version-v1.0.0--alpha1-blue" />
<a href="https://github.com/eliasthecactus/tscbot/blob/main/LICENSE" target="_blank">
<img alt="License: MIT" src="https://img.shields.io/github/license/eliasthecactus/tscbot" />
</a>
</p>

  

> 😋 This script is a custom automation tool designed to work with the TSC Tracker, a private torrent tracker. It functions similarly to Radarr and Sonarr but is specifically tailored to the TSC Tracker platform. The script allows users to manage and automate their downloads, request and more...



## Screenshots
### Dashboard
![dashboard](https://raw.githubusercontent.com/eliasthecactus/tscbot/main/src/img/dashboard.PNG)
### Search TSC
![dashboard](https://raw.githubusercontent.com/eliasthecactus/tscbot/main/src/img/search.PNG)
### Request using xrel
![dashboard](https://raw.githubusercontent.com/eliasthecactus/tscbot/main/src/img/request.PNG)


## Features
- bla bla
- bla bla

## Requirements
- Enable the `wget-Kommando` in your TSC-Account-Settings
- Set the `Torrentlist-Layout` to `Torrentlist-Layout`
- Working EMBY instance (planed to add jellyfin and/or custom auth)
- Working qBittorrent instance
- TSC-Account


## Usage
### 1. Clone repo
```bash
git clone https://github.com/eliasthecactus/tscbot.git
cd tscbot/
```
### 2. Install requirements
```bash
pip install -r requirements.txt
```
### 3. Configure the config.py
```bash
cd application
cp config_example.py config.py
vi config.py
```
### 4. Using Flask (only for development)
```bash
python app.py
```


## 📃 ToDo
- [x] Add Emby-Auth
- [x] Add xrel integration
- [ ] TV Show support
- [ ] Request state overview


## Team
<div style="display: flex; flex-direction: row; align-items: center;">
<img src="https://avatars.githubusercontent.com/u/14819853?v=3&s=30" alt="eliasthecacuts" style="width: 30px; height: 30px;">
<strong>elias - [Instagram](https://instagram.com/eliasthecactus)</strong>
</div>


## 🤝 Contributing
Contributions, issues and feature requests are welcome!<br />Feel free to check [issues page](https://github.com/eliasthecactus/tscbot/issues).


## Show your support
Give a ⭐️ if this project helped you!



## 📝 License
[Copyright](https://github.com/eliasthecactus/tscbot/blob/main/LICENSE) © 2023 [eliasthecactus](https://github.com/eliasthecactus)
