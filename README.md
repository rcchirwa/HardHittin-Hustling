#Data Hustling

####*Mashed Up in Python, MongoDB and Spark*

This is a project the involves data exploration of various feeds from a local hip artist

Data has been gathered from a Twitter ETL process that gathered data about users and stored it to a local MongoDB database. 
The information was then exported to json file that could be ingested by a stand alone instance of Spark.

Data was also gathered from Server log files and ingested into Spark to analyze.

The .json and .txt files used above have been provided so that if you have an instance of Spark running and IPython Noteebook available you can examine various ways of interacting with Spark

Ipyton notebook and Spark can be started as follows:

`IPYTHON_OPTS="notebook --pylab inline" ./bin/pyspark`

This will launch and instance of ipython notebook with the Spark Context available to you in the notebook


The files ETL script as well as the assciated modules files have been included :-)