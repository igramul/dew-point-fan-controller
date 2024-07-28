# System Python
PYTHON = python3
BIN    = ./venv/bin
TARGET = /pyboard
CONFIG = "firmware/config.json firmware/secrets.json firmware/calibration.json"

.PHONY: firmware/version.py
firmware/version.py:
	echo version=\"`git describe`\" > $@
	echo commit=\"`git rev-parse HEAD`\" >> $@
	echo commit_short=\"`git rev-parse --short HEAD`\" >> $@


.PHONY: all
all: install


.PHONY: install
install: $(BIN)/rshell firmware/version.py
	# $(BIN)/rshell connect
	$(BIN)/rshell cp -r firmware/micropython_i2c_lcd $(TARGET)
	$(BIN)/rshell cp firmware/*.py $(TARGET)
	# $(BIN)/rshell cp $(CONFIG) $(TARGET)

.PHONY: reset
reset: $(BIN)/rshell
	$(BIN)/rshell "repl ~ import machine ~ machine.soft_reset() ~"

$(BIN)/rshell: venv venv-update
	$(BIN)/pip install rshell

venv:
	$(PYTHON) -m venv venv

.PHONY: venv-update
venv-update: venv
	$(BIN)/pip install --upgrade pip setuptools

.PHONY:
clean:
	rm -f firmware/version.py

.PHONY: venv-clean
venv-clean:
	rm -r venv

.PHONY: clean-all
clean-all: clean venv-clean

.PHONY: test
test:
	$(BIN)/$(PYTHON) -m unittest discover tests "*_test.py"
