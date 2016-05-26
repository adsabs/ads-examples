"""
Plot the search facet plots that are found on the ADS search results page.
This example allows you to create metrics for i) an ORCiD iD query, and ii) a
generic ADS query.

You can also save all plots to disk in CSV format.

There is a limit on the number of items returned. To change this, you can
modify the rows and max_pages.

rows: number of items returned in a single request (max: 2000)
max_pages: number of times to iterate over the rows returned (starts: 0)
"""

import sys
import numpy
import argparse
import matplotlib
matplotlib.use('TkAgg')
import seaborn  # simply importing this changes matplotlib styles
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import ads


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

    binsize = dyear(binsize)

    new_x, new_y = [x[0]], [0]
    for i in range(len(x)):
        new_x.extend([x[i], x[i]+binsize])
        new_y.extend([y[i], y[i]])

    # Add tails
    new_x.append(x[-1]+binsize)
    new_y.append(0)

    return numpy.array(new_x) - binsize/2.0, numpy.array(new_y)


def step(ax, x, y, label='', color='blue', lw=1):
    """
    Create a step plot that is filled underneath. This is not usually possible
    using the normal ax.step() function
    """
    x_, y_ = stepify(x, y)
    ax.errorbar(x_, y_, label=label, color=color, lw=lw)
    ax.fill_between(x_, 0, y_, color=color, alpha=0.5)


def get_numbers_of_papers_raw(p):
    """
    Returns the number of reads vs year. This is not affected by the limit
    of the number of bibcodes required by the /metrics end point
    :param p: list of ads.Article
    :type p: list
    """

    # Do it in two steps because I'm too lazy to do it in a nice way
    years = {
        'total papers': {}, 'ref papers': {},
    }

    for article in p:
        if article.year is None:
            y = article.pubdate.split('-')[0]
        else:
            y = article.year

        try:
            years['total papers'][y] += 1
        except KeyError:
            years['total papers'][y] = 1

        if 'REFEREED' in article.property:
            try:
                years['ref papers'][y] += 1
            except KeyError:
                years['ref papers'][y] = 1

    year = [int(i) for i in years['total papers'].keys()]

    # A little bit of a hack
    min_year = min(year)
    max_year = max(year)
    year = [str(i) for i in numpy.arange(min_year, max_year+1, 1)]

    # year.sort()
    total_paper, ref_paper = [], []
    y = []

    for i in range(len(year)):
        k = year[i]

        y.append(datetime.strptime(k, '%Y'))
        total_paper.append(years['total papers'].get(k, 0))
        ref_paper.append(years['ref papers'].get(k, 0))

    return (numpy.array(i) for i in [
        y, total_paper, ref_paper
    ])


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


