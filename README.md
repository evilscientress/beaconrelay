## beaconrelay

A small python demon that relays the Icinga 2 status to mqtt for use with my EPS8266 based notification beacon.


### Instalation

* Clone the Repository
* create a virtual env or install the dependencies globaly
* install the dependencies

```bash
git clone https://github.com/evilscientress/beaconrelay.git
cd beaconrelay
virtualenv env
. ./env/bin/activate
pip install -r requierments.txt
```

### Configuration

The relaybeacon demon can be configured with a ini style configuration file.
Per default a file called `beaconrelay.cfg` is loaded from the current working directory. 
The location of the config file can be changed by setting the `BEACONRELAY_CONFIG` enviorment variable.


A minimal configuration looks like this, for more optios check the `beaconrelay.cfg.example` file in the repo.
```ini
[icinga]
address=https://icingahost.example.com:5665
user=beaconrelay
password=correct horse battery staple

[mqtt]
hostname=iot.eclipse.org
tls=True # optional defaults to False
user=mqttuser
password=mqttpassword
```

### Usage

```bash
python relaybeacon.py
```