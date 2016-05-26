"""
Plot metrics for a given set of bibcodes using the ADS API. This example allows
you to create metrics for i) an ORCiD iD query, ii) a generic ADS query, and
iii) for a list of bibcodes. It will generate the plots that are usuall found
on the ADS Bumblebee interface by clicking Export -> Metrics.

If requested, a PDF document will be created that also includes the simple
metric values with their descriptions, combined with the plots if the user
specifies.

You can also save all plots to disk in CSV format.

Given there is a 2000 limit to the metrics service, you can also request that
the 'Number of Publications' plot be created using the unlimited query search.
Bear in mind, you will have to manually modify max_pages and rows if you are
doing very large searches.
"""

import sys
import numpy
import argparse
import matplotlib
matplotlib.use('TkAgg')
import seaborn  # simply importing this changes matplotlib styles
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas
import ads
import subprocess
from jinja2 import Template


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

    return numpy.array(new_x), numpy.array(new_y)


def step(ax, x, y, label='', color='blue', lw=1):
    """
    Create a step plot that is filled underneath. This is not usually possible
    using the normal ax.step() function
    """
    x_, y_ = stepify(x, y)
    ax.errorbar(x_, y_, label=label, color=color, lw=lw)
    ax.fill_between(x_, 0, y_, color=color, alpha=0.5)


def get_numbers_of_papers(metrics):
    """
    Convert the metrics into a format that is easier to work with. Year-ordered
    numpy arrays.
    """
    publications = metrics['histograms']['publications']

    year, total, year_refereed, refereed = [], [], [], []
    y = list(publications['all publications'].keys())
    y.sort()
    for i in range(len(y)):
        k = y[i]
        year.append(datetime.strptime(k, '%Y'))
        total.append(publications['all publications'][k])
        refereed.append(publications['refereed publications'][k])

    year, total, refereed = \
        numpy.array(year), numpy.array(total), numpy.array(refereed)
    return year, total, refereed


def get_citations_of_papers(metrics):
    """
    Convert the metrics into a format that is easier to work with. Year-ordered
    numpy arrays.
    """
    year_citation, ref_to_ref, ref_to_non_ref, non_ref_to_ref, non_ref_to_non_ref = \
        [], [], [], [], []

    citations = metrics['histograms']['citations']

    y = list(citations['refereed to refereed'].keys())
    y.sort()
    for i in range(len(y)):
        k = y[i]
        year_citation.append(datetime.strptime(k, '%Y'))
        ref_to_ref.append(citations['refereed to refereed'][k])
        ref_to_non_ref.append(citations['refereed to nonrefereed'][k])
        non_ref_to_ref.append(citations['nonrefereed to refereed'][k])
        non_ref_to_non_ref.append(citations['nonrefereed to nonrefereed'][k])

    year_citation, ref_to_ref, ref_to_non_ref, non_ref_to_ref, non_ref_to_non_ref = \
        numpy.array(year_citation), numpy.array(ref_to_ref), \
        numpy.array(ref_to_non_ref), numpy.array(non_ref_to_ref), numpy.array(non_ref_to_non_ref)
    return year_citation, ref_to_ref, ref_to_non_ref, non_ref_to_ref, non_ref_to_non_ref


def get_indices_of_papers(metrics):
    """
    Convert the metrics into a format that is easier to work with. Year-ordered
    numpy arrays.
    """
    year_h, h, g, tori, i10, read10, i100 = [], [], [], [], [], [], []
    y = list(metrics['time series']['h'].keys())
    y.sort()
    for i in range(len(y)):
        k = y[i]
        h.append(metrics['time series']['h'][k])
        g.append(metrics['time series']['g'][k])
        i10.append(metrics['time series']['i10'][k])
        tori.append(metrics['time series']['tori'][k])
        i100.append(metrics['time series']['i100'][k])

        # Normalise read10 Index value by dividing by 10
        read10.append(metrics['time series']['read10'][k]/10.)
        year_h.append(datetime.strptime(k, '%Y'))

    year_h, h, g, tori, i10, read10, i100 = \
        numpy.array(year_h), numpy.array(h), numpy.array(g), numpy.array(tori), \
        numpy.array(i10), numpy.array(read10), numpy.array(i100)
    return year_h, h, g, tori, i10, read10, i100


