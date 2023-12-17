# p2p web scraper

## problem trust

the biggest problem is: i dont trust other people

other people can send malicious data, which would corrupt my database

possible solution: people send the raw HTTPS response from the server
which i can verify with the server's public key

https://crypto.stackexchange.com/questions/5455/does-a-trace-of-ssl-packets-provide-a-proof-of-data-authenticity

> The server doesn't sign the data itself. It only signs part of the handshake if you're using a signing based suite. That means you can prove to a third party that a handshake with a certain server happened, and what data was exchanged in that handshake.
>
> The actual connection is encrypted and authenticated using symmetric operations. Anybody who knows those symmetric keys can forge a ciphertext that decrypts and authenticates successfully with these keys. So you can't prove which data was exchanged.

https://security.stackexchange.com/questions/231014/is-it-possible-to-store-record-https-client-auth-traffic-as-a-signed-document

> TLS does not provide non-repudiation. The signature is proof that you communicated with the other party, but it is not proof of when the communication took place (because gmt_unix_time is deprecated) and it is not proof of what was communicated, only that the communication took place
>
> After the handshake, both sides have the same symmetric keys for both sides. Both sides can generate a transcript that shows the other side sent, encrypted and authenticated with the expected keys, any data. There is no way to know whether that is true or not.
>
> To achieve non-repudiation, you would need to add a digital signature at the end of the connection, signing a hash of the entire connection until the disconnect message was received. But there is no such feature in TLS.

> no site is signing the application traffic with their own private key but encryption and MAC are only based on a shared secret created during the key exchange.

https://security.stackexchange.com/questions/143375/how-to-prove-some-server-sent-some-file-over-https

> this would be required to implement a zero-trust peer-to-peer web scraping network, to scrape files which are only location-addressed (not content-addressed), to prevent untrusted peers to contribute malicious data. peer-to-peer web scraping would be useful to defeat rate-limiting services like cloudflare.

https://security.stackexchange.com/questions/261910/validate-https-traffic-at-later-time

> TLSv1.3 explicitly prevents this kind of traffic analysis "at later time", i.e. without having the internal state of both sides. This is called "perfect forward secrecy" (PFS).

https://github.com/tlsnotary/tlsn

https://tlsnotary.org/

With TLSNotary, you can create cryptographic proofs of authenticity for any data on the web,
Using our protocol you can securely prove:
You received a private message from someone.
A snapshot of a webpage.
What's the catch?
TLSNotary does require a trust assumption.
A Verifier of a proof must trust that the Notary did not collude with the Prover to forge it.
This trust can be minimized by requiring multiple proofs each signed by different Notaries.
In some applications the Verifier can act as the Notary themselves, which allows for fully trustless proofs!

https://github.com/tlsnotary/tlsn/issues/388
fully trustless proofs - when possible?

## p2p proxy network

this would be much simpler than trying to break the forward secrecy of TLS

multiple peers would run a proxy service on their computer

this can be a VPN server, or a HTTPS proxy, or a SOCKS5H proxy.

similar to a torproject.org exit node,
but we dont need onion routing,
and the public tor exit nodes are blocked by cloudflare
(getting private tor exit nodes is non-trivial).

this can be abused, so the proxy should only allow requests to whitelisted domains.
so a pure HTTPS proxy would not work,
because it sees only destination IP addresses, but no destination hostnames.

the proxy must be a "non-transparent proxy" aka "elite proxy",
so the destination host does not know that we are using a proxy.

https://forum.opnsense.org/index.php?topic=24671.0

> Squid http and https proxy ACL Whitelisting


<blockquote>

I'm trying to setup squid as a non-transparent proxy
for both HTTP and HTTPS trafic
in order to blacklist all web trafic
except for a handful of urls/domains.

While proxying itself is working fine
I'm having troubles configuring ACL Whiltelisting for HTTPS.
It seems to work fine for HTTP though.

