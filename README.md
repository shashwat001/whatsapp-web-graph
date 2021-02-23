# whatsapp-web-graph

**Heavily WIP**

whatsapp-web-graph is a reverse engineered whatsapp-web python application to generate some interesting analytics and graphs on connected users.

## Installation

```
pip install -r requirements.txt
```
#### For graphs
```
sudo apt-get install python-tk
```

## Usage

```bash
python client.py
```

The config and log directory is `````~/.wweb`````. To subscribe to specific numbers, add a file `````~/.wweb/subscribe.json````` and add numbers one in each line as follows:
```
9193XXXXXXX
919583XXXXX
```

The logs are put in ```~/.wweb/logs/info.log```  
The online and offline info of subscribers are put in ```~/.wweb/presence.json```

## Graph generation

To generate bar chart of the users and time spent by them on whatsapp.

<code>python graph-presence.py</code> or <br>
<code>python graph-presence.py --usertype=number</code>

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