def get_reads_of_papers(metrics):
    """
    Convert the metrics into a format that is easier to work with. Year-ordered
    numpy arrays.
    """
    year_reads, total, reads_ref = [], [], []
    y = list(metrics['histograms']['reads']['all reads'].keys())
    y.sort()
    for i in range(len(y)):
        k = y[i]
        year_reads.append(datetime.strptime(k, '%Y'))
        total.append(metrics['histograms']['reads']['all reads'][k])
        reads_ref.append(metrics['histograms']['reads']['refereed reads'][k])

    year_reads, total, reads_ref = \
        numpy.array(year_reads), numpy.array(total), numpy.array(reads_ref)
    return year_reads, total, reads_ref


def metrics_to_pandas(metrics):
    """
    Place holder for an attempt to make a generic Pandas object for the metrics
    service. However, for this to work well, you need to know all the possible
    year keys, and so currently as it is written it won't result in necessarily
    all the entries (i.e., there are different number of years in 'reads' and
    'citations', etc.). There is a smarter recursive way to do it, so please
    update if you have time.
    """
    years = metrics['histograms']['publications']['all publications'].keys()
    years.sort()

    data = {}
    tree = ['metrics']

    def expand(m, d, tree):

        try:
            for key in m:
                try:
                    d[':'.join(tree)] = numpy.array([float(m[i]) for i in years])
                except KeyError:
                    tree.append(key)
                    expand(m[key], d, tree)
        except TypeError:
            data[':'.join(tree)] = m
            tree.pop()
            return

        tree.pop()

    expand(metrics, data, tree)

    return pandas.DataFrame(data, index=pandas.DatetimeIndex(years))


def build_latex(metrics, orcid_id=None, plot=None, desc=None):
    """
    Fill in the basic latex template and generate a PDF. This requires the
    user to have PDFLaTeX installed, otherwise it will not work.
    # TODO: add detection of whether PDFLaTeX is installed or not.

    :param metrics: data returned from metrics end point
    :type metrics: JSON

    :param orcid_id: Users ORCiD iD
    :type orcid_id: basestring

    :param plot: does the user want a plot created
    :type plot: boolean
    """

    # Load LaTeX template
    with open('mymetrics.tex.template', 'r') as f:
        latex_template = Template(f.read())

    orcid = '{{\\bf ORCiD iD}}: {}'.format(orcid_id) if orcid_id else ''
    plotpdf = '\\includegraphics[height=0.95\\textheight]{metrics.pdf}' if plot else ''
    desc = desc if desc else ''

    rendered_latex = latex_template.render(
        orcid_id=orcid,
        number_of_papers_total=metrics['basic stats']['number of papers'],
        number_of_papers_ref=metrics['basic stats refereed']['number of papers'],
        normalized_paper_total='{0:.1f}'.format(metrics['basic stats']['normalized paper count']),
        normalized_paper_ref='{0:.1f}'.format(metrics['basic stats refereed']['normalized paper count']),
        number_citing_total=metrics['citation stats']['number of citing papers'],
        number_citing_ref=metrics['citation stats refereed']['number of citing papers'],
        total_cites=metrics['citation stats']['total number of citations'],
        total_cites_ref=metrics['citation stats refereed']['total number of citations'],
        self_cite_total=metrics['citation stats']['number of self-citations'],
        self_cite_ref=metrics['citation stats refereed']['number of self-citations'],
        avg_cite_total='{0:.1f}'.format(metrics['citation stats']['average number of citations']),
        avg_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['average number of citations']),
        med_cite_total=metrics['citation stats']['median number of citations'],
        med_cite_ref=metrics['citation stats refereed']['median number of citations'],
        norm_cite_total='{0:.1f}'.format(metrics['citation stats']['normalized number of citations']),
        norm_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['normalized number of citations']),
        ref_cite_total=metrics['citation stats']['total number of refereed citations'],
        ref_cite_ref=metrics['citation stats refereed']['total number of refereed citations'],
        avg_ref_cite_total='{0:.1f}'.format(metrics['citation stats']['average number of refereed citations']),
        avg_ref_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['average number of refereed citations']),
        med_ref_cite_total=metrics['citation stats']['median number of refereed citations'],
        med_ref_cite_ref=metrics['citation stats refereed']['median number of refereed citations'],
        norm_ref_cite_total='{0:.1f}'.format(metrics['citation stats']['normalized number of refereed citations']),
        norm_ref_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['normalized number of refereed citations']),
        h_total=metrics['indicators']['h'],
        h_ref=metrics['indicators refereed']['h'],
        m_total='{0:.1f}'.format(metrics['indicators']['m']),
        m_ref='{0:.1f}'.format(metrics['indicators refereed']['m']),
        g_total=metrics['indicators']['g'],
        g_ref=metrics['indicators refereed']['g'],
        i10_total=metrics['indicators']['i10'],
        i10_ref=metrics['indicators refereed']['i10'],
        i100_total=metrics['indicators']['i100'],
        i100_ref=metrics['indicators refereed']['i100'],
        tori_total='{0:.1f}'.format(metrics['indicators']['tori']),
        tori_ref='{0:.1f}'.format(metrics['indicators refereed']['tori']),
        riq_total=metrics['indicators']['riq'],
        riq_ref=metrics['indicators refereed']['riq'],
        read10_total='{0:.1f}'.format(metrics['indicators']['read10']),
        read10_ref='{0:.1f}'.format(metrics['indicators refereed']['read10']),
        reads_total=metrics['basic stats']['total number of reads'],
        reads_ref=metrics['basic stats refereed']['total number of reads'],
        avg_reads_total='{0:.1f}'.format(metrics['basic stats']['average number of reads']),
        avg_reads_ref='{0:.1f}'.format(metrics['basic stats refereed']['average number of reads']),
        med_reads_total=metrics['basic stats']['median number of reads'],
        med_reads_ref=metrics['basic stats refereed']['median number of reads'],
        downloads_total=metrics['basic stats']['total number of downloads'],
        downloads_ref=metrics['basic stats refereed']['total number of downloads'],
        downloads_avg='{0:.1f}'.format(metrics['basic stats']['average number of downloads']),
        downloads_avg_ref='{0:.1f}'.format(metrics['basic stats refereed']['average number of downloads']),
        med_downloads=metrics['basic stats']['median number of downloads'],
        med_downloads_ref=metrics['basic stats refereed']['median number of downloads'],
        plot=plotpdf,
        desc=desc
    )

    # Save filled LaTeX template
    with open('mymetrics.tex', 'w') as f:
        f.write(rendered_latex)

    # Build laTeX
    cmd = ['pdflatex', 'mymetrics.tex']
    print('Building LaTeX: {}'.format(' '.join(cmd)))
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if err:
        print('LaTeX compilation error: {}'.format(err))


