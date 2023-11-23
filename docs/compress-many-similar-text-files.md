# compress many similar text files

## sources

### Very different compression rate with two similar files

https://superuser.com/questions/1554371/very-different-compression-rate-with-two-similar-files

> Compression works by detecting repeating patterns in the data

> usually better compression requires more CPU


### Is compression more efficient if we're compressing multiple files, and many of the files are similar to each other?

https://www.quora.com/Is-compression-more-efficient-if-were-compressing-multiple-files-and-many-of-the-files-are-similar-to-each-other

An example of inter-file compression is described in

http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.66.819&rep=rep1&type=pdf

"Simple experiment to show the effects of interfile dependencies:
•9.8 GB of data from several websites, The Internet Archive
•Compressed using chunking to 1.83 GB. (5.62 GB using gzip)
•Chunks were mirrored and distributed evenly onto 179 devices, 20 MB each."

<blockquote>

Providing High Reliability in a Minimum Redundancy Archival Storage System

Abstract

Inter-file compression techniques store files as sets of
references to data objects or chunks that can be shared among
many files. While these techniques can achieve much better
compression ratios than conventional intra-file compression
methods such as Lempel-Ziv compression, they also reduce
the reliability of the storage system because the loss of a few
critical chunks can lead to the loss of many files. We show
how to eliminate this problem by choosing for each chunk a
replication level that is a function of the amount of data that
would be lost if that chunk were lost. Experiments using
actual archival data show that our technique can achieve
significantly higher robustness than a conventional approach
combining data mirroring and intra-file compression while
requiring about half the storage space.

</blockquote>

<blockquote>

3. Effect of Compression on Reliability

Chunk-based interfile compression can be quite effective
for certain types of data. You, et al. [33] have characterized
this data as files that evolve slowly mainly through small
changes, additions, and deletions. One of the data sets for
our experiments consists of 9.8 GB of several web sites:
those of the University of California at Santa Cruz, Santa
Clara University, Stanford University, University of
California at Berkeley, BBC, NASDAQ, CERT, CNN, SANS,
SUN, CISCO, and IBM as they developed over time. We
obtained them from the Internet Archive’s Wayback machine [29].
This data is a representative sample of archival
data, and will greatly profit from chunk-based compression
due to the incremental nature of the changes that
it has gone through. Chunk-based inter-file compression
stores this data using a storage space of 1.74 GB for chunks
and 280 MB for metadata. On the other hand, when each
file was compressed using LZ-compression, the total storage space
required was 5.6 GB. Clearly, chunk-based compression can
use significantly less storage space than LZcompression.

To study the effect of chunk-based compression on
reliability we conducted a pilot experiment using this data. We
compressed the files using chunk-based compression, and
then mirrored the chunks and stored them evenly across a
set of 179 devices. The devices were then randomly selected
to fail independently, resulting in the loss of up to
7% of the total devices. 

</blockquote>

<blockquote>

7. Related Work

Several systems that exploit data redundancy at different levels of granularity have been developed in order to
improve storage space efficiency. One class of systems detects redundant chunks of data at granularities that range
from entire file, as in EMC’s Centera [11], down to individual fixed-size disk blocks, as in Venti [23] and variable-size
data chunks as in LBFS [17].

RAID [6] is a device driven method for introducing redundancy and thus ensuring the reliability for storage systems. OceanStore [14] aims to provide continuous access to
persistent data on a global scale and uses automatic replication strategies to boost reliability of the system in the face
of disasters. FARSITE [1] is a distributed file system that
achieves reliability through replication of file system metadata, such as directories, and file data. FARSITE chooses
replication instead of erasure coding schemes to avoid the
additional overhead of latter when reconstructing a piece
of information. Other file systems such as PASIS [12]
and Glacier [13] also make use of aggressive replication to
guard against data loss. The LOCKSS project [15] uses a
peer-to-peer audit and repair protocol to preserve the integrity and long-term access to collections of documents.
Baker et al. [5] suggest that long term reliability additionally requires auditing the integrity of data above the level of
the storage devices. The surplus storage space we save by
using interfile compression can be used to implement proactive policies for ensuring reliability [31], verifying the data
integrity [27], and developing recovery strategies [32] for
large scale storage systems.

8. Future Work

In addition to chunk-based compression, Deep Store also
uses delta compression to archive data. We will study the
characteristics of delta compression and develop heuristics
for reliability as we have done here for chunk-based compression.

In this work, we have used only one method of introducing redundancies; replication. We will experiment with
other mechanisms such as RAID-5 parity, erasure correcting codes, and Reed-Solomon block codes [3, 22, 26].

</blockquote>

### Compressing a folder with many duplicated files

https://stackoverflow.com/questions/27457326/compressing-a-folder-with-many-duplicated-files


### Storing many text files with large similarities

https://stackoverflow.com/questions/48289006/storing-many-text-files-with-large-similarities

> You would want to concatenate your groups of a thousand files into a single file for gzipping, which should take advantage of the common blocks, if they are within 32K bytes distance from each other in the concatenation. You could also try zstd which has much larger dictionary sizes, and would surely be able to take advantage of the common blocks.

### Which compression utility should I use for an extremely large plain text file

https://softwarerecs.stackexchange.com/questions/49019/which-compression-utility-should-i-use-for-an-extremely-large-plain-text-file

> My data file is a little under 2TB (terabytes) of line-separated plain text records, each about 4 or 5 KB (totaling to a few hundred million records).

> I compressed a 219 GB subset of my data with several different programs to see which one got the best results.

> in other words: benchmark! the [turbobench](https://github.com/powturbo/TurboBench) tool might help. interesting results: compressed size, cpu time for compression and decompression, memory usage for compression and decompression, speed of random file access in a multi-file archive

## keywords

- compress many similar files
- compress many similar subtitles files
- structural compression algorithms
- inter-file compression algorithms
- chunk-based compression algorithms
- chunk-based inter-file compression algorithms
- chunkbased interfile compression algorithms
- chunkbased inter-file compression algorithms
