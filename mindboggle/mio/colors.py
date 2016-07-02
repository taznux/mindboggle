#!/usr/bin/env python
"""
Colormap-related functions

Authors:
    - Arno Klein, 2016  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2016,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""


def distinguishable_colors(ncolors, backgrounds=[[0,0,0],[1,1,1]],
                           save_csv=True, plot_colormap=True, verbose=True):
    """
    Create a colormap of perceptually distinguishable colors.

    This program is a Python program based on Tim Holy's 2010-2011
    BSD-licensed Matlab program "distinguishable_colors.m"
    (https://www.mathworks.com/matlabcentral/fileexchange/
     29702-generate-maximally-perceptually-distinct-colors):

    "This function generates a set of colors which are distinguishable
    by reference to the "Lab" color space, which more closely matches
    human color perception than RGB. Given an initial large list of possible
    RGB colors, it iteratively chooses the entry in the list that is farthest
    (in Lab space) from all previously-chosen entries. While this "greedy"
    algorithm does not yield a global maximum, it is simple and efficient.
    Moreover, the sequence of colors is consistent no matter how many you
    request, which facilitates the users' ability to learn the color order
    and avoids major changes in the appearance of plots when adding or
    removing lines."

    Parameters
    ----------
    ncolors : integer
        number of colors for the colormap
    backgrounds : list of list(s) of 3 elements between 0 and 1
        rgb background colors to initialize and distinguish from
    save_csv : Boolean
        save colormap as csv file?
    plot_colormap : Boolean
        plot colormap as horizontal bar chart?
    verbose : Boolean
        print to stdout?

    Returns
    -------
    colors : numpy ndarray of ndarrays of 3 floats between 0 and 1
        rgb colormap

    Examples
    --------
    >>> from mindboggle.mio.colors import distinguishable_colors
    >>> ncolors = 31
    >>> backgrounds = [[0,0,0],[1,1,1]]
    >>> save_csv = False
    >>> plot_colormap = False
    >>> verbose = False
    >>> colors = distinguishable_colors(ncolors, backgrounds,
    ...     save_csv, plot_colormap, verbose)
    >>> colors[0]
    array([ 0.62068966,  0.06896552,  1.        ])
    >>> colors[1]
    array([ 0.       ,  0.5862069,  0.       ])
    >>> colors[2]
    array([ 0.75862069,  0.20689655,  0.        ])

    """
    import numpy as np
    import matplotlib.pyplot as plt
    from colormath.color_objects import LabColor, AdobeRGBColor
    from colormath.color_conversions import convert_color
    from colormath.color_diff import delta_e_cie2000

    filename = "colormap_of_{0}_distinguishable_colors".format(ncolors)

    # ------------------------------------------------------------------------
    # Generate a sizable number of RGB triples. This represents our space of
    # possible choices. By starting in RGB space, we ensure that all of the
    # colors can be generated by the monitor:
    # ------------------------------------------------------------------------
    n_grid = 30  # number of grid divisions along each axis in RGB space
    x = np.linspace(0, 1, num=n_grid, endpoint=True)
    R, G, B = np.meshgrid(x, x, x)
    ncolors_total = np.size(R)
    RGB = np.vstack([np.ravel(R), np.ravel(G), np.ravel(B)])
    RGB = [[RGB[0][icolor], RGB[1][icolor], RGB[2][icolor]]
           for icolor in range(ncolors_total)]
    if ncolors > ncolors_total:
        raise IOError("You can't readily distinguish that many colors")

    # ------------------------------------------------------------------------
    # Convert to Lab color space which better represents human perception:
    # ------------------------------------------------------------------------
    # https://python-colormath.readthedocs.io/en/latest/illuminants.html
    lab_colors = []
    for rgb in RGB:
        lab = convert_color(AdobeRGBColor(rgb[0],
                                          rgb[1],
                                          rgb[2]), LabColor)
        lab_colors.append(lab)

    bg_lab_colors = []
    for bg_rgb in backgrounds:
        bg_lab = convert_color(AdobeRGBColor(bg_rgb[0],
                                             bg_rgb[1],
                                             bg_rgb[2]), LabColor)
        bg_lab_colors.append(bg_lab)

    # ------------------------------------------------------------------------
    # If the user specified multiple background colors, compute differences
    # between the candidate colors and the background colors:
    # ------------------------------------------------------------------------
    min_dx = np.inf * np.ones(ncolors_total)
    if backgrounds:
        for bg_lab_color in bg_lab_colors:
            # Store difference from closest previously-chosen color:
            for icolor_total, lab_color in enumerate(lab_colors):
                dx = delta_e_cie2000(lab_color, bg_lab_color)
                min_dx[icolor_total] = min(dx, min_dx[icolor_total])

    # ------------------------------------------------------------------------
    # Iteratively pick the color that maximizes the difference
    # with the nearest already-picked color:
    # ------------------------------------------------------------------------
    # Initialize by making the "previous" color equal to the last background:
    last_lab_color = bg_lab_colors[-1]
    colors = np.zeros((ncolors, 3))
    for icolor in range(ncolors):

        # Find the difference of the last color from all colors on the list:
        for icolor_total, lab_color in enumerate(lab_colors):
            dx = delta_e_cie2000(lab_color, last_lab_color)
            min_dx[icolor_total] = min(dx, min_dx[icolor_total])

        # Find the entry farthest from all previously chosen colors:
        imax_dx = np.argmax(min_dx)

        # Store distant color:
        colors[icolor] = RGB[imax_dx]

        # Prepare for next iteration:
        last_lab_color = lab_colors[imax_dx]

    # ------------------------------------------------------------------------
    # Plot the colormap as a horizontal bar chart:
    # ------------------------------------------------------------------------
    if plot_colormap:
        if verbose:
            print("RGB values:")
        plt.figure(ncolors, figsize=(5, 10))
        for icolor in range(ncolors):
            ax = plt.subplot(ncolors, 1, icolor + 1)
            plt.axis("off")
            rgb = colors[icolor]
            #rgb = [[rgb.rgb_r, rgb.rgb_g, rgb.rgb_b]]
            if verbose:
                print(rgb)
            plt.barh(0, 50, 1, 0, color=rgb)
            plt.savefig(filename + ".png")
        if verbose:
            print("Colormap image saved to {0}".format(filename + ".png"))

    # ------------------------------------------------------------------------
    # Save the colormap as a csv file:
    # ------------------------------------------------------------------------
    if save_csv:
        np.savetxt(filename + ".csv", colors, fmt='%.18e', delimiter=',',
                   newline='\n', header='')
        if verbose:
            print("Colormap saved to {0}".format(filename + ".csv"))

    return colors


def label_adjacency_matrix(label_file, ignore_values=[-1, 999], add_value=0,
                           save_table=True, output_format='csv',
                           verbose=True):
    """
    Extract surface or volume label boundaries, find unique label pairs,
    and write adjacency matrix (useful for constructing a colormap).

    Each row of the (upper triangular) adjacency matrix corresponds to an
    index to a unique label, where each column has a 1 if the label indexed
    by that column is adjacent to the label indexed by the row.

    Parameters
    ----------
    label_file : string
        path to VTK surface file or nibabel-readable volume file with labels
    ignore_values : list of integers
        labels to ignore
    add_value : integer
        value to add to labels
    matrix : pandas dataframe
        adjacency matrix
    save_table : Boolean
        output table file?
    output_format : string
        format of adjacency table file name (currently only 'csv')
    verbose : Boolean
        print to stdout?

    Returns
    -------
    labels : list
        label numbers
    matrix : pandas DataFrame
        adjacency matrix
    output_table : string
        adjacency table file name

    Examples
    --------
    >>> from mindboggle.mio.colors import label_adjacency_matrix
    >>> from mindboggle.mio.fetch_data import prep_tests
    >>> urls, fetch_data = prep_tests()
    >>> ignore_values = [-1, 0]
    >>> add_value = 0
    >>> save_table = False
    >>> output_format = 'csv'
    >>> verbose = False
    >>> label_file = fetch_data(urls['left_manual_labels'], '', '.vtk')
    >>> labels, matrix, output_table = label_adjacency_matrix(label_file,
    ...     ignore_values, add_value, save_table, output_format, verbose)
    >>> matrix.lookup([20,21,22,23,24,25,26,27,28,29],
    ...               [35,35,35,35,35,35,35,35,35,35])
    array([ 0.,  1.,  0.,  0.,  0.,  0.,  0.,  1.,  1.,  1.])

    >>> label_file = fetch_data(urls['freesurfer_labels'], '', '.nii.gz')
    >>> labels, matrix, output_table = label_adjacency_matrix(label_file,
    ...     ignore_values, add_value, save_table, output_format, verbose)
    >>> matrix.lookup([4,5,7,8,10,11,12,13,14,15], [4,4,4,4,4,4,4,4,4,4])
    array([ 1.,  1.,  0.,  0.,  0.,  1.,  0.,  0.,  1.,  0.])

    """
    import numpy as np
    import pandas as pd
    from nibabel import load
    from scipy import ndimage

    from mindboggle.guts.mesh import find_neighbors
    from mindboggle.guts.segment import extract_borders
    from mindboggle.mio.vtks import read_vtk

    # Use Mindboggle's extract_borders() function for surface VTK files:
    if label_file.endswith('.vtk'):
        f1,f2,f3, faces, labels, f4, npoints, f5 = read_vtk(label_file,
                                                            True, True)
        neighbor_lists = find_neighbors(faces, npoints)
        return_label_pairs = True
        indices_borders, label_pairs, f1 = extract_borders(list(range(npoints)),
            labels, neighbor_lists, ignore_values, return_label_pairs)

        output_table = 'adjacent_surface_labels.' + output_format

    # Use scipy to dilate volume files to find neighboring labels:
    elif label_file.endswith('.nii.gz'):

        L = load(label_file).get_data()
        unique_volume_labels = np.unique(L)

        label_pairs = []
        for label in unique_volume_labels:

            if label not in ignore_values:

                B = L * np.logical_xor(ndimage.binary_dilation(L==int(label)),
                                       (L==int(label)))
                neighbor_labels = np.unique(np.ravel(B))

                for neigh in neighbor_labels:
                    if neigh > 0 and neigh in unique_volume_labels:
                    #        and neigh%2==(int(label)%2):
                        label_pairs.append([int(label), int(neigh)])

        output_table = 'adjacent_volume_labels.' + output_format

    else:
        raise IOError("Use appropriate input file type.")

    # Find unique pairs (or first two of each list):
    pairs = []
    for pair in label_pairs:
        new_pair = [int(pair[0]) + add_value,
                    int(pair[1]) + add_value]
        if new_pair not in pairs:
            pairs.append(new_pair)

    # Write adjacency matrix:
    unique_labels = np.unique(pairs)
    nlabels = np.size(unique_labels)
    matrix = np.zeros((nlabels, nlabels))
    for pair in pairs:
        index1 = [i for i, x in enumerate(unique_labels) if x == pair[0]]
        index2 = [i for i, x in enumerate(unique_labels) if x == pair[1]]
        matrix[index1, index2] = 1

    df1 = pd.DataFrame({'ID': unique_labels}, index=None)
    df2 = pd.DataFrame(matrix, index=None)
    df2.columns = unique_labels
    matrix = pd.concat([df1, df2], axis=1)

    if save_table:
        if output_format == 'csv':
            matrix.to_csv(output_table, index=False)
            if verbose:
                print("Adjacency matrix saved to {0}".format(output_table))
        else:
            raise IOError("Set appropriate output file format.")
    else:
        output_table = None

    labels = list(unique_labels)

    return labels, matrix, output_table


def group_colors(colormap, adjacency_matrix=[], IDs=[], names=[], groups=[],
                 save_text_files=True, plot_colors=True,
                 plot_graphs=True, out_dir='.', verbose=True):
    """
    This greedy algoritm reorders a colormap so that labels assigned to
    the same group have more similar colors, but within a group (usually
    of adjacent labels), the colors are reordered so that adjacent labels
    have dissimilar colors:

    1. Convert colormap to Lab color space
       which better represents human perception.
    2. Load a binary (or weighted) adjacency matrix, where each row or column
       represents a label, and each value signifies whether (or the degree
       to which) a given pair of labels are adjacent.
       If a string (file) is provided instead of a numpy ndarray:
            column 0 = label "ID" number
            column 1 = label "name"
            column 2 = "group" number (each label is assigned to a group)
            columns 3... = label adjacency matrix
    3. Sort labels by decreasing number of adjacent labels (adjacency sum).
    4. Order label groups by decreasing maximum adjacency sum.
    5. Create a similarity matrix for pairs of colors.
    6. Sort colors by decreasing perceptual difference from all other colors.
    7. For each label group:
        7.1. Select unpicked colors for group that are similar to the first
             unpicked color (unpicked colors were sorted above by decreasing
             perceptual difference from all other colors).
        7.2. Reorder subgraph colors according to label adjacency sum
             (decreasing number of adjacent labels).
    8. Assign new colors.

    For plotting graphs and colormap:

    1. Convert the matrix to a graph, where each node represents a label
       and each edge represents the adjacency value between connected nodes.
    2. Break up the graph into subgraphs, where each subgraph contains labels
       assigned the same group number (which usually means they are adjacent).
    3. Plot the colormap and colored sub/graphs.

    Parameters
    ----------
    colormap : string or numpy ndarray of ndarrays of 3 floats between 0 and 1
        csv file containing rgb colormap, or colormap array
    adjacency_matrix : string or NxN numpy ndarray (N = number of labels)
        csv file containing label adjacency matrix or matrix itself
    IDs : list of integers
        label ID numbers
    names : list of strings
        label names
    groups : list of integers
        label group numbers (one per label)
    save_text_files : Boolean
        save colormap as csv and json files?
    plot_colors : Boolean
        plot colormap as horizontal bar chart?
    plot_graphs : Boolean
        plot colormap as graphs?
    out_dir : string
        output directory path
    verbose : Boolean
        print to stdout?

    Returns
    -------
    colors : numpy ndarray of ndarrays of 3 floats between 0 and 1
        rgb colormap

    Examples
    --------
    >>> # Get colormap:
    >>> from mindboggle.mio.colors import distinguishable_colors
    >>> colormap = distinguishable_colors(ncolors=31,
    ...     backgrounds=[[0,0,0],[1,1,1]],
    ...     save_csv=False, plot_colormap=False, verbose=False)
    >>> # Get adjacency matrix:
    >>> from mindboggle.mio.colors import label_adjacency_matrix
    >>> from mindboggle.mio.fetch_data import prep_tests
    >>> urls, fetch_data = prep_tests()
    >>> label_file = fetch_data(urls['left_manual_labels'], '', '.vtk')
    >>> IDs, adjacency_matrix, output_table = label_adjacency_matrix(label_file,
    ...     ignore_values=[-1, 0], add_value=0, save_table=False,
    ...     output_format='', verbose=False)
    >>> adjacency_matrix = adjacency_matrix.values
    >>> adjacency_matrix = adjacency_matrix[:, 1::]
    >>> # Reorganize colormap:
    >>> from mindboggle.mio.colors import group_colors
    >>> from mindboggle.mio.labels import DKTprotocol
    >>> dkt = DKTprotocol()
    >>> save_text_files = True #False
    >>> plot_colors = False
    >>> plot_graphs = False
    >>> out_dir = '.'
    >>> verbose = False
    >>> #IDs = dkt.DKT31_numbers
    >>> names = dkt.DKT31_names #dkt.left_cerebrum_cortex_DKT31_names
    >>> groups = dkt.DKT31_groups
    >>> colors = group_colors(colormap, adjacency_matrix, IDs, names, groups,
    ...     save_text_files, plot_colors, plot_graphs, out_dir, verbose)
    >>> colors[0]
    [0.7586206896551724, 0.20689655172413793, 0.0]
    >>> colors[1]
    [0.48275862068965514, 0.4482758620689655, 0.48275862068965514]
    >>> colors[2]
    [0.3448275862068966, 0.3103448275862069, 0.034482758620689655]
    >>> colors[-1]
    [0.7931034482758621, 0.9655172413793103, 0.7931034482758621]

    No groups / subgraphs:

    >>> groups = []
    >>> colors = group_colors(colormap, adjacency_matrix, IDs, names, groups,
    ...     save_text_files, plot_colors, plot_graphs, out_dir, verbose)
    >>> colors[0]
    [0.5172413793103449, 0.8275862068965517, 1.0]
    >>> colors[1]
    [0.13793103448275862, 0.0, 0.24137931034482757]
    >>> colors[2]
    [0.3793103448275862, 0.27586206896551724, 0.48275862068965514]
    >>> colors[-1]
    [0.6206896551724138, 0.48275862068965514, 0.3448275862068966]

    """
    import os
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import networkx as nx
    from colormath.color_diff import delta_e_cie2000
    from colormath.color_objects import LabColor, AdobeRGBColor
    from colormath.color_conversions import convert_color

    # ------------------------------------------------------------------------
    # Set parameters for graph layout and output files:
    # ------------------------------------------------------------------------
    if plot_graphs:
        graph_node_size = 1000
        graph_edge_width = 2
        graph_font_size = 10
        subgraph_node_size = 3000
        subgraph_edge_width = 5
        subgraph_font_size = 18
        axis_buffer = 10
        graph_image_file = os.path.join(out_dir, "label_graph.png")
        subgraph_image_file_pre = os.path.join(out_dir, "label_subgraph")
        subgraph_image_file_post = ".png"

    if plot_colors:
        colormap_image_file = os.path.join(out_dir, 'label_colormap.png')

    if save_text_files:
        colormap_csv_file = os.path.join(out_dir, 'label_colormap.csv')
        colormap_json_file = os.path.join(out_dir, 'label_colormap.json')
        colormap_xml_file = os.path.join(out_dir, 'label_colormap.xml')

    # ------------------------------------------------------------------------
    # Load colormap:
    # ------------------------------------------------------------------------
    if verbose:
        print("Load colormap and convert to CIELAB color space.")
    if isinstance(colormap, np.ndarray):
        colors = colormap
    elif isinstance(colormap, str):
        colors = pd.read_csv(colormap, sep=',', header=None)
        colors = colors.values
    else:
        raise IOError("Please use correct format for colormap.")
    nlabels = np.shape(colors)[0]
    new_colors = np.copy(colors)

    if not IDs:
        IDs = range(nlabels)
    if not names:
        names = [str(x) for x in range(nlabels)]
    if not groups:
        groups = [1 for x in range(nlabels)]

    # ------------------------------------------------------------------------
    # Convert to Lab color space which better represents human perception:
    # ------------------------------------------------------------------------
    # https://python-colormath.readthedocs.io/en/latest/illuminants.html
    lab_colors = []
    for rgb in colors:
        lab_colors.append(convert_color(AdobeRGBColor(rgb[0], rgb[1], rgb[2]),
                                        LabColor))

    # ------------------------------------------------------------------------
    # Load label adjacency matrix:
    # ------------------------------------------------------------------------
    if np.size(adjacency_matrix):
        if verbose:
            print("Load label adjacency matrix.")
        if isinstance(adjacency_matrix, np.ndarray):
            adjacency_values = adjacency_matrix
        # If a string (file) is provided instead of a numpy ndarray:
        #    column 0 = label "ID" number
        #    column 1 = label "name"
        #    column 2 = "group" number (each label is assigned to a group)
        #    columns 3... = label adjacency matrix
        elif isinstance(adjacency_matrix, str):
            matrix = pd.read_csv(adjacency_matrix, sep=',', header=None)
            matrix = matrix.values
            IDs = matrix.ID
            names = matrix.name
            groups = matrix.group
            adjacency_values = matrix[[str(x) for x in IDs]].values
        else:
            raise IOError("Please use correct format for adjacency matrix.")
        if np.shape(adjacency_values)[0] != nlabels:
            raise IOError("The colormap and label adjacency matrix don't "
                          "have the same number of labels.")

        # Normalize adjacency values:
        adjacency_values = adjacency_values / np.max(adjacency_values)
    else:
        plot_graphs = False

    # ------------------------------------------------------------------------
    # Sort labels by decreasing number of adjacent labels (adjacency sum):
    # ------------------------------------------------------------------------
    if np.size(adjacency_matrix):
        adjacency_sums = np.sum(adjacency_values, axis = 1)  # sum rows
        isort_labels = np.argsort(adjacency_sums)[::-1]
    else:
        isort_labels = range(nlabels)

    # ------------------------------------------------------------------------
    # Order label groups by decreasing maximum adjacency sum:
    # ------------------------------------------------------------------------
    label_groups = np.unique(groups)
    if np.size(adjacency_matrix):
        max_adjacency_sums = []
        for label_group in label_groups:
            igroup = [i for i,x in enumerate(groups) if x == label_group]
            max_adjacency_sums.append(max(adjacency_sums[igroup]))
        label_groups = label_groups[np.argsort(max_adjacency_sums)[::-1]]

    # ------------------------------------------------------------------------
    # Convert adjacency matrix to graph for plotting:
    # ------------------------------------------------------------------------
    if plot_graphs:
        adjacency_graph = nx.from_numpy_matrix(adjacency_values)
        for inode in range(nlabels):
            adjacency_graph.node[inode]['ID'] = IDs[inode]
            adjacency_graph.node[inode]['label'] = names[inode]
            adjacency_graph.node[inode]['group'] = groups[inode]

    # ------------------------------------------------------------------------
    # Create a similarity matrix for pairs of colors:
    # ------------------------------------------------------------------------
    if verbose:
        print("Create a similarity matrix for pairs of colors.")
    dx_matrix = np.zeros((nlabels, nlabels))
    for icolor1 in range(nlabels):
        for icolor2 in range(nlabels):
            dx_matrix[icolor1,icolor2] = delta_e_cie2000(lab_colors[icolor1],
                                                         lab_colors[icolor2])
    # ------------------------------------------------------------------------
    # Sort colors by decreasing perceptual difference from all other colors:
    # ------------------------------------------------------------------------
    icolors_to_pick = list(np.argsort(np.sum(dx_matrix, axis = 1))[::-1])

    # ------------------------------------------------------------------------
    # Loop through label groups:
    # ------------------------------------------------------------------------
    for label_group in label_groups:
        if verbose:
            print("Labels in group {0}...".format(label_group))
        igroup = [i for i,x in enumerate(groups) if x == label_group]
        N = len(igroup)

        # --------------------------------------------------------------------
        # Select unpicked colors for group that are similar to the first
        # unpicked color (unpicked colors were sorted above by decreasing
        # perceptual difference from all other colors):
        # --------------------------------------------------------------------
        isimilar = np.argsort(dx_matrix[icolors_to_pick[0],
                                        icolors_to_pick])[0:N]
        icolors_to_pick_copy = icolors_to_pick.copy()
        group_colors = [list(colors[icolors_to_pick[i]]) for i in isimilar]
        for iremove in isimilar:
            icolors_to_pick.remove(icolors_to_pick_copy[iremove])

        # --------------------------------------------------------------------
        # Reorder subgraph colors according to label adjacency sum
        # (decreasing number of adjacent labels):
        # --------------------------------------------------------------------
        isort_group_labels = np.argsort(isort_labels[igroup])
        group_colors = [group_colors[i] for i in isort_group_labels]

        # --------------------------------------------------------------------
        # Compute differences between every pair of colors within group:
        # --------------------------------------------------------------------
        run_permutations = False
        weights = False
        if run_permutations:
            permutation_max = np.zeros(N)
            NxN_matrix = np.zeros((N, N))
            # ----------------------------------------------------------------
            # Convert subgraph into an adjacency matrix:
            # ----------------------------------------------------------------
            neighbor_matrix = np.array(nx.to_numpy_matrix(subgraph,
                                            nodelist=igroup))
            if not weights:
                neighbor_matrix = (neighbor_matrix > 0).astype(np.uint8)
            # ----------------------------------------------------------------
            # Permute colors and color pair differences:
            # ----------------------------------------------------------------
            DEmax = 0
            permutations = [np.array(s) for s
                            in itertools.permutations(range(0, N), N)]
            if verbose:
                print(" ".join([str(N),'labels,',
                                str(len(permutations)),
                                'permutations:']))
            for permutation in permutations:
                delta_matrix = NxN_matrix.copy()
                for i1 in range(N):
                  for i2 in range(N):
                    if (i2 > i1) and (neighbor_matrix[i1, i2] > 0):
                      delta_matrix[i1,i2] = delta_e_cie2000(group_lab_colors[i1],
                                                            group_lab_colors[i2])
                if weights:
                    DE = np.sum((delta_matrix * neighbor_matrix))
                else:
                    DE = np.sum(delta_matrix)
                # ------------------------------------------------------------
                # Store color permutation with maximum adjacency cost:
                # ------------------------------------------------------------
                if DE > DEmax:
                    DEmax = DE
                    permutation_max = permutation
                # ------------------------------------------------------------
                # Reorder subgraph colors by the maximum adjacency cost:
                # ------------------------------------------------------------
                group_colors = [group_colors[x] for x in permutation_max]
                new_colors[isimilar] = group_colors

        # --------------------------------------------------------------------
        # Assign new colors:
        # --------------------------------------------------------------------
        else:
            new_colors[isimilar] = group_colors

        # --------------------------------------------------------------------
        # Draw a figure of the colored subgraph:
        # --------------------------------------------------------------------
        if plot_graphs:
            plt.figure(label_group)
            subgraph = adjacency_graph.subgraph(igroup)

            # Layout:
            pos = nx.nx_pydot.graphviz_layout(subgraph,
                                              prog="neato")
            nx.draw(subgraph, pos, node_size=subgraph_node_size,
                    width=subgraph_edge_width, alpha=0.5,
                    with_labels=False)

            # Labels:
            labels={}
            for iN in range(N):
                labels[subgraph.nodes()[iN]] = \
                    subgraph.node[subgraph.nodes()[iN]]['label']
            nx.draw_networkx_labels(subgraph, pos, labels,
                                    font_size=subgraph_font_size,
                                    font_color='black')
            # Nodes:
            nodelist = list(subgraph.node.keys())
            for iN in range(N):
                nx.draw_networkx_nodes(subgraph, pos,
                    node_size=subgraph_node_size,
                    nodelist=[nodelist[iN]],
                    node_color=group_colors[iN])

            # Figure:
            ax = plt.gca().axis()
            plt.gca().axis([ax[0]-axis_buffer, ax[1]+axis_buffer,
                            ax[2]-axis_buffer, ax[3]+axis_buffer])
            plt.savefig(subgraph_image_file_pre + str(int(label_group)) +
                        subgraph_image_file_post)
            #plt.show()

    # ------------------------------------------------------------------------
    # Plot the entire graph (without colors):
    # ------------------------------------------------------------------------
    if plot_graphs:
        plt.figure(nlabels)

        # Graph:
        pos = nx.nx_pydot.graphviz_layout(adjacency_graph, prog="neato")
        nx.draw(adjacency_graph, pos,
                node_color='yellow',
                node_size=graph_node_size,
                width=graph_edge_width,
                with_labels=False)

        # Labels:
        labels={}
        for ilabel in range(nlabels):
            labels[ilabel] = adjacency_graph.node[ilabel]['label']
        nx.draw_networkx_labels(adjacency_graph, pos, labels,
                                font_size=graph_font_size,
                                font_color='black')
        # # Nodes:
        # nodelist = list(adjacency_graph.node.keys())
        # for icolor, new_color in enumerate(new_colors):
        #     nx.draw_networkx_nodes(subgraph, pos,
        #                            node_size=graph_node_size,
        #                            nodelist=[nodelist[icolor]],
        #                            node_color=new_color)

        plt.savefig(graph_image_file)
        plt.show()

    # ------------------------------------------------------------------------
    # Plot the subgraphs (colors):
    # ------------------------------------------------------------------------
    if plot_graphs:
        for label_group in label_groups:
            plt.figure(label_group)
            plt.show()

    # ------------------------------------------------------------------------
    # Plot the colormap as a horizontal bar chart:
    # ------------------------------------------------------------------------
    if plot_colors:
        plt.figure(nlabels, figsize=(5, 10))
        for ilabel in range(nlabels):
            ax = plt.subplot(nlabels, 1, ilabel + 1)
            plt.axis("off")
            rgb = new_colors[ilabel]
            plt.barh(0, 50, 1, 0, color=rgb)
        plt.savefig(colormap_image_file)
        plt.show()

    # ------------------------------------------------------------------------
    # Save new colormap as text files:
    # ------------------------------------------------------------------------
    if save_text_files:

        # ------------------------------------------------------------------------
        # Save new colormap as a csv file:
        # ------------------------------------------------------------------------
        np.savetxt(colormap_csv_file, new_colors, fmt='%.18e', delimiter=',',
                   newline='\n', header='')

        # ------------------------------------------------------------------------
        # Save new colormap as a json file:
        # ------------------------------------------------------------------------
        f = open(colormap_json_file,'w')
        f.write("""
{
  "name": "DKT31colormap",
  "description": "Colormap for DKT31 human brain cortical labels”,
   “colormap": [
""")

        for icolor, color in enumerate(new_colors):
            if icolor == len(new_colors) - 1:
                end_comma = ''
            else:
                end_comma = ','
            f.write('''
            {0}“ID”: "{1}", 
            “name”: "{2}", 
            “red”: “{3}”, 
            “green”: “{4}”, 
            “blue”: “{5}"{6}{7}
            '''.format("{", IDs[icolor], names[icolor],
                       color[0], color[1], color[2], "}", end_comma))

        f.write("""
  ]
}
""")
        f.close()

        # ------------------------------------------------------------------------
        # Save new colormap as an xml file:
        # ------------------------------------------------------------------------
        f = open(colormap_xml_file,'w')
        f.write("""
<ColorMap name="DKT31colormap" space="RGB">
""")
        for icolor, color in enumerate(new_colors):
            f.write('''
<Point x="{0}" o="{0}" r="{1}" g="{2}" b="{3}"/>
            '''.format(IDs[icolor] / max(IDs), color[0], color[1], color[2]))
        f.write("""
</ColorMap>
""")
        f.close()

    # ------------------------------------------------------------------------
    # Return new colors:
    # ------------------------------------------------------------------------
    colors = new_colors.tolist()

    return colors