Test Setup:
Opnsense 21.7.2_1 in a KVM virtual machine.
Client is a Rocky 8 VM behind the Opnsense.
Tests are done with curl (curl http://google.com -x 192.168.1.1:3128)

Squid configuration:

- General forward settings
  - Proxy interfaces: LAN
  - Transparent proxy disabled
  - SSL Inspection enabled.
  - CA to use: locally generated CA specifically for squid.
It is installed as a trusted certificate on the test client behind opnsense.
- Access Control List
  - Whitelist: this is the actual core of my issue. Some values do not seem to work as excpected. See below
  - Blacklist: ".[a-zA-Z]+" (basically block everything)

The rest of the config is untouched.

Basically if I set the whitelist to "google.com" or "google", I can curl to both http://google.com and https://google.com. This is an expected result
If I set the whitelist to "http://google.com" I can only query http://google.com. https://google.com gives me the "Access Denied" page. This is an expected result.

However when the whitelist is set to "https?://google.com", I can query http://google.com successfuly but querying https://google.com gives me the "Access Denied" page. The expected result would be to successfuly query https://google.com

Also when setting the whitelist to "https://google.com" I cannot query anything. The expected result would be to only be able to successfuly query https://google.com

It almost seems like when checking the ACL for HTTPS trafic, squid only matches the regex against the domain name of the website and not the full accessed URL.

Am I missing something there?

</blockquote>

<blockquote>

Apparently the issue was the blacklist.

By using "https?:\/\/" as the blacklist it works as intended:
all trafic is denied except for what is whitelisted.

I cannot really explain why this was not working though...
If someone has the correct explanation as to
why ".[a-zA-Z]+" was blocking trafic in https but not http
I'd be more than happy to hear it.

</blockquote>

TODO how does "SSL Inspection" work in squid?

probably:

- SSL Inspection enabled.
- CA to use: locally generated CA specifically for squid.
It is installed as a trusted certificate on the test client behind opnsense.

this sounds bad, because a malicous proxy server could poison the traffic.

## filtering socks5h proxy server

https://github.com/topics/socks5-proxy

https://github.com/topics/socks5-server

### goproxy

https://github.com/snail007/goproxy

### 3proxy

https://github.com/3proxy/3proxy

tiny free proxy server
socks5

https://github.com/pufferffish/wireproxy

### proxify

https://github.com/projectdiscovery/proxify

### microsocks

https://github.com/rofl0r/microsocks

### awslambdaproxy

https://github.com/dan-v/awslambdaproxy

An AWS Lambda powered HTTP/SOCKS web proxy

### spp

https://github.com/esrrhs/spp

A simple and powerful proxy



### merino

https://github.com/ajmwagar/merino

A SOCKS5 Proxy server written in Rust


## non-socks5h proxy servers

### tinyproxy

http://tinyproxy.github.io/

https://github.com/tinyproxy/tinyproxy

<blockquote>

**Filter**

Tinyproxy supports filtering of web sites based on URLs or domains.

</blockquote>

<blockquote>

**FilterURLs**

If this boolean option is set to `Yes` or `On`, filtering is performed for URLs rather than for domains. The default is to filter based on domains.

Note that filtering for URLs works only in plain HTTP scenarios.

</blockquote>

### Allow users to choose a SOCKS5 proxy instead of firewall rules.

https://github.com/QubesOS/qubes-issues/issues/5032

> **Describe the solution you'd like**
>
> One solution is to use a filtering SOCKS5 proxy instead. SOCKS5 has several advantages:

> A filtering SOCKS5 proxy written in Nim already exists. My understanding is that Nim is memory-safe when compiled correctly.

### nimSocks

https://github.com/enthus1ast/nimSocks

A filtering SOCKS proxy server and client library written in nim.

### wzshiming/socks5

https://github.com/wzshiming/socks5

Socks5/Socks5h server and client. Full TCP/Bind/UDP and IPv4/IPv6 support

### A way to whitelist (or blacklist) https connections

https://serverfault.com/questions/659169/a-way-to-whitelist-or-blacklist-https-connections

### How do proxy servers filter https websites?

https://serverfault.com/questions/276467/how-do-proxy-servers-filter-https-websites

### socks5h

https://github.com/topics/socks5h

h = hostname resolution (DNS queries) over the proxy server

required to prevent DNS leaks

### dante

socks5 proxy server, but has no filtering

https://www.inet.no/dante/

https://www.inet.no/dante/doc/1.4.x/index.html

https://github.com/notpeter/dante

### squid

squid is marked as "inscure" in nixpkgs because of
https://megamansec.github.io/Squid-Security-Audit/

> The Squid Team have been helpful and supportive during the process of reporting these issues.
> However, they are effectively understaffed, and simply do not have the resources to fix the discovered issues.
> Hammering them with demands to fix the issues won’t get far.

https://github.com/squid-cache/squid

https://serverfault.com/questions/820578/how-to-enable-socks5-for-squid-proxy

http://wiki.squid-cache.org/Features/Socks

Goal: To add SOCKS support to Squid.
Status: Testing. Code available.

The aim of this project will be
to make http_port accept SOCKS connections
and make outgoing connections to SOCKS cache_peers
so that Squid can send requests easily through to SOCKS gateways
or act as an HTTP SOCKS gateway itself.

https://alternativeto.net/software/squid/

> - Privoxy is the most popular Windows, Mac & Linux alternative to Squid.
> - Privoxy is the most popular Open Source & free alternative to Squid.

### privoxy

http://www.privoxy.org/

https://github.com/ssrlive/privoxy

https://github.com/ler762/privoxy

https://github.com/yak1ex/privoxy-enhanced

### tinyproxy

https://github.com/tinyproxy/tinyproxy

> --enable-filter: Allows Tinyproxy to filter out certain domains and URLs.

https://github.com/tinyproxy/tinyproxy/issues/166

How do I enable SOCKS5?

if you need a socks5 proxy, check out https://github.com/rofl0r/microsocks
