# Usage:
```
python3 main.py [-h] -n raven -g https://github.com/RavenProject/Ravencoin.git
                [-c master or v0.15.99.0] [-v 1.0] [-r 1] [-o /path/to]
                [-m John Doe] [-e john@doe.com]
```

Create a source Debian package for any cryptocoin wallet

## Arguments:
* `-h, --help`  
show this help message and exit
* `-n raven, --name raven`  
Coin name (default: None)
* `-g https://github.com/RavenProject/Ravencoin.git, --git-url https://github.com/RavenProject/Ravencoin.git`  
GIT project url (default: None)
* `-c master or v0.15.99.0, --git-checkout master or v0.15.99.0`  
GIT tag or branch to checkout (default: master)
* `-v 1.0, --version 1.0`  
Force package version (default: None)
* `-r 1, --revision 1` 
Debian package revision (default: 1)
* `-o /path/to, --out-dir /path/to`  
Out folder for generated source package (default: /tmp)
* `-m John Doe, --maintainer-name John Doe`  
Debian package maintainer pretty name (default: Guessed automatically)
* `-e john@doe.com, --maintainer-email john@doe.com`  
Debian package maintainer email address (default: Guessed automatically)
