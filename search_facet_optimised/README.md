# Examples of how to use the ADS API

## Search Facet Plots Using Facets

A small tool to plot the search facet plots that are found on the ADS search results page. This is a more optimised version than the brute force approach used in the other example [Search Facet Plot](https://raw.githubusercontent.com/jonnybazookatone/ads-examples/master/search_facet):

![Search results page on ADS Bumblebee](https://raw.githubusercontent.com/jonnybazookatone/ads-examples/master/search_facet_optimised/ui_example.png)

The tool allows you to create metrics for a set of bibcodes in two ways:

  1. via ORCiD iD
  2. via a generic ADS query

If you want to preseve the plots, you can either save them to disc as an image, or in CSV format.

Note: this tool is not limited by the number of bibcodes in the response unlike the metrics service.

Example usage:
```
python plot_search.py --orcid 0000-0001-8043-4965 --plot -f png --save-to-file csv
```

Makes plots like this:

![Search example page](https://raw.githubusercontent.com/jonnybazookatone/ads-examples/master/search_facet_optimised/example.png)
