# blgr

[![Join the chat at https://gitter.im/sepulchered/blgr](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/sepulchered/blgr?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Static blog generator for using with ipython notebooks.
It's in alpha stage now thus don't expect much.

![Codship Build Status](https://codeship.com/projects/23f344f0-88ee-0132-d13f-02ce2f7c7d8a/status?branch=master)


## Usage

Here is snapshot of blgr.py script:

    usage: blgr.py [-h] -c CONFIG_PATH {serve,create,generate} ...

    blgr cli

    positional arguments:
      {serve,create,generate}
                            command

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG_PATH, --config_path CONFIG_PATH
                            path to config file

As for now it is not set to be used as cli application, but just python script.
