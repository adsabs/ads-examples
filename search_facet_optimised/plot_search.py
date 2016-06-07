"""
Plot the search facet plots that are found on the ADS search results page.
This example allows you to create metrics for i) an ORCiD iD query, and ii) a
generic ADS query.

You can also save all plots to disk in CSV format.

There is in principle no limit on the number of papers that are returned to
create the plots, unlike that of the metrics end point. There is currently not
extensive documentation on how to use the facets, nor a client implementation
from Andy Casey's API. For further details on how to leverage the facets, please
contact the ADS team at adshelp [at] cfa.harvard.edu.
"""

import os
import sys
import numpy
import argparse
import matplotlib
matplotlib.use('TkAgg')
import seaborn  # simply importing this changes matplotlib styles
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests



def dyear(y):
    """
    Convert delta year into a timedelta object
    :param y: delta year
    """
    return timedelta(days=365*y)


def stepify(x, y, binsize=1):
    """
    Create a step-like version of the data.
    :param x: x-array
    :param y: y-array
    :param binsize: length of the step size
    """

    offset = dyear(binsize/2.0)
    binsize = dyear(binsize)

    new_x, new_y = [x[0]], [0]
    for i in range(len(x)):
        new_x.extend([x[i], x[i]+binsize])
        new_y.extend([y[i], y[i]])

    # Add tails
    new_x.append(x[-1]+binsize)
    new_y.append(0)

    return numpy.array(new_x) - offset, numpy.array(new_y)


def step(ax, x, y, label='', color='blue', lw=1):
    """
    Create a step plot that is filled underneath. This is not usually possible
    using the normal ax.step() function
    """
    x_, y_ = stepify(x, y)
    ax.errorbar(x_, y_, label=label, color=color, lw=lw)
    ax.fill_between(x_, 0, y_, color=color, alpha=0.5)


def h_index(citations):
    """
    Calculate the H-index
    https://en.wikipedia.org/wiki/H-index
    :param citations: list of citations (sorted or unsorted)
    """

    c = list(citations)
    c.sort(reverse=True)

    for i in range(len(c)):
        if i > c[i]:
            return i

    return len(c)


