 # bpi2017

## Description

Datasets used for the Business Process Intelligence (BPI) Challenge in 2017. This event log pertains to a loan application process of a Dutch financial institute. The data contains all applications filed trough an online system in 2016 and their subsequent events until February 1st 2017, 15:11.

The company providing the data and the process under consideration is the same as for the BPI Challenge 2012. However, the system supporting the process has changed in the meantime. In particular, the system now allows for multiple offers per application. These offers can be tracked through their IDs in the log. A detailed description is given below for each dataset.

## Availability and License

Original files are available at [4TU.ResearchData](https://data.4tu.nl/articles/dataset/BPI_Challenge_2017/12696884/1) under the CC0 license. This means one can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission. Cite as follows: 

```
@article{vanDongen2017,
	author = "Boudewijn van Dongen",
	title = "{BPI Challenge 2017}",
	year = "2017",
	month = "2",
	url = "https://data.4tu.nl/articles/dataset/BPI_Challenge_2017/12696884",
	doi = "10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b"
} 
```

## Datasets

### full-log.xml (558.9MB)
This dataset contains full set of event logs. In the following, there are five methods to take subsets of this dataset in order to produce a proxy behavior.

### simulated-log.xml (57.1MB)
The proxy behavior is derived by simulating the process model.

### clustered-log.xml (343.9MB)
Using a K-medoid method, the traces are partitioned into K different clusters using control-flow information. Then, from each cluster, a single trace is chosen as a cluster representative. The value of K is dynamic, calculated as 1/10 of the unique number of variants in the event log.

### random-log.xml (343.7MB)
Traces are randomly selected for the proxy behavior.

### frequency-log.xml (78.9MB)
The traces are selected based on their frequency in the log.

### reduced-log.xml (373.2MB)
First, a subset of activities is chosen (activity selection). Then, the proxy behavior is generated from traces that contain these activities. We used the implementation of Sani et al. ("Conformance checking approximation using subset selection and edit distance") to generate the proxy behavior.

### sample-log.xml (78.7MB)
Under all configurations, we employed the same sample of 100 traces from the input log. All these traces represent different trace variants.

#### Statistics
```
 ======================== STATISTICS ======================== 
  DATASET NAME: raw-data/bpi2017/full-log.xml
  #EVENT NAMES: 26
       #TRACES: 31509
       #EVENTS: 1202267
 MIN TRACESIZE: 10
 AVG TRACESIZE: 38.15630454790695
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/simulated-log.xml
  #EVENT NAMES: 64
       #TRACES: 10000
       #EVENTS: 261953
 MIN TRACESIZE: 6
 AVG TRACESIZE: 26.1953
 MAX TRACESIZE: 41
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/clustered-log.xml
  #EVENT NAMES: 26
       #TRACES: 14338
       #EVENTS: 699751
 MIN TRACESIZE: 10
 AVG TRACESIZE: 48.80394755195983
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/random-log.xml
  #EVENT NAMES: 26
       #TRACES: 14422
       #EVENTS: 698997
 MIN TRACESIZE: 10
 AVG TRACESIZE: 48.46741090001387
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/frequency-log.xml
  #EVENT NAMES: 24
       #TRACES: 1593
       #EVENTS: 71818
 MIN TRACESIZE: 12
 AVG TRACESIZE: 45.08349026993095
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/reduced-log.xml
  #EVENT NAMES: 23
       #TRACES: 15930
       #EVENTS: 768942
 MIN TRACESIZE: 10
 AVG TRACESIZE: 48.27005649717514
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
  DATASET NAME: raw-data/bpi2017/sampled-log.xml
  #EVENT NAMES: 24
       #TRACES: 1592
       #EVENTS: 71397
 MIN TRACESIZE: 10
 AVG TRACESIZE: 44.847361809045225
 MAX TRACESIZE: 180
 ------------------------------------------------------------ 
       OVERALL: 
  #EVENT NAMES: 90
 ============================================================ 
```