.. link:
.. description:
.. tags:
.. date: 2013-08-27 18:20:55 UTC-03:00
.. title: Charts
.. slug: charts

If you are using reStructuredText and install pygal, Nikola has support for rather nice charts
with little effort, and i's even semi-interactive (hover your pointer over the legend!):

.. code:: rest

    .. chart:: StackedLine
       :title: 'Browser usage evolution (in %)'
       :fill: True
       :x_labels: ['2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012']
       :width: 600
       :height: 400
       :explicit_size: True
       :style: BlueStyle

       ('Others',  [14.2, 15.4, 15.3,  8.9,    9, 10.4,  8.9,  5.8,  6.7,  6.8,  7.5])
       ('IE',      [85.8, 84.6, 84.7, 74.5,   66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1])
       ('Firefox', [None, None, None, 16.6,   25,   31, 36.4, 45.5, 46.3, 42.8, 37.1])
       ('Chrome',  [None, None, None, None, None, None,    0,  3.9, 10.8, 23.8, 35.3])

.. raw:: html

   <div style="text-align: center;">

.. chart:: StackedLine
    :title: 'Browser usage evolution (in %)'
    :fill: True
    :x_labels: ['2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012']
    :width: 600
    :height: 400
    :explicit_size: True
    :style: BlueStyle

    ('Others',  [14.2, 15.4, 15.3,  8.9,    9, 10.4,  8.9,  5.8,  6.7,  6.8,  7.5])
    ('IE',      [85.8, 84.6, 84.7, 74.5,   66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1])
    ('Firefox', [None, None, None, 16.6,   25,   31, 36.4, 45.5, 46.3, 42.8, 37.1])
    ('Chrome',  [None, None, None, None, None, None,    0,  3.9, 10.8, 23.8, 35.3])

.. raw:: html

   </div>


Here's how it works:

* Next to the directive, use the `chart type you want <http://pygal.org/chart_types/>`_
* Any option you can set in a chart? Use it like ``:title:`` in this example. Syntax on
  the value is just like in the pygal examples.
* For each data series do it like the line that says ``Firefox`` in this example. The first element
  is the label, then comes the data.

Easy, right? Please explore `the pygal site <http://pygal.org>`_ for more information, and just
take this example and tweak stuff.
