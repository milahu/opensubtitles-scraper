# torrent archive updates

concept for a growing dataset, distributed over bittorrent

useful for

- opensubtitles dataset
- IMDB dataset

the IMDB dataset is hosted on
https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset
which requires login

we think its better/easier/faster/cheaper
to distribute large data over bittorrent

## challenges

### cheap updates

the datasets are growing every day,
so we want weekly or monthly releases

old files are immutable,
so new release and last release are 99% identical

to update, download only new and changed files

## see also

- https://blog.libtorrent.org/2020/09/bittorrent-v2/ - bittorrent v2
  - share identical files between multiple torrents
- https://github.com/cjb/GitTorrent - git over bittorrent
  - https://blog.printf.net/articles/2015/05/29/announcing-gittorrent-a-decentralized-github/
- https://www.ctrl.blog/entry/git-p2p-compared.html - BitTorrent, Dat, IPFS
- https://stackoverflow.com/questions/6268628/git-a-large-data-set
- https://datascience.stackexchange.com/questions/5178/how-to-deal-with-version-control-of-large-amounts-of-binary-data
  - https://bup.github.io/ - backup system based on the git packfile format, providing fast incremental saves and global deduplication
- https://stackoverflow.com/questions/17888604/git-with-large-files
  - GVFS - git virtual filesystem for partial clones
- https://opendata.stackexchange.com/questions/4080/what-are-some-opendata-torrents-to-seed

## keywords

- growing dataset
- live dataset
- append-only
