# Dew Point Fan Controller

## Getting started

First setup your config ans secret files as yout need them.
Start with a copy of the example files with the following command:

    cp firmware/config-example.json firmware/config.json
    cp firmware/secrets-example.json firmware/secrets.json

Connect the Raspberry PI Pico with an USB cable to your computer an start with:

    make install

You may need to reset the board an try until the installation process completes.


## Additional Software

### HD44780 LCD Controller Interface with MicroPython

https://github.com/Thomascountz/micropython_i2c_lcd.git

Copy the folder micropython_i2c_lcd on the Raspberry Pi Pico device.
