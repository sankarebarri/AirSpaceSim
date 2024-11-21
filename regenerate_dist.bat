@echo off
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q AirSpaceSim.egg-info
python setup.py sdist bdist_wheel
pip install dist\AirSpaceSim-0.1.0.tar.gz
pause
