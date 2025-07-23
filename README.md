# py-cloudinfra 

Unofficial Python SDK for the Check Point Infinity Portal, which allows 
Python developers to write software that interacts with applications like 
Smart-1 Cloud or CloudGuard WAF.

This repository is not endorsed, supported or maintained by Check Point.

## Installation

```
pip install git+https://github.com/chkp-jrosenboom/py-cloudinfra
```

## Usage

Configure your credentials in `~/.cloudinfra/credentials`.
At the minimum you need to specify your default CLOUDINFRA_URL.

As a convention, use "{environment}.{app}" to name your profiles.

```ini
[default]
CLOUDINFRA_URL=https://cloudinfra-gw-us.portal.checkpoint.com
CLOUDINFRA_APP=api/v2

[Lab.cloudinfra]
CLOUDINFRA_URL=https://cloudinfra-gw-us.portal.checkpoint.com
CLOUDINFRA_APP=api/v1
CLOUDINFRA_KEY=e04330888b55922fa9ca3dec8424e6fb
CLOUDINFRA_SECRET=9c35541dc9ad6bc1f34c98c2cf3ced06

[Lab.maas]
CLOUDINFRA_APP=app/maas/v2
CLOUDINFRA_KEY=225d4c98896ff40d39de2fca2ee83fc3
CLOUDINFRA_SECRET=eac767d11671a5631b9deb4d9e19307b

[Demo.maas]
CLOUDINFRA_APP=app/maas/v2
CLOUDINFRA_KEY=0ea452acb0d97ad0636ae3c3c592c7f1
CLOUDINFRA_SECRET=6f01839ebd7daf58f302cafbfc010d7c
```

Create a session from your profile and send requests.

```python3
import cloudinfra

maas = cloudinfra.Session(profile_name="Demo.maas")
print(maas.get("environments"))
```

You can also pass in key and secret, or even a JWT directly:
```
session_with_key = cloudinfra.Session(key=key, secret=secret)
session_with_token = cloudinfra.Session(token=token)
```

If you don't pass in a profile nor credentials, it will
- attempt CLOUDINFRA_KEY and CLOUDINFRA_SECRET from environment
- attempt to load the `default` profile from `~/.cloudinfra/credentials

## Troubleshooting

_py-cloudinfra_ provides detailed logging to help diagnose issues.

The default log level is `error`.

Logs are written to STDERR by default.
You can set `CLOUDINFRA_LOGFILE` to specify a logfile instead.

Set the `LOGLEVEL` environment variable to `debug` to enable verbose output, which includes HTTP requests, responses, and internal SDK operations. This can assist in identifying authentication problems, misconfigured profiles, or API errors.

`LOGLEVEL=debug python3 script.py`