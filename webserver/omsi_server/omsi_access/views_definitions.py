"""Collection of definitions for the omsi_access views, e.g., format specification, query parameters etc."""

available_formats = {'JSON': 'JSON',
                     'PNG': 'PNG',
                     'HDF5': 'HDF5'}
"""Dictionary defining the different data formats available.

   * JSON : Regular JSON
   * JSOND3 : This is also just a regular JSON but the formatting is (naming of keys etc.) is optimized for D3.
   * PNG: Return PNG image
   * HDF5: Return HDF5 file

"""

available_mtypes = {'filelistView': 'filelistView',
                    'filelistEdit': 'filelistEdit',
                    'filelistManage': 'filelistManage',
                    'filelistRawData': 'filelistRawData',
                    'file': 'file',
                    'provenance': 'provenance'}
"""Dictionary defining the available metadata types.

   * `filelistView` : Dict of dicts of all files the current user can view \
                      The keys are the file paths. For each file a dict is given \
                      that specifies the permissions the user has and the status \
                      of the file (e.g, managed, unmanaged).
   * `filelistEdit` : Dict of dicts of all files the current user can edit \
                      The keys are the file paths. For each file a dict is given \
                      that specifies the permissions the user has and the status \
                      of the file (e.g, managed, unmanaged)
   * `filelistManage` : Dict of dicts of all files the current user can manage. \
                      The keys are the file paths. For each file a dict is given \
                      that specifies the permissions the user has and the status \
                      of the file (e.g, managed, unmanaged)
   * `filelistRawData` : Dict of dicts of all raw data files the user has uploaded. \
                         The keys are the file paths. For each file a dict is given \
                         that specifies the permissions the user has and the status \
                         of the file (e.g, managed, unmanaged)
   * `file` : Basic file metadata
   * `provenance` : Get the provenance information for the specified object.
"""


available_layouts = {'default': 'default',
                     'hilbert': 'hilbert'}
"""Dictionary defining the available data layout options. Available options are:

   * `default` : Let the server function decide on the default data layout.
   * `hilbert` : Use a 2D hilbert data layout. Currently only supported by qspectrum and qmz.
"""

query_parameters = {'file': 'file',
                   'format': 'format',
                   'expIndex': 'expIndex',
                   'anaIndex': 'anaIndex',
                   'anaIdentifier': 'anaIdentifier',
                   'anaDataName': 'anaDataName',
                   'dataIndex': 'dataIndex',
                   'row': 'row',
                   'col': 'col',
                   'mz': 'mz',
                   'row2': 'row2',
                   'col2': 'col2',
                   'precision': 'precision',
                   'findPeaks': 'findPeaks',
                   'mtype': 'mtype',
                   'qslice_viewerOption': 'qslice_viewerOption',
                   'viewerOption': 'viewerOption',
                   'qspectrum_viewerOption': 'qspectrum_viewerOption',
                   'nameKey': 'nameKey',
                   'childKey': 'childKey',
                   'depth': 'depth',
                   'layout': 'layout',
                   'operations': 'operations',
                   'operations1': 'operations1',
                   'operations2': 'operations2',
                   'operationsMerge': 'operationsMerge'}
"""Dictionary defining the names of all available query string parameters. Available parmeters are:

    * `file` : Name of the file to be retrieved
    * `format` : The format in which the data sould be returned
    * `expIndex` : The index of the experiment to be retrieved
    * `anaIndex`: The index of the analysis dataset to be used (default None). Note, anaIndex or
                  anaIdentifier are redundant and only one should be sepcified.
    * `anaIdentifier`: Identifier string of the analysis dataset (default None).
                  Note, andIndex or anaIdentifier are redundant and only one should be sepcified.
    * `anaDataName`: Name of the analysis dataset that should be retrieved. (default None).
                  If not provided then the function will try and figure out which dataset to be
                  used based on what the analysis specifies as data to be used.
    * `dataIndex` : The index of the raw MSI dataset to be retrieved
    * `viewerOption` : Integer indicating which default behavior should be used for the given
                analysis (if multiple options are available). (Default=0) Alternatively also
                'qspectrum_viewerOption' may be used instead.
    * `qspectrum_viewerOption` : Same as viewerOption but specifically refering to the qslice data pattern.
    * `qspectrum_viewerOption` : Same as viewerOption but specifically refering to the qspectrum data pattern.
    * `precision` : Floating point precision of the output data.
    * `findPeaks` : Execute peak finding or not.
    * `mtype` : Type of metadata requested, one of: file, experiment, analysis, instrument,
                method, filelist, dataset, experimentFull
    * `row` : Selection string for the row in the image. [row,:,:] in array notation.
    * `col` : Selection string for the column in the image. [:,col,:] in array notation.
    * `mz` : Selection string for the data axis dimensions of the image. [:,:,mz] in array notation.
    * `row2` : Secondary selection string for the row in the image.
    * `col2` : Secondary selection string for the column in the image.
    * `nameKey` : Used by qmetadata to indicate which key name should be used to store object names
    * `childKey` : Used by qmetadata to indcate which key name should be used to store lists of children
    * `depth` : Used by qmetadata mtype==file to indicate until which path depth the childKey s
                hould be used. For path deeper then depth an '_' is prepanded to childKey.
                This is used to indcate for D3 which children should be displayed and which one
                should be expanded by default.
    * `layout` : Parameter used to specify the requested data layout
    * `operations` : Data operations to be applied to the final data.
                     JSON string with list of dictionaries or a python list of dictionaries.
                     Each dict specifies a single data transformation or data reduction that
                     are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                     for details.
    * `operations1` : Data operations to be applied to primary selection (x,y).
                     JSON string with list of dictionaries or a python list of dictionaries.
                     Each dict specifies a single data transformation or data reduction that
                     are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                     for details.
    * `operations2` : Data operations to be applied to secondary selection (x2,y2).
                      JSON string with list of dictionaries or a python list of dictionaries.
                      Each dict specifies a single data transformation or data reduction that
                      are applied in order. See omsi.shared.omsi_data_selection.transform_and_reduce_data(...)
                      for details.

"""
