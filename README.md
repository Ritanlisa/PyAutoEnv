# PyAutoEnv
Allow user to create a python environment full automatically
## Usage
```
usage: AutoEnv.py [-h] [--conda] [--python PYTHON] [--retlenv RETLENV] [--retry RETRY] [--cuda CUDA] [--wait WAIT] entry

positional arguments:
  entry              entry point of the python file

optional arguments:
  -h, --help         show this help message and exit
  --conda            use conda environment
  --python PYTHON    use pip environment
  --retlenv RETLENV  max retry times for creating local environment
  --retry RETRY      max retry times for dealing dependencies
  --cuda CUDA        install pytorch with cuda support
  --wait WAIT        wait time(s) to check if the entry program runs successfully
(base) PS C:\Users\Ritanlisa\Desktop\PyAutoEnv> 
```