# Examples of how to use the ADS API

## Private libraries export to CSV file

Some users may have a need to extract their private libraries into a CSV format.
Currently, there is no intention of fulfiling this request within the user
interface, but it is possible to do using the API.

Simply run this command line tool:

```bash
python lib_2_csv.py --save-to-file myfile.csv
```

The only currently option is the output file name:

```bash
python lib_2_csv.py --help
usage: lib_2_csv.py [-h] [-s OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -s OUTPUT_FILE, --save-to-file OUTPUT_FILE
                        Save my libraries to this file.
```

**Note**: it assumes your API token resides in the folder `~/.ads/dev_key`.
You can also override it with the `TOKEN` variable at the top of the script.