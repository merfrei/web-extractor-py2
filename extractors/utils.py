"""Utils to be used for extractors.
Here will be included all the code to be shared for every extractor or that
does not specifically belong to any of them.
"""


from collections import Counter


def most_common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]


def get_master_path(*paths, **kwargs):
    """ Find the common parts of the paths when the inputs have a "master path"
    The inputs must be of the same length
    >>> get_master_path(['/html/body/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/ul/li[1]/form/div/div[1]/span[1]',
                         '/html/body/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/ul/li[2]/form/div/div[1]/span[1]'])
    '/html/body/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/ul/li/form/div/div[1]/span[1]'
    """
    separator = '/'
    if 'separator' in kwargs:
        separator = kwargs['separator']
    # Split
    paths_splitted = [p.split(separator) for p in paths]
    # Look for the most common length
    common_length = most_common([len(p) for p in paths_splitted])
    # Remove incorrect length
    paths_splitted = [p for p in paths_splitted if len(p) == common_length]

    master_path = []
    for i in range(common_length):
        values = [paths[i].split('[')[0] for paths in paths_splitted]
        common_value = most_common(values)
        values = set([paths[i] for paths in paths_splitted if common_value in paths[i]])
        if len(values) == 1:
            master_path.append(values.pop())
        else:
            master_path.append(common_value)

    return separator.join(master_path)
