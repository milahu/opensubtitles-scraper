# headfull web scraper

opposite of: headless web scraper



## status

early draft is implemented in fetch-subs.py

```
./fetch-subs.py --proxy-provider chromium --num-downloads 2 --first-num 9756545 --debug
```



## todo

- parse positions of chromium icons on a desktop of unknown size.
currently, the positions are calibrated to my desktop (1920x1080 monitor, KDE plasma desktop, 150% scaling, ...).
see also [screen parsing](#screen-parsing)
- make this run in a headless environment like github CI.
start an xorg-server with some lightweight desktop manager (example: openbox),
and on that virtual desktop, create the chromium window



## screen parsing



https://medium.com/acm-uist/understanding-user-interfaces-with-screen-parsing-3a8bcdb94e86

<blockquote>

This blog post summarizes our paper Screen Parsing: Towards Reverse Engineering of UI Models from Screenshots, which was published in the proceedings of UIST 2021.

</blockquote>

https://dl.acm.org/doi/fullHtml/10.1145/3472749.3474763

<blockquote>

Screen Parsing: Towards Reverse Engineering of UI Models from Screenshots

Automated understanding of user interfaces (UIs) from their pixels can improve accessibility, enable task automation, and facilitate interface design without relying on developers to comprehensively provide metadata. A first step is to infer what UI elements exist on a screen, but current approaches are limited in how they infer how those elements are semantically grouped into structured interface definitions. In this paper, we motivate the problem of screen parsing, the task of predicting UI elements and their relationships from a screenshot. We describe our implementation of screen parsing and provide an effective training procedure that optimizes its performance. In an evaluation comparing the accuracy of the generated output, we find that our implementation significantly outperforms current systems (up to 23%). Finally, we show three example applications that are facilitated by screen parsing: (i) UI similarity search, (ii) accessibility enhancement, and (iii) code generation from UI screenshots.

Keywords: user interface modeling, ui semantics, hierarchy prediction

</blockquote>