def save_metrics(metrics):

    with open('mymetrics.txt.template', 'r') as f:
        txt_template = Template(f.read())

        txt_rendered = txt_template.render(
            number_of_papers_total=metrics['basic stats']['number of papers'],
            number_of_papers_ref=metrics['basic stats refereed']['number of papers'],
            normalized_paper_total='{0:.1f}'.format(metrics['basic stats']['normalized paper count']),
            normalized_paper_ref='{0:.1f}'.format(metrics['basic stats refereed']['normalized paper count']),
            number_citing_total=metrics['citation stats']['number of citing papers'],
            number_citing_ref=metrics['citation stats refereed']['number of citing papers'],
            total_cites=metrics['citation stats']['total number of citations'],
            total_cites_ref=metrics['citation stats refereed']['total number of citations'],
            self_cite_total=metrics['citation stats']['number of self-citations'],
            self_cite_ref=metrics['citation stats refereed']['number of self-citations'],
            avg_cite_total='{0:.1f}'.format(metrics['citation stats']['average number of citations']),
            avg_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['average number of citations']),
            med_cite_total=metrics['citation stats']['median number of citations'],
            med_cite_ref=metrics['citation stats refereed']['median number of citations'],
            norm_cite_total='{0:.1f}'.format(metrics['citation stats']['normalized number of citations']),
            norm_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['normalized number of citations']),
            ref_cite_total=metrics['citation stats']['total number of refereed citations'],
            ref_cite_ref=metrics['citation stats refereed']['total number of refereed citations'],
            avg_ref_cite_total='{0:.1f}'.format(metrics['citation stats']['average number of refereed citations']),
            avg_ref_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['average number of refereed citations']),
            med_ref_cite_total=metrics['citation stats']['median number of refereed citations'],
            med_ref_cite_ref=metrics['citation stats refereed']['median number of refereed citations'],
            norm_ref_cite_total='{0:.1f}'.format(metrics['citation stats']['normalized number of refereed citations']),
            norm_ref_cite_ref='{0:.1f}'.format(metrics['citation stats refereed']['normalized number of refereed citations']),
            h_total=metrics['indicators']['h'],
            h_ref=metrics['indicators refereed']['h'],
            m_total=metrics['indicators']['m'],
            m_ref=metrics['indicators refereed']['m'],
            g_total=metrics['indicators']['g'],
            g_ref=metrics['indicators refereed']['g'],
            i10_total=metrics['indicators']['i10'],
            i10_ref=metrics['indicators refereed']['i10'],
            i100_total=metrics['indicators']['i100'],
            i100_ref=metrics['indicators refereed']['i100'],
            tori_total='{0:.1f}'.format(metrics['indicators']['tori']),
            tori_ref='{0:.1f}'.format(metrics['indicators refereed']['tori']),
            riq_total=metrics['indicators']['riq'],
            riq_ref=metrics['indicators refereed']['riq'],
            read10_total='{0:.1f}'.format(metrics['indicators']['read10']),
            read10_ref='{0:.1f}'.format(metrics['indicators refereed']['read10']),
            reads_total=metrics['basic stats']['total number of reads'],
            reads_ref=metrics['basic stats refereed']['total number of reads'],
            avg_reads_total='{0:.1f}'.format(metrics['basic stats']['average number of reads']),
            avg_reads_ref='{0:.1f}'.format(metrics['basic stats refereed']['average number of reads']),
            med_reads_total=metrics['basic stats']['median number of reads'],
            med_reads_ref=metrics['basic stats refereed']['median number of reads'],
            downloads_total=metrics['basic stats']['total number of downloads'],
            downloads_ref=metrics['basic stats refereed']['total number of downloads'],
            downloads_avg='{0:.1f}'.format(metrics['basic stats']['average number of downloads']),
            downloads_avg_ref='{0:.1f}'.format(metrics['basic stats refereed']['average number of downloads']),
            med_downloads=metrics['basic stats']['median number of downloads'],
            med_downloads_ref=metrics['basic stats refereed']['median number of downloads'],
        )

    with open('metrics.txt', 'w') as f:
        f.write(txt_rendered)