def main(output_path, figure_format, orcid=False, query=False, save=False, plot=False, test=False, log=False, rows=200, max_pages=1):

    # Imports should not be here, but I don't care....
    if test:
        import ads.sandbox as ads
    else:
        import ads

    fl = ['bibcode', 'year', 'pubdate', 'read_count', 'citation_count', 'property']

    print('Using rows: {} with max_pages: {}'.format(rows, max_pages))
    print('Field parameters requested: {}'.format(fl))

    # See what the user has given to generate the metrics plot
    if query:
        sq = ads.SearchQuery(q=query, fl=fl, rows=rows, max_pages=max_pages, sort='citation_count desc')
        p = list(sq)
        bibcodes = [i.bibcode for i in sq.articles]
        print('You gave a query: {}'.format(query))
        print('Found {} bibcodes (e.g., {})'.format(len(bibcodes), bibcodes[0:4]))
    elif orcid:
        query = 'orcid:{}'.format(orcid)
        sq = ads.SearchQuery(q=query, fl=fl, rows=rows, max_pages=max_pages, sort='citation_count desc')
        p = list(sq)
        bibcodes = [i.bibcode for i in sq.articles]
        print('You gave an ORCiD iD: {}'.format(orcid))
        print('Found {} bibcodes (e.g., {})'.format(len(bibcodes), bibcodes[0:4]))
    else:
        sys.exit()

    # Number found
    print('Number of results found: {}'.format(sq.response.numFound))
    print('Number of results downloaded: {}'.format(len(sq.articles)))

    # Number of papers
    y, tot_pap, ref_pap = get_numbers_of_papers_raw(p)

    # Collect the metrics from the API
    if plot:
        # Define the figure and the axes
        fig = plt.figure(0, figsize=(8.27, 11.69))
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        # Number of papers
        step(ax1, y, tot_pap - ref_pap, label='Not refereed: {}'.format(tot_pap.sum() - ref_pap.sum()), color='green')
        step(ax1, y, ref_pap, label='Refereed: {}'.format(ref_pap.sum()), color='blue')

        y_max = max((tot_pap-ref_pap).max(), ref_pap.max()) + 1
        ax1.set_ylim([0, y_max])
        ax1.set_ylabel('Numer of papers')
        ax1.set_xlabel('Year')
        leg1 = ax1.legend(loc=0)
        leg1.draw_frame(False)

        # Number of citations
        tot_cite = numpy.array([i.citation_count for i in sq.articles])
        h = h_index(tot_cite)
        ax2.errorbar(numpy.arange(1, tot_cite.size+1, 1), tot_cite, label='Total citations: {}'.format(int(tot_cite.sum())), ls='-', color='blue', lw=3, alpha=0.5)
        h_x = numpy.arange(0, h+1, 1)
        h_y = numpy.array([h for i in h_x])
        ax2.errorbar(h_x, h_y, lw=3, color='black', alpha=0.5, label='H-index: {}'.format(h))
        ax2.errorbar(h_y, h_x, lw=3, color='black', alpha=0.5)

        ax2.set_ylabel('Total numer of citations per paper')
        leg2 = ax2.legend(loc=0)
        leg2.draw_frame(False)

        y_max = tot_cite.max() + 1
        y_min = 0
        if log:
            ax2.set_yscale('log')

        ax2.set_ylim([y_min, y_max])

        x_max = tot_cite.size + 1
        ax2.set_xlim([0, x_max])

        # Number of reads
        tot_read = [i.read_count for i in sq.articles]
        tot_read.sort(reverse=True)
        tot_read = numpy.array(tot_read)

        h = h_index(tot_read)
        ax3.errorbar(numpy.arange(1, tot_read.size+1, 1), tot_read, label='Total reads: {}'.format(int(tot_read.sum())), ls='-', color='blue', lw=3, alpha=0.5)

        h_x = numpy.arange(0, h+1, 1)
        h_y = numpy.array([h for i in h_x])
        ax3.errorbar(h_x, h_y, lw=3, color='black', alpha=0.5, label='H-index: {}'.format(h))
        ax3.errorbar(h_y, h_x, lw=3, color='black', alpha=0.5)

        ax3.set_ylabel('Total numer of reads per paper')
        leg3 = ax3.legend(loc=0)
        leg3.draw_frame(False)
        if log:
            ax3.set_yscale('log')

        ax3.set_ylim([0, tot_read.max()+1])

        im = plt.imread('ads_logo.jpg')
        newax = fig.add_axes([0.1, 0.9, 0.8, 0.1], anchor='NW', aspect='equal')
        newax.imshow(im)
        newax.axis('off')

        figure_path = '{}/search_metrics.{}'.format(output_path, figure_format)
        plt.savefig(figure_path)

    # Save to disk if requested
    if save == 'csv':
        with open('{}/number.csv'.format(output_path), 'w') as f:

                f.write('#year,total_number,refereed_number\n')
                for i in range(len(y)):
                    f.write('{year},{tot},{ref}\n'.format(
                        year=y[i].year,
                        tot=tot_pap[i],
                        ref=ref_pap[i]
                    ))
        with open('{}/citation_read.csv'.format(output_path), 'w') as f:
            f.write('#bibcode,citation_count,read_count\n')
            for i in sq.articles:
                f.write('{bib},{cit},{read}\n'.format(
                    bib=i.bibcode,
                    cit=i.citation_count,
                    read=i.read_count
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
        '--test',
        dest='test',
        help='Run using ADS sandbox environment',
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
        '--rows',
        dest='rows',
        help='Maximum number of rows to request',
        default=200,
        type=int
    )
    parser.add_argument(
        '--max-pages',
        dest='max_pages',
        help='Maximum number of pages to access from the response',
        default=1,
        type=int
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
        test=args.test,
        log=args.log,
        rows=args.rows,
        max_pages=args.max_pages
    )
