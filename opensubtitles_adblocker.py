#!/usr/bin/env python3



class OpensubtitlesAdblocker:

    regex = None

    def __init__(self):

        self.init_regex()

    def filter_subtitle_bytes(self, subtitle_bytes):

        """
        filter raw bytes of subtitles file

        processing the raw bytes is required to make this more robust

        one subtitle file can contain multiple text encodings
        where "read as text file" would fail

        the downside of this is that
        we have to store bytestrings in regex_lines_list
        to handle non-utf8 special characters
        """

        # average size: 20KB in zip = about 50KB unpacked

        # no. too risky
        # grep -b saveanilluminati.com "Utopia UK S02E06 720p BluRay H264 BONE.en.06251501.srt"
        # 10309:Find out @ saveanilluminati.com
        """
        # perf: filter only first and last N bytes
        # ads are only on start and end of subtitle
        cut_start = 10_000
        cut_end = 5_000

        if len(subtitle_bytes) > (cut_start + cut_end):
            return (
                self.regex.sub(b"", subtitle_bytes[:cut_start]) +
                subtitle_bytes[cut_start:(-1*cut_end)] + # dont filter
                self.regex.sub(b"", subtitle_bytes[(-1*cut_end):])
            )
        """

        return self.regex.sub(b"", subtitle_bytes)

        #return pat.sub(self.replace_match, subtitle_bytes)

    def filter_subtitle_files(self, files, backup=False, stdout=False):

        import os
        import sys

        for subtitle_path in files:

            try:
                with open(subtitle_path, "rb") as f:
                    subtitle_bytes = f.read()
            except FileNotFoundError:
                sys.stderr.write(f"error: no such file: {repr(subtitle_path)}\n")
                continue

            subtitle_bytes = self.filter_subtitle_bytes(subtitle_bytes)

            if stdout:
                sys.stdout.buffer.write(subtitle_bytes)
                sys.stdout.buffer.flush()
                continue

            if backup:
                subtitle_path_bak = subtitle_path + ".bak"
                if os.path.exists(subtitle_path_bak):
                    sys.stderr.write(f"error: backup exists: {repr(subtitle_path_bak)}\n")
                else:
                    os.rename(subtitle_path, subtitle_path_bak)

            with open(subtitle_path, "wb") as f:
                f.write(subtitle_bytes)

    #@staticmethod
    #def replace_match(match):
    #    # todo: preserve strings between matches
    #    return ""

    def init_regex(self):

        import re

        def regex_of_lines(regex_lines):
            # srt: "\n" or "\r\n" or "\r"
            # ssa: "\\N"
            # sub: "|"
            # TODO more?
            line_sep = b"(?:\\n|\\r\\n|\\r|\\\\N|\\|)"
            # require match of line end to avoid replacing substrings first
            line_end = b"(?:\\n|\\r\\n|\\r|\\\\N|\\||$)" # $ = end of string
            def to_bytes(str_or_bytes):
                if type(str_or_bytes) == bytes:
                    return str_or_bytes
                return str_or_bytes.encode("utf8")
            return b"(?:" + line_sep.join(map(to_bytes, regex_lines)) + line_end + b")"

        regex_bytes = b"|".join(map(regex_of_lines, self.regex_lines_list))

        self.regex = re.compile(regex_bytes)

        #self.regex = re.compile(regex_bytes, re.IGNORECASE) # no. 10x slower

    #def get_regex_strings():
    regex_lines_list = (

        # opensubtitles.org
        ('Support us and become VIP member ?', 'to remove all ads from www\\.OpenSubtitles\\.org'),
        ('Support us and become VIP member ?', 'to remove all ads from OpenSubtitles\\.org'),
        ('Advertise your product or brand here', 'contact www\\.OpenSubtitles\\.org today'),
        ('Please rate this subtitle at www\\.osdb\\.link/[0-9a-zA-Z]{1,6}', 'Help other users to choose the best subtitles'),
        ('-== \\[ www\\.OpenSubtitles\\.com \\] ==-',),
        ('-== \\[ www\\.OpenSubtitles\\.org \\] ==-',),
        ('-= www\\.OpenSubtitles\\.org =-',),
        ('想在此处添加您的广告信息？立即联系 www\\.OpenSubtitles\\.org',),
        ('api\\.OpenSubtitles\\.org is deprecated, please', 'implement REST API from OpenSubtitles\\.com'),

        # addic7ed.com
        # TODO refactor
        ('Sync and corrections by masaca', '- addic7ed\\.com -'),
        ('Sync by YYeTs', 'Corrected by MystEre', 'www\\.addic7ed\\.com'),
        ('== sync, corrected by elderman ==', '@elder_man'),
        ('==sync, correction by dcdah==', 'for www\\.addic7ed\\.com'),
        ('Sync & corrections by Elderfel', 'www\\.addic7ed\\.com'),
        ('Sync & corrections by honeybunny', 'www\\.addic7ed\\.com'),
        ('- synced and corrected by chamallow -', '- www\\.addic7ed\\.com -'),
        ('- Synced and corrected by VitoSilans -', '-- www\\.Addic7ed\\.com --'),
        ('Done by mosito1001', 'www\\.addic7ed\\.com'),
        ('- sync and corrections by Caio -', '- www.addic7ed.com -'),
        ('Sync and corrections by explosiveskull', 'www\\.addic7ed\\.com'),

        ('Who are the real-world Illuminati \\?', 'Find out @ saveanilluminati\\.com'),
        ('2万円賭けて、5千円分の無料チップをゲット。', ' 賭けのルールはありません-世界の bitcasino\\.io/ja'),
        ('5 days of Hacking / Camping / Lectures', 'Join May Contain Hackers: MCH2022\\.org'),
        ('Closed-Captioned By', 'Captions, Inc\\., Los Angeles'),
        ('CLOSED CAPTIONED BY', 'CAPTIONS, INC\\., LOS ANGELES'),
        ('COPYRIGHTED BY ALIEN', 'PRODUCTIONS ALL RIGHTS RESERVED\\.'),
        ('\\[ENGLISH\\]',),
        ('\\[ENGLISH SDH\\]',),
        ('\\[English - US - SDH\\]',),
        ('English -SDH',),
        ('qatinefilms',),
        ('qatinefilms4k@gmail\\.com',),
        ('Special thanks to all the people oi the School oi Traditional Arts, PARK Song-hee, a human', 'cultural asset and the members and teachers oi Duresori\\. English subtitled by LEE Jee-heng\\.'),
        ('♪Subs: Aorion, corrected by♪ AsifAkheir ☻♥',),
        ('Subtitles: A\\.Whitelaw',),
        ('Subtitles arranged by Aziz Kezer',),
        ('Subtitles by', 'SDI Media Group'),
        ('Subtitles by YayPonies', 'http://yayponies\\.eu', 'HoH version'),
        ('Subtitles downloaded from Podnapisi\\.NET',),
        ('Subtitle translation by Ja-won Lee',),
        ('Subtitling: Eclair Group',),
        ('Translated by Inglourious @KG',),
        ('www\\.tvsubtitles\\.net',),
        ('Want more movies in English\\?', 'www\\.EngFilms\\.ru'),
        ('Download Movie Subtitles Searcher from www\\.podnapisi\\.net',),
        ('Transcript : http://www\\.twiztv\\.com',),
        ('Synchro : Skool237 \\(JE HAIS CA !!!\\)',),
        ('www\\.forom\\.com',),
        ('<i><b><u>Subtitles', '~Adoni@~</u></b></i>'),
        ('Visiontext subtitles: Julie Clayton',),
        ('Subtitles by Tzar',),
        (b'Subtitles \xdfy M\xfch\xe0mm\xe1\xd0 \xdc\xa7m\xe2\xf1',),
        ('<font color="#3399CC">Subtitles by </font><font color="ffffff">MemoryOnSmells</font>', '<font color="#3399CC">http://UKsubtitles\\.ru\\.</font>'),
        ('Uploaded By <font color="#00E68A">Abdullah Al Amin</font>', '<font color="#FF3399">http://bollyhdtv\\.blogspot\\.com/</font>'),
        ('www\\.NapiProjekt\\.pl - nowa jakość napisów\\.', 'Napisy zostały specjalnie dopasowane do Twojej wersji filmu\\.'),
        ('Subtitle by silentFØX',),
        (b'Subtitle by silentF\xd8X',),
        ('Subtitles: Arigon',),
        (b'Odwied\x9f www\\.NAPiSY\\.info',),
        ('Legendado por: lilicca,', 'Virtualnet and Bozano\\.'),
        ('Ressinc R5: Rafael UPD', 'Group GetSeries'),
        ('www\\.cpturbo\\.org', 'www\\.cpturbo2\\.org'),
        ('<font color="#ffff00">Provided by explosiveskull</font>', 'https://twitter\\.com/kaboomskull'),
        ('Subtitles by', 'SDI Media Group',),
        # TODO allow more complex line separator for ass format
        # quickfix for ass format
        # The Day After Tomorrow (2004).thdyatrtmrwm.br.en.09394982.ass
        # Dialogue: 1,2:03:34.45,2:03:36.45,D_2,,0,0,0,,Subtitles by
        # Dialogue: 0,2:03:34.45,2:03:36.45,D_1,,0,0,0,,SDI Media Group
        ('Subtitles by',),
        ('SDI Media Group',),
        ('- Subtitle Created By: islanq',),
        ('Repair and Synchronization by', 'Easy Subtitles Synchronizer 1\\.0\\.0\\.0'),
        ('Subtitle improved and resynced', '==Ding Tonsing=='),
        ('Encoded by Hunter', 'Crazy4TV\\.com'),
        ('<font color="#3399FF">Sync and correction by Mlmlte</font>', '<font color="#3399FF">www\\.addic7ed\\.com</font>'),
        ('<font color="#ffff00">>>>>oakislandtk<<<<<</font>', '<font color="#ffff00">www\\.opensubtitles\\.org</font>',),
        ('Visiontext Subtitles: Neil Blackmore',),
        ('ENHOH',),
        ('Corrected & Arranged by BANQUO', '\\(alacayel@gmail\\.com\\)'),
        ('-: Edited & Corrected by :-', '-: MeadeIndeed @ Subscene :-'),
        ('Subtitles:', 'Barabas'),

        # Irreversible.2002.720p.BluRay.x264-[YTS.AM].en.00072011.srt
        (b'Subtitles ripped and corrected ', b'by Max \\(c\\) 2004\\.'),

        # Irreversible.2002.720p.BluRay.x264-[YTS.AM].en.00114767.sub
        (b'Subtitles checked and adjusted', b'to the movie by adamnoga@poczta\\.onet\\.pl'),

        # The.People.vs.Larry.Flynt.1996.720p.BRRip.x264.AAC-ETRG.en.03529991.srt
        (b'Downloaded From www\\.AllSubs\\.org',),

        # The.People.vs.Larry.Flynt.1996.720p.BRRip.x264.AAC-ETRG.en.00078935.sub
        (b'Corrected by BFUB',),
        (b'a member of -=TFUFH=-',),
        (b'www\\.faghoes\\.tk',),

        # Detachment.2011.720p.BluRay.X264.YIFY.en.04557421.srt
        (b'Thank you for using those subtitles\\.', b'- Sekhmet'),
        (b"I'm not a native-English speaker so you'll find some", b'remaining gaps \\(and probably mistakes\\)\\.', b"If you want to write them down and send them to me, I'll be happy to correct them: sekhmetouserapis_at_gmail\\.com"),
        (b'Subtitles by Sekhmet', b'For any comment: sekhmetouserapis_at_gmail\\.com'),
        (b'Subtitles by Sekhmet\\. For any comment:', b'sekhmetouserapis_at_gmail\\.com'),

        # Detachment.2011.720p.BluRay.X264.YIFY.en.05050795.srt
        (b'Translation by mattrew', b'mod_forumcity@hotmail\\.com'),
        (b'Resync by rupala @ portugal',),

        # Detachment.2011.720p.BluRay.X264.YIFY.en.08503899.srt
        (b'<font color="#0080ff">Corrected Text and Reading Expansion', b'By Chuck</font>'),
        (b'"Detachment"', b'<font color="#ff0000">Corrected Text and Reading Expansion', b'By Chuck</font>'),

        # World.War.Z.2013.720p.BluRay.x264.YIFY.en.05162196.srt
        (b'www\\.phreex\\.net',),
        (b'Downloaded from www\\.phreex\\.net', b'Uploaded by nLiVE'),

        # World.War.Z.2013.720p.BluRay.x264.YIFY.en.05163544.srt
        (b'Subtitles corrected & re-synced', b'by AsifAkheir\xe2\x99\xaa\xe2\x99\xaa '),
        (b'Subtitles corrected & re-synced', b'by AsifAkheir'),

        # World.War.Z.2013.720p.BluRay.x264.YIFY.en.05180161.srt
        (b'Synced By : meisam_t72',),

        # World.War.Z.2013.720p.BluRay.x264.YIFY.en.06655926.srt
        (b'www\\.titlovi\\.com',),
        (b'Preuzeto sa www\\.titlovi\\.com',),

        # World.War.Z.2013.720p.BluRay.x264.YIFY.en.05163660.srt
        # what an attention-seeking piece of shit...
        # colors:
        # 12345
        # green
        # orange
        # "#8000ff"
        # "#ffff80"
        # "#00ff80"
        # "#ff2492"
        # "#00ff40"
        # "#8d1cff"
        # 123456789
        (b'<font color=[^>]{5,9}>\xc2?\xa9',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 ',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@r',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!N',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nd',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nde',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR ',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@n',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 ',),

        # note: with multiple lines, longer strings must come first to avoid replacing substrings first
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2', b'<font color=white>Mobile - \\+919815899536', b'<font color=[^>]{5,9}>EMail - parminder222536@hotmail\\.com'),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2', b'<font color=white>Mobile - \\+919815899536'),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),

        (b'<font color=[^>]{5,9}>\xc2?\xa9</font> P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 </font>P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P</font>@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@</font>rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@r</font>M!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM</font>!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!</font>NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!N</font>deR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nd</font>eR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nde</font>R M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR</font> M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR </font>M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M</font>@nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@</font>nk\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@n</font>k\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk</font>\xc3\x96\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96</font>\xc3\x96 \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96</font> \xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 </font>\xe2\x84\xa2',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xc3\x96\xc3\x96 \xe2\x84\xa2</font>',),

        # The Day After Tomorrow (2004).thdyatrtmrwm.br.en.05727781.srt
        (b'<font color=[^>]{5,9}>\xc2?\xa9',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 ',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@r',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!N',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nd',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nde',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR ',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@n',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 ',),

        # note: with multiple lines, longer strings must come first to avoid replacing substrings first
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 \x99', b'<font color=white>Mobile - \\+919815899536', b'<font color=[^>]{5,9}>EMail - parminder222536@hotmail\\.com'),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 \x99', b'<font color=white>Mobile - \\+919815899536'),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 \x99',),

        (b'<font color=[^>]{5,9}>\xc2?\xa9</font> P@rM!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 </font>P@rM!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P</font>@rM!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@</font>rM!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@r</font>M!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM</font>!NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!</font>NdeR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!N</font>deR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nd</font>eR M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!Nde</font>R M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR</font> M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR </font>M@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M</font>@nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@</font>nk\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@n</font>k\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk</font>\xd6\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6</font>\xd6 \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6</font> \x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 </font>\x99',),
        (b'<font color=[^>]{5,9}>\xc2?\xa9 P@rM!NdeR M@nk\xd6\xd6 \x99</font>',),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.00060483.srt
        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.00060546.srt
        (b'English Subtitle by Do My Best', b'For The\\.Last\\.Samurai\\.SCREENER-OBUS fixed by KoXo'),
        (b'English Subtitle by Do My Best',),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.00200296.srt
        (b'Subtitles by Raiden',),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.00226821.srt
        (b'English Subtitle by Azmodan',),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.04653590.srt
        (b'Created and Encoded by --  Bokutox -- of  www\\.YIFY-TORRENTS\\.com\\. The Best 720p/1080p/3d movies with the lowest file size on the internet\\.',),
        (b'Created and Encoded by --  Bokutox -- of  www\\.YIFY-TORRENTS\\.com\\. The Best 720p/1080p/3d movies with the lowest file size on the internet\\. World of Warcraft - Outland PVP \\(EU\\) - Torporr \\(name\\)',),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.06218558.srt
        # typo: wwwwww
        (b'Support us and become VIP member ', b'to remove all ads from wwwwww\\.OpenSubtitles\\.org'),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.06569701.srt
        (b'This was a roNy re-encode for', b'300MBUNiTED\\.com'),

        # The.Last.Samurai.2003.720p.BrRip.x264.YIFY.en.07235867.srt
        (b'ENGLISH',),
        # bug: %url%
        (b'Please rate this subtitle at %url%', b'Help other users to choose the best subtitles'),

        # The.Girl.With.The.Dragon.Tattoo.2011.720p.BluRay.x264.YIFY.en.04456246.srt
        (b'<font color="#3399FF">Subtitle by d3xt3r</font>', b'<font color="#3399FF">www\\.addic7ed\\.com</font>'),
        (b'<font color="#3399FF">Subtitle by d3xt3r</font>',),

        # The.Girl.With.The.Dragon.Tattoo.2011.720p.BluRay.x264.YIFY.en.04482747.srt
        (b'warwerwor', b'fb:ozmonkingkong@yahoo\\.co\\.id', b'suster_myud', b'burnyozmon\\.blogspot\\.com'),

        # The.Girl.With.The.Dragon.Tattoo.2011.720p.BluRay.x264.YIFY.en.09422142.srt
        (b'Watch any video online with Open-SUBTITLES', b'Free Browser extension: osdb\\.link/ext'),

        # Undergods.2020.720p.BluRay.800MB.x264-GalaxyRG.en.08764986.srt
        (b'Subtitles:', b'Babel Subtitling - babelSUB\\.'),

        # Undergods.2020.720p.BluRay.800MB.x264-GalaxyRG.en.08779441.srt
        (b'Provided by explosiveskull', b'https://twitter\\.com/kaboomskull'),

        # V.For.Vendetta.2005.720p.BrRip.x264.YIFY.en.05626626.srt
        (b'Subt\xedtulos: walterar', b'en www\\.SubDivX\\.com', b'v\\. 060506'),

        # V.For.Vendetta.2005.720p.BrRip.x264.YIFY.en.06534338.srt
        (b'<font color="#490BD">Translated by NM007', b"Don't Forget To Visit http://numetalizer\\.blogspot\\.com</font>"),

        # V.For.Vendetta.2005.720p.BrRip.x264.YIFY.en.05644615.srt
        (b'<font face="Monotype Corsiva" color=#808080"> \xc2\xa9 anoXmous </ font>', b'<font face="Monotype Corsiva" color=#D900D9"> @ https://thepiratebay\\.se/user/anoXmous </font>'),

        # Mr.Robot.S01E01.720p.BluRay.x264.ShAaNiG.en.1954766725.srt
        (b'Synced and corrected by', b'<b>Dr\\. Dunnestein</b>'),

        # Mr.Robot.S01E01.720p.BluRay.x264.ShAaNiG.en.1954873317.srt
        (b'- Synced and corrected by skoad -', b'www\\.addic7ed\\.com'),

        # Mr.Robot.S01E01.720p.BluRay.x264.ShAaNiG.en.1955152292.srt
        (b'<font color="#8e35ef">Club Protocol Uploads - CPUL</font>', b'https://thepiratebay\\.se/user/CPUL'),

        # Mr.Robot.S01E02.720p.BluRay.x264.ShAaNiG.en.1954801892.srt
        (b'Use the free code JOINNOW at ', b'\xe2\x80\xa8www\\.playships\\.eu'),

        # Mr.Robot.S01E02.720p.BluRay.x264.ShAaNiG.en.1954809951.srt
        (b'- Synced and corrected by sk\xf8ad -', b'www\\.addic7ed\\.com'),

        # Mr.Robot.S01E02.720p.BluRay.x264.ShAaNiG.en.1954809953.srt
        (b'- Synced and corrected by sk\xc3\xb8ad -', b'www\\.addic7ed\\.com'),

        # Mr.Robot.S01E05.720p.BluRay.x264.ShAaNiG.en.1954869789.srt
        (b'Advertise your product or brand here', b'contact www\xe2\x80\x8e\\.OpenSubtitles\xe2\x80\x8e\\.org today'),
        (b'Support us and become VIP member ', b'to remove all ads from OpenSubtitles\xe2\x80\x8e\\.org'),

        # Mr.Robot.S01E05.720p.BluRay.x264.ShAaNiG.en.1955035356.srt
        (b'<font color="#8D38C9\\fnArial"><i><b>Fixed & Synced By MoUsTaFa ZaKi </b></i></font>',),

        # Mr.Robot.S01E09.720p.BluRay.x264.ShAaNiG.en.1954858448.srt
        (b'- Synced and corrected by martythecrazy -', b'- www\\.addic7ed\\.com -'),

        # Mr.Robot.S01E09.720p.BluRay.x264.ShAaNiG.en.1954858493.srt
        (b'- Synced and corrected by martythecrazy -', b'- Resync by <font color="#80ffff">GoldenBeard</font> -', b'- www\\.addic7ed\\.com -'),

        # kkbb.eng.03178097.srt
        (b'Subtitles By Rajanee',),

        # kkbb.eng.04622272.srt
        (b'\\[Ripped by AGiX\\]',),

        # kkbb.eng.00237777.sub
        (b'new subtitle',),
        (b'New subtitle',),
        (b'FPS 23\\.94',),
        (b'timing and correction by deric 2006',),

        # kkbb.eng.00237603.srt
        (b'Adapted by:',),

        # kkbb.eng.08609747.srt
        (b'Encoded by Ashish Thakur',),

    )



if __name__ == "__main__":

    import sys
    import os
    import argparse

    parser = argparse.ArgumentParser(
        prog='opensubtitles_adblocker',
    )
    parser.add_argument('--backup', action='store_true')
    parser.add_argument('--stdout', action='store_true')
    parser.add_argument('files', metavar='file', nargs='+')

    args = parser.parse_args()

    adblocker = OpensubtitlesAdblocker()

    adblocker.filter_subtitle_files(
        args.files,
        backup=args.backup,
        stdout=args.stdout,
    )