def get_numbers_of_papers_raw(sq):
    """
    Returns the number of reads vs year. This is not affected by the limit
    of the number of bibcodes required by the /metrics end point
    """

    # Do it in two steps because I'm too lazy to do it in a nice way
    years = {'total': {}, 'ref': {}}
    for article in sq:
        if article.year is None:
            y = article.pubdate.split('-')[0]
        else:
            y = article.year

        try:
            years['total'][y] += 1
        except KeyError:
            years['total'][y] = 1

        if 'REFEREED' in article.property:
            try:
                years['ref'][y] += 1
            except KeyError:
                years['ref'][y] = 1

    year = list(years['total'].keys())

    year.sort()
    number = []
    number_ref = []
    y = []
    for i in range(len(year)):
        k = year[i]
        y.append(datetime.strptime(k, '%Y'))
        number.append(years['total'][k])
        number_ref.append(years['ref'].get(k, 0))

    return numpy.array(y), numpy.array(number), numpy.array(number_ref)


def main(output_path, figure_format, orcid=False, bibcodes=False, query=False, save=False, plot=False, printable=False, test=False, desc=None):

    # Imports should not be here, but I don't care....
    if test:
        import ads.sandbox as ads
    else:
        import ads

    fl = ['id', 'bibcode']
    rows = 2000
    max_pages = 1

    print('Using rows: {} with max_pages: {}'.format(rows, max_pages))

    # See what the user has given to generate the metrics plot
    if query:
        sq = ads.SearchQuery(q=query, fl=fl, rows=rows, max_pages=max_pages)
        sq.execute()
        bibcodes = [i.bibcode for i in sq.articles]
        print('You gave a query: {}'.format(query))
        print('Found {} bibcodes (e.g., {})'.format(len(bibcodes), bibcodes[0:4]))
    elif orcid:
        query = 'orcid:{}'.format(orcid)
        sq = ads.SearchQuery(q=query, fl=fl, rows=rows, max_pages=max_pages)
        sq.execute()
        bibcodes = [i.bibcode for i in sq.articles]
        print('You gave an ORCiD iD: {}'.format(orcid))
        print('Found {} bibcodes (e.g., {})'.format(len(bibcodes), bibcodes[0:4]))
    elif bibcodes:
        sq = False
        print('You gave {} bibcodes: {}'.format(len(bibcodes), bibcodes[0:4]))
    else:
        sys.exit()

    # Collect the metrics from the API
    mq = ads.MetricsQuery(bibcodes=bibcodes)
    metrics = mq.execute()

    if plot:
        # Number of papers
        y, t, r = get_numbers_of_papers(metrics)

        number = dict(name='numbers', year=y, total=t, refereed=r)
        # Number of citations
        y, r2r, r2nr, nr2r, nr2nr = get_citations_of_papers(metrics)
        citation = dict(name='citations', year=y, ref_to_ref=r2r, non_ref_to_ref=nr2r, ref_to_non_ref=r2nr, non_ref_to_non_ref=nr2nr)

        # Indices
        y, h, g, tori, i10, read10, i100 = get_indices_of_papers(metrics)
        index = dict(name='indices', year=y, h=h, g=g, tori=tori, i10=i10, read10=read10, i100=i100)

        # Number of reads
        y, t, rr = get_reads_of_papers(metrics)
        reads = dict(name='reads', year=y, total=t, reads_ref=rr)

        # Define the figure and the axes
        fig = plt.figure(0, figsize=(8.27, 11.69))
        ax1 = fig.add_subplot(411)
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)

        # Number of papers
        step(ax1, number['year'], number['total'] - number['refereed'], label='Not refereed', color='green')
        step(ax1, number['year'], number['refereed'], label='Refereed', color='blue')
        ax1.set_ylim([0, max(number['total'])+1])
        ax1.set_ylabel('Numer of papers')
        leg1 = ax1.legend(loc=0)
        leg1.draw_frame(False)

        # Number of citations
        step(ax2, citation['year'], citation['ref_to_ref'], label='Ref. citations to ref. papers', color='blue')
        step(ax2, citation['year'], citation['ref_to_non_ref'], label='Ref. citations to non ref. papers', color='green')
        step(ax2, citation['year'], citation['non_ref_to_ref'], label='Non ref. citations to ref. papers', color='gold')
        step(ax2, citation['year'], citation['non_ref_to_non_ref'], label='Non ref. citations to non ref. papers', color='red')

        ax2.set_ylabel('Numer of citations')
        max_citation = max(
            citation['ref_to_ref'].max(),
            citation['ref_to_non_ref'].max(),
            citation['non_ref_to_ref'].max(),
            citation['non_ref_to_non_ref'].max()
        )
        ax2.set_ylim([0, max_citation+1])
        leg2 = ax2.legend(loc=0)
        leg2.draw_frame(False)

        # Indices
        ax3.errorbar(index['year'], index['h'], label='h Index', color='blue', lw=2, ls='-')
        ax3.errorbar(index['year'], index['g'], label='g Index', color='green', lw=2, ls='-')
        ax3.errorbar(index['year'], index['i10'], label='i10 Index', color='gold', lw=2, ls='-')
        ax3.errorbar(index['year'], index['tori'], label='tori Index', color='red', lw=2, ls='-')
        ax3.errorbar(index['year'], index['i100'], label='i100 Index', color='purple', lw=2, ls='-')
        ax3.errorbar(index['year'], index['read10'], label='read10 Index', color='darkblue', lw=2, ls='-')
        max_index = max(h.max(), g.max(), i10.max(), tori.max(), i100.max(), read10.max())

        ax3.set_ylim([0, max_index+1])
        leg3 = ax3.legend(loc=0, ncol=2)
        leg3.draw_frame(False)

        # Number of reads
        step(ax4, reads['year'], reads['total'] - reads['reads_ref'], label='Non refereed', color='green')
        step(ax4, reads['year'], reads['reads_ref'], label='Refereed', color='blue')
        max_reads = max(
            reads['total'].max(),
            reads['reads_ref'].max()
        )

        min_year = reads['year'][0]
        for i in range(len(reads['year'])):
            if reads['total'][i] > 0 or reads['reads_ref'][i] > 0:
                break
            min_year = reads['year'][i]

        ax4.set_xlim([min_year, reads['year'].max()])
        ax4.set_ylim([0, max_reads+1])

        ax4.set_xlabel('Year')
        ax4.set_ylabel('Number of reads')
        leg4 = ax4.legend(loc=0)
        leg4.draw_frame(False)

        figure_path = '{}/metrics.{}'.format(output_path, figure_format)
        plt.savefig(figure_path)

    # Save to disk if requested
    if save == 'csv':
        for output in [number, citation, index, reads]:
            with open('{}/{}.{}'.format(output_path, output['name'], save), 'w') as f:

                keys = [i for i in output.keys() if i != 'name' and i != 'year']
                f.write('#year,{}\n'.format(','.join(keys)))

                for i in range(len(output['year'])):
                    f.write('{year},{other}\n'.format(
                        year=output['year'][i].year,
                        other=','.join([str(output[k][i]) for k in keys])
                    ))

        save_metrics(metrics)

    # Does the user want a printable PDF?
    if printable:
        build_latex(metrics, orcid_id=orcid, plot=plot, desc=desc)


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
        '--bibcodes',
        dest='bibcodes',
        help='List of bibcodes [default: None]',
        default=None,
        nargs='+',
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
        '--printable',
        dest='printable',
        help='Create a nice PDF format to print',
        action='store_true',
        default=False
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
        '--description',
        dest='description',
        help='Add a description at the top of the PDF',
        default=None
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
        bibcodes=args.bibcodes,
        save=args.save,
        printable=args.printable,
        plot=args.plot,
        test=args.test,
        desc=args.description
    )
