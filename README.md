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
Arguments
- --localstorage/-L - To read auth info from ~/.wweb/localstorage.json files instead of data.json. The file should have json like in the format of json in chrome/firefox localstorage.
- --wwebdir/-w - Use custom wwebdir directory.

The config and log directory is `````~/.wweb`````. To subscribe to specific numbers, add a file `````~/.wweb/subscribe.json````` and add numbers one in each line as follows:
```
9193XXXXXXX
919583XXXXX
```

The logs are put in ```~/.wweb/logs/info.log```  
The online and offline info of subscribers are put in ```~/.wweb/presence.json```

#### Note
On April 23, 2021, Whatsapp disabled visibility of online status for the one who doesn't have user's number stored in their contact list. However apparently if the other person has exchanged messages with the user even without saving the number, the online status could be received.

## Graph generation

To generate bar chart of the users and time spent by them on whatsapp.

- To generate graph with number alias(to hide number)  
<code>python graph-presence.py</code> or <br>
- Following arguments can be passed 
  - --usertype=number - To show actual number instead of alias in graph
  - --timeafter/-a \<time string in yyyy-mm-dd hh-mm-ss\> To consider time after given time
  - --timebefore/-b \<time string in yyyy-mm-dd hh-mm-ss\> To consider time before given time
  - --skip_graph/-s to skip generating graph and only display stdout

## Example

- ./graph_presencev2.py -i 30 --usertype=number -a "2021-02-08 08:00:00"  -s --sum
- ./graph_presencev2.py -i 30 --usertype=number -a "2021-03-01 07:00:00" -b "2021-03-01 20:00:00"
- ./graph_presencev2.py

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