def main(
        output_path,
        figure_format,
        orcid=False,
        query=False,
        save=False,
        plot=False,
        log=False,
        token=None
):

    if token is None:
        TOKEN = os.getenv('ADS_DEV_KEY')
    else:
        TOKEN = token

    # See what the user has given to generate the metrics plot
    if query:
        print('You gave a query: {}'.format(query))
        q = query
    elif orcid:
        q = 'orcid:{}'.format(orcid)
        print('You gave an ORCiD iD: {}'.format(orcid))
    else:
        sys.exit()

    headers = {'Authorization': 'Bearer:{}'.format(TOKEN)}
    url = 'https://api.adsabs.harvard.edu/v1/search/query'

    params_year_facet = {
        'facet': 'true',
        'facet.minCount': '1',
        'facet.pivot': 'property,year',
        'q': q,
        'sort': 'date desc'
    }
    params_citation_facet = {
        'facet': 'true',
        'facet.minCount': '1',
        'facet.pivot': 'property,citation_count',
        'q': q,
        'sort': 'citation_count desc',
    }
    params_read_facet = {
        'facet': 'true',
        'facet.minCount': '1',
        'facet.pivot': 'property,read_count',
        'q': q,
        'sort': 'read_count desc',
    }

    # Get the number of papers facet
    r_year_facet = requests.get(
            url,
            params=params_year_facet,
            headers=headers
        )
    data_year_facet = \
        r_year_facet.json()['facet_counts']['facet_pivot']['property,year']

    # Get the citation facets
    r_citation_facet = requests.get(
            url,
            params=params_citation_facet,
            headers=headers
        )
    data_citation_facet = \
        r_citation_facet.json()['facet_counts']['facet_pivot']['property,citation_count']

    # Get the read facets
    r_read_facet = requests.get(
            url,
            params=params_read_facet,
            headers=headers
        )
    data_read_facet = \
        r_read_facet.json()['facet_counts']['facet_pivot']['property,read_count']

    # Number of Papers
    # ----------------
    # Lets re-organise into year: ref/unref
    years = {}
    for p in data_year_facet:
        property = p['value']

        for entry in p['pivot']:

            y = datetime.strptime(entry['value'], '%Y')
            years.setdefault(y, {})

            years[y].setdefault('refereed', 0)
            years[y].setdefault('unrefereed', 0)

            if property == 'refereed':
                years[y]['refereed'] += entry['count']
            elif property == 'notrefereed':
                years[y]['unrefereed'] += entry['count']

    # Ensure ordering, probably a smarter way to do it
    yy = years.keys()
    yy.sort()
    x_year = numpy.array(yy)

    ref_pap = numpy.array([years[x_year[i]]['refereed'] for i in range(len(x_year))])
    unref_pap = numpy.array([years[x_year[i]]['unrefereed'] for i in range(len(x_year))])

    # Number of Citations
    # -------------------
    # Lets re-organise the citations and determine the h-index
    y_cc = []
    for p in data_citation_facet:
        property = p['value']
        for entry in p['pivot']:
            if property in ['refereed', 'notrefereed']:
                for _ in range(entry['count']):
                    y_cc.append(entry['value'])
    y_cc.sort(reverse=True)
    y_cc = numpy.array(y_cc)
    x_cc = numpy.array([i for i in range(len(y_cc))])

    # Number of Reads
    # ---------------
    # Lets re-organise the citations and determine the h-index
    y_rc = []
    for p in data_read_facet:
        property = p['value']
        for entry in p['pivot']:
            if property in ['refereed', 'notrefereed']:
                for _ in range(entry['count']):
                    y_rc.append(entry['value'])
    y_rc.sort(reverse=True)
    y_rc = numpy.array(y_rc)
    x_rc = numpy.array([i for i in range(len(y_rc))])

    # Collect the metrics from the API
    if plot:
        # Define the figure and the axes
        fig = plt.figure(0, figsize=(8.27, 11.69))
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        # Number of papers
        step(
            ax1,
            x_year,
            unref_pap,
            label='Not refereed: {}'.format(unref_pap.sum()),
            color='green'
        )
        step(
            ax1,
            x_year,
            ref_pap,
            label='Refereed: {}'.format(ref_pap.sum()),
            color='blue'
        )

        y_max = max((unref_pap).max(), ref_pap.max()) + 1
        ax1.set_ylim([0, y_max])
        ax1.set_ylabel('Numer of papers')
        ax1.set_xlabel('Year')
        leg1 = ax1.legend(loc=0)
        leg1.draw_frame(False)

        # Plot number of citations
        # ------------------------
        h = h_index(y_cc)
        ax2.errorbar(
            x_cc,
            y_cc,
            label='Total citations: {}'.format(y_cc.sum()),
            ls='-',
            color='blue',
            lw=3,
            alpha=0.5
        )
        h_x = numpy.arange(0, h+1, 1)
        h_y = numpy.array([h for i in h_x])
        ax2.errorbar(
            h_x, h_y, lw=3, color='black', alpha=0.5, label='H-index: {}'.format(h)
        )
        ax2.errorbar(
            h_y, h_x, lw=3, color='black', alpha=0.5
        )

        # Labels, legends, and scaling
        ax2.set_ylabel('Total numer of citations per paper')
        leg2 = ax2.legend(loc=0)
        leg2.draw_frame(False)
        y_max = y_cc.max() + 1
        y_min = 0
        if log:
            ax2.set_yscale('log')
        ax2.set_ylim([y_min, y_max])
        x_max = y_cc.size + 1
        ax2.set_xlim([0, x_max])

        # Plot number of reads
        # ---------------------
        h = h_index(y_rc)
        ax3.errorbar(
            x_rc,
            y_rc,
            label='Total reads: {}'.format(int(y_rc.sum())),
            ls='-',
            color='blue',
            lw=3,
            alpha=0.5
        )

        h_x = numpy.arange(0, h+1, 1)
        h_y = numpy.array([h for i in h_x])
        ax3.errorbar(
            h_x, h_y, lw=3, color='black', alpha=0.5, label='H-index: {}'.format(h)
        )
        ax3.errorbar(
            h_y, h_x, lw=3, color='black', alpha=0.5
        )

        ax3.set_ylabel('Total numer of reads per paper')
        leg3 = ax3.legend(loc=0)
        leg3.draw_frame(False)
        if log:
            ax3.set_yscale('log')

        ax3.set_ylim([0, y_rc.max()+1])

        im = plt.imread('ads_logo.jpg')
        newax = fig.add_axes([0.1, 0.9, 0.8, 0.1], anchor='NW', aspect='equal')
        newax.imshow(im)
        newax.axis('off')

        figure_path = '{}/search_metrics.{}'.format(output_path, figure_format)
        plt.savefig(figure_path)

    # Save to disk if requested
    if save == 'csv':
        with open('{}/number.csv'.format(output_path), 'w') as f:

                f.write('#year,unrefereed_number,refereed_number\n')
                for i in range(len(x_year)):
                    f.write('{year},{unref},{ref}\n'.format(
                        year=x_year[i].year,
                        unref=unref_pap[i],
                        ref=ref_pap[i]
                    ))
        with open('{}/citation_count.csv'.format(output_path), 'w') as f:
            f.write('#index,citation_count\n')
            for i in range(len(y_cc)):
                f.write('{index},{cit}\n'.format(
                    index=i,
                    cit=y_cc[i],
                ))
        with open('{}/read_count.csv'.format(output_path), 'w') as f:
            f.write('#index,read_count\n')
            for i in range(len(y_rc)):
                f.write('{index},{read}\n'.format(
                    index=i,
                    read=y_rc[i],
                ))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help='Path to save figure [default: `pwd`]',
        default='.',
        type=str
    )
    parser.add_argument(
        '-f',
        '--format',
        dest='format',
        help='Format to save figure [default: pdf]',
        choices=['png', 'pdf', 'ps', 'svg'],
        default='pdf',
        type=str
    )
    parser.add_argument(
        '--orcid',
        dest='orcid',
        help='ORCiD identifier [default: None]',
        default=None,
        type=str
    )
    parser.add_argument(
        '--query',
        dest='query',
        help='Query run in the ADS user interface, enclosed by quotes [default: None]',
        default=None,
        type=str
    )
    parser.add_argument(
        '--save-to-file',
        dest='save',
        help='Save plots to a given format [default: False]',
        choices=['csv'],
        default=False,
        type=str
    )
    parser.add_argument(
        '--plot',
        dest='plot',
        help='Make a plot of the metrics',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--log',
        dest='log',
        help='Plot axis in log-scale',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--token',
        dest='token',
        help='ADS development token',
        default=None,
        type=str
    )

    args = parser.parse_args()

    if args.orcid is None and args.query is None and args.bibcodes is None:
        parser.print_help()
        sys.exit()

    main(
        output_path=args.output,
        figure_format=args.format,
        orcid=args.orcid,
        query=args.query,
        save=args.save,
        plot=args.plot,
        log=args.log,
    )
