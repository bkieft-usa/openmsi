omsi_client Package
===================

The `omsi_client` implements the omsi webpage, web frontent, and web-based viewer and data access applications.
The `omsi_server` application is used to retrieve data from the server, while the `omsi_client` defines
the web interface for interacting and viewing the data. 

'templates`
-----------

This folder contains the DJANGO template html files for rendering the OpenMSI webpage, including the online
data MSI data viewer. Here a list of available template pages:

   * ``base.html``: The basic page layout. Many of the other templates inherit from this template.
   * ``algorithms.html`` :  Descriptions of various algorithms used and/or developed by OpenMSI.
   * ``benchmarks.html`` : Information about benchmarks for OpenMSI.
   * ``contact.html`` : Contact the OpenMSI team.
   * ``docs.html`` : Developer and user documentation.
   * ``downloads.html`` : Webpage providing access to various downloads provided by OpenMSI.
   * ``examples.html`` : Webpage with a series of examples illustrating the use of OpenMSI.
   * ``index.html`` : The main OpenMSI webpage.
   * ``viewer.html`` : The OpenMSI web viewer application.


:mod:`urls` Module
------------------

This module defines the omsi_client specific URL patterns.

.. automodule:: omsi_client.urls
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`views` Module
-------------------

This module defines the DJANGO views for accessing the pages for the OMSI web application.

.. automodule:: omsi_client.views
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`models` Module
--------------------

.. automodule:: omsi_client.models
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`tests` Module
-------------------

.. automodule:: omsi_client.tests
    :members:
    :undoc-members:
    :show-inheritance:
