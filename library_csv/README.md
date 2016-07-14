# Examples of how to use the ADS API

## Private libraries export to CSV file

Some users may have a need to extract their private libraries into a CSV format.
Currently, there is no intention of fulfiling this request within the user
interface, but it is possible to do using the API.

Simply run this command line tool:

```bash
$ python lib_2_csv.py --save-to-file myfile.csv

  Collecting library: Test [jOWhy4PdRBu_wyUoBuGR1g]
  Pagination 1 out of 5
  Pagination 2 out of 5
  Pagination 3 out of 5
  Pagination 4 out of 5
  Pagination 5 out of 5
  Collecting library: Untitled Library 1 [WenstVArTeq2m6qheH-0eQ]
  Collecting library: ADS Classic Library [5OFj8pgBTKqup1WMkAA7BA]
  Pagination 1 out of 1
  Collecting library: No Description [UvwG9EedQJem6gZ4Wd5g3A]
  Pagination 1 out of 1
```

This will result in some output like the following:
```bash
$ more private_libraries.csv
  #name,num_documents,bibcodes
  Test,102,2016LPI....47.2774E	2016ApJ...819..137K	2016NatGe...9..174E	2016ASSP...42...91E	2015E&SS....2..435E	2015Natur.527...3
   1E	2015DPS....4721813E	2015EPSC...10...75E	2015JChPh.143k4110E	2015arXiv150506493E	2015arXiv150506433E	2015A&C....10...6
   1E	2015MNRAS.446.4239E	2015GMD.....8..261E	2014AcAau.105..511E	2014AGUFM.G31A0383E	2014AGUFM.S33F4902E	2014GMDD....7.438
   3E	2014arXiv1404.5552E	2014PNAS..111.3239E	2014A&A...562A.100E	2014GCN..15903...1E	2014GCN..15829...1E	2014GCN..15904...
   1E	2014PhDT........18E	2014arXiv1401.3013E	2014GCN..15965...1E	2013AGUFMNH43D..04E	2013AGUFM.C43C0685E	2013AGUFMGC31D..0
   2E	2013AGUFM.T42A..03E	2013arXiv1312.5099E	2013arXiv1312.2333E	2013BpJ...105.1935E	2013arXiv1311.6505E	2013JGRB..118.562
   5E	2013A&A...556A..23E	2013arXiv1308.5520E	2013Nanos...5.6662E	2013PhRvC..87e4622E	2013Sci...340..556E	2013JGRB..118.161
   9E	2013SPIE.8578E..0AE	2013PLoSO...857400E	2013GCN..14898...1E	2012AGUFM.T14A..07E	2012AGUFM.C23C0669E	2012PMB....57.828
   5E	2012AcAau..78...26E	2012AcAau..78...20E	2012EnST...46.9681E	2012OptL...37.2571E	2012LPICo1679.4137E	2012LPICo1679.409
   0E	2012EGUGA..1412258E	2012arXiv1205.0057E	2012A&A...539A.113E	2012JGRB..117.3401E	2012arXiv1203.5132E	2012GCN..13457...
   1E	2012GCN..14091...1E	2012GCN..13409...1E	2012GCN..13426...1E	2012GCN..12988...1E	2012grb..confE..86E	2012GCN..13438...
   1E	2012GCN..13003...1E	2012GCN..12931...1E	2011AGUFM.T33A2375E	2011PhDT........40E	2011AGUFM.T34C..02E	2011arXiv1110.189
   8E	2011PhRvL.107p8301E	2011arXiv1109.3921E	2011arXiv1109.3848E	2011arXiv1107.4860E	2011PLoSO...621194E	2011MNRAS.413.234
   5H	2011arXiv1105.0142E	2011AcAau..68.1201E	2011Icar..212..268E	2011GeoRL..38.6305E	2011AcAau..68..441E	2011AcAau..68..38
   9E	2011AcAau..68..399E	2011arXiv1102.3719E	2011SPIE.7896E..0EE	2011SPIE.7896E..11E	2011AcAau..68..339E	2011AcAau..68..41
   8E	2011AcAau..68..435E	2011arXiv1101.2462E	2011GCN..11665...1E	2011GCN..11669...1E	2011GCN..11743...1E	2011GCN..12356...
   1E	2011SMat....7.6820E	2011GCN..12353...1E	2011GCN..12366...1E	2010AGUFM.T13C2213E	2010AGUFM.S53E..01E	2010AGUFMGC23A090
   7E
  Untitled Library 1,0,
  ADS Classic Library,1,2016ASSP...42...91E
  No Description,3,1974AJ.....79.1082E	1908sscc.book.....E	1908nhu..book.....E
```

As you can see, each value is comma separated, and bibcodes are separated by tabs. If you want this output in something different, then just change the script. The only current option via command line is to choose the output file name:

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
