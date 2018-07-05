# encode: utf-8
"""
Convert your ADS Libraries into CSV output
"""

import os
import math
import requests
import argparse

token = None

def get_config():
    """
    Load ADS developer key from file
    :return: str
    """
    global token
    if token is None:
        try:
            with open(os.path.expanduser('~/.ads/dev_key')) as f:
                token = f.read().strip()
        except IOError:
            print('The script assumes you have your ADS developer token in the'
                  'folder: {}'.format())

    return {
        'url': 'https://api.adsabs.harvard.edu/v1/biblib',
        'headers': {
            'Authorization': 'Bearer:{}'.format(token),
            'Content-Type': 'application/json',
        }
    }


def get_libraries():
    """
    Get a list of all my libraries and their meta-data
    :return: list
    """

    config = get_config()

    r = requests.get(
        '{}/libraries'.format(config['url']),
        headers=config['headers']
    )

    # Collect a list of all of our libraries, this will include the number
    # of documents, the name, description, id, and other meta data
    try:
        data = r.json()['libraries']
        return data
    except ValueError:
        raise ValueError(r.text)


def get_library(library_id, num_documents):
    """
    Get the content of a library when you know its id. As we paginate the
    requests from the private library end point for document retrieval,
    we have to repeat requests until we have all documents.

    :param library_id: identifier of the library
    :type library_id:
    :param num_documents: number of documents in the library
    :type num_documents: int

    :return: list
    """

    config = get_config()

    start = 0
    rows = 25
    num_paginates = int(math.ceil(num_documents / (1.0*rows)))

    documents = []
    for i in range(num_paginates):
        print('Pagination {} out of {}'.format(i+1, num_paginates))

        r = requests.get(
            '{}/libraries/{id}?start={start}&rows={rows}'.format(
                config['url'],
                id=library_id,
                start=start,
                rows=rows
            ),
            headers=config['headers']
        )

        # Get all the documents that are inside the library
        try:
            data = r.json()['documents']
        except ValueError:
            raise ValueError(r.text)

        documents.extend(data)

        start += rows

    return documents


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        '--save-to-file',
        dest='output_file',
        help='Save my libraries to this file.',
        default='private_libraries.csv'
    )
    args = parser.parse_args()
    output_file = args.output_file

    # Collect libraries and their meta-data (no documents at this stage)
    libraries = get_libraries()

    # Prepare output data
    output = {
        'names': [],
        'num_documents': [],
        'bibcodes': [],
    }

    # Collect all the documents/bibcodes from each library
    for library in libraries:

        print(
            'Collecting library: {} [{}]'
            .format(library['name'], library['id'])
        )

        documents = get_library(
            library_id=library['id'],
            num_documents=library['num_documents']
        )

        output['names'].append(library['name'])
        output['num_documents'].append(library['num_documents'])
        output['bibcodes'].append(documents)

    # Write to file, could be above, but just separate for clarity
    with open(output_file, 'w') as f:

        # Header of file
        f.write('#name,num_documents,bibcodes\n')

        for i in range(len(libraries)):

            f.write(
                '{name},{num_documents},{bibcodes}\n'.format(
                    name=output['names'][i].replace(',', ';'),
                    num_documents=output['num_documents'][i],
                    bibcodes='\t'.join(output['bibcodes'][i])
                )
            )
