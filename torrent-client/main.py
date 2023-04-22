# http://libtorrent.org/python_binding.html

# https://superuser.com/questions/884642/is-there-a-way-to-download-only-specified-chunk-range-in-bittorrent-clients#_=_
# https://github.com/nicklan/Deluge-Pieces-Plugin/tree/master/pieces

# todo? use a "pure python bittorrent client" to download each piece to a separate file
# https://stackoverflow.com/questions/4418157/python-bittorrent-library
# https://github.com/gallexis/pytorrent
# https://github.com/borzunov/bit-torrent
# https://github.com/kishanpatel22/bittorrent

# https://stackoverflow.com/questions/13953086/download-specific-piece-using-libtorrent

# https://www.libtorrent.org/reference-Storage.html#map-file
# returns a peer_request representing the piece index, byte offset and size the specified file range overlaps. This is the inverse mapping over map_block(). Note that the peer_request return type is meant to hold bittorrent block requests, which may not be larger than 16 kiB. Mapping a range larger than that may return an overflown integer.

# https://gist.github.com/johncf/f1606e33562b51f67aa53ffdddf2183c
# Torrent: download specific pieces with libtorrent

import libtorrent
import time
import sys

session = libtorrent.session({'listen_interfaces': '0.0.0.0:6881'})

info = libtorrent.torrent_info(sys.argv[1])
handle = session.add_torrent({'ti': info, 'save_path': '.'})
status = handle.status()
print('starting', status.name)

class DownloadPriority:
    """
        libtorrent/download_priority.hpp
    """
    dont_download = 0
    default_priority = 4
    low_priority = 1
    top_priority = 7
libtorrent.download_priority = DownloadPriority()

print("disabling all pieces")
for piece_id in range(len(status.pieces)):
    priority = libtorrent.download_priority.dont_download
    handle.piece_priority(piece_id, priority)

while (not status.is_seeding):
    status = handle.status()

    #if (status.num_pieces > 0):
    #    handle.piece_priority(piece_id, priority)

    print('\r%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d pieces: %d/%d) %s' % (
        status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000,
        status.num_peers, status.num_pieces, len(status.pieces), status.state), end=' ')

    alerts = session.pop_alerts()
    for alert in alerts:
        if alert.category() & libtorrent.alert.category_t.error_notification:
            print(alert)

    #sys.stdout.flush()

    time.sleep(1)

print(handle.status().name, 'complete')
