# System Python
PYTHON = python3
BIN    = ./venv/bin
TARGET = /pyboard


.PHONY: all
all: $(BIN)/rshell install


.PHONY: install
install: $(BIN)/rshell
	$(BIN)/rshell cp -r micropython_i2c_lcd $(TARGET)
	$(BIN)/rshell cp *.py $(TARGET)


$(BIN)/rshell: venv venv-update
	$(BIN)/pip install rshell

venv:
	python3 -m venv venv

.PHONY: venv-update
venv-update: venv
	$(BIN)/pip install --upgrade pip setuptools

.PHONY: venv-clean
venv-clean:
	rm -r venv

.PHONY: clean-all
clean-all: venv-clean
