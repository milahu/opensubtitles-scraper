#! /usr/bin/env python3

# find identical strings (or similar strings = identical substrings)
# in subs for different movies
# at start and end of movie
# (but maybe also in the middle of the movie?)

# get subs from opensubs.db
# unpack and convert to utf8
# parse subs
# add every* textpart to opensubs-find-ads.db
#   with a full text search index (sqlite fts)
#   todo really? fts splits text by words
# * to make it simple, add only the first 20, and the last 5 textparts

# python -u remove-ads.py | tee -a remove-ads.py.log

import os
import sqlite3
import glob
import shutil

from opensubtitles_dump_client.repack import Repack

# https://github.com/tkarabela/pysubs2
# https://github.com/tkarabela/pysubs2/issues/43 # Add character encoding autodetection
#import pysubs2
import lib.thirdparty.pysubs2.pysubs2 as pysubs2

# TODO expand
import opensubtitles_ads



class FindAds(Repack):

    def __init__(self):

        super().__init__()

        self.find_ads_db_path = "opensubs-find-ads.db"

        self.debug_stop_after_n_subs = 1000

        self.debug_order_by_random = True

        self.use_first_n_subs = 30
        self.use_last_n_subs = 10

        self.find_ads_db_connection = None
        self.find_ads_db_cursor = None

        # when a sub has no fps value, use this pseudo fps
        # this will produce wrong timings, but here, we dont care
        self.fallback_pseudo_fps = 24

    def main(self):

        assert os.path.exists(self.opensubs_db_path), f"error: missing input file: {self.opensubs_db_path}"
        assert os.path.exists(self.metadata_db_path), f"error: missing input file: {self.metadata_db_path}"

        #os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.cached_zip_dir, exist_ok=True)

        #with open(self.index_file, "r") as f:
        #    self.index_data = json.load(f)

        self.metadata_db_connection = sqlite3.connect(self.metadata_db_path)
        # default: rows are tuples (faster)
        #self.metadata_db_connection.row_factory = sqlite3.Row # rows are dicts
        # metadata_data

        self.find_ads_db_connection = sqlite3.connect(self.find_ads_db_path)
        self.find_ads_db_cursor = self.find_ads_db_connection.cursor()

        # TODO index?
        # TODO fts? https://pypi.org/project/sqlitefts/
        self.find_ads_db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS subs_textparts (\n"
            "  idx INTEGER PRIMARY KEY,\n"
            "  sub INTEGER,\n"
            "  pos INTEGER,\n" # 0 = first, -1 = last
            "  len INTEGER,\n" # textpart duration in milliseconds
            "  txt TEXT\n"
            ")\n"
        )

        self.metadata_db_cursor = self.metadata_db_connection.cursor()
        #self.metadata_db_connection.row_factory = sqlite3.Row # rows are dicts
        self.metadata_db_cursor.row_factory = sqlite3.Row # rows are dicts

        print(f"loading cached zip files from {self.cached_zip_dir}")
        self.cached_zip_files = glob.glob(f"{self.cached_zip_dir}/*.zip")
        self.cached_zip_files_by_num = dict()
        for zip_file in self.cached_zip_files:
            num = int(os.path.basename(zip_file).split(".", 2)[0])
            self.cached_zip_files_by_num[num] = zip_file
        self.cached_zip_files = self.cached_zip_files_by_num
        print("cached zip files:", len(self.cached_zip_files))

        done_subs = 0

        sql_query = "SELECT IDSubtitle FROM subz_metadata WHERE ISO639 = ? AND IDSubtitle BETWEEN ? AND ?"

        # TODO more efficient
        # choose a random sub_number and read the next 10...100 subs sequentially
        if self.debug_order_by_random:
            sql_query += " ORDER BY random()"

        if self.debug_stop_after_n_subs:
            sql_query += f" LIMIT {self.debug_stop_after_n_subs}"

        sql_args = (self.lang_code_short, self.opensubs_db_first_sub_number, self.opensubs_db_last_sub_number)

        sql_cursor = self.metadata_db_connection.cursor()

        try:
            for (sub_number,) in sql_cursor.execute(sql_query, sql_args):
                print("sub_number", sub_number)
                #if len(sub_numbers) >= 10: raise NotImplementedError
                self.parse_textparts(sub_number)
                done_subs += 1
                #if done_subs > self.debug_stop_after_n_subs:
                #    break
        except BaseException as e:
            # write data before abort
            try:
                print(f"writing {self.find_ads_db_path}")
            except BrokenPipeError:
                # this happens with
                # python -u find_ads.py | tee -a find_ads.py.log
                pass
            self.find_ads_db_connection.commit()
            self.find_ads_db_connection.close()
            raise e

        # write data before exit
        print(f"writing {self.find_ads_db_path}")
        self.find_ads_db_connection.commit()
        self.find_ads_db_connection.close()

    def parse_textparts(self, sub_number):

        sub_tempdir = f"{self.main_tempdir}/sub-{sub_number}"
        keep_sub_tempdir = False
        os.makedirs(sub_tempdir) # exist_ok=True
        #print(f"extracting {sub_tempdir}")
        self.extract_movie_sub(sub_number, sub_tempdir)

        for subfile_name in os.listdir(sub_tempdir):

            subfile_path = sub_tempdir + "/" + subfile_name
            # no need to guess encoding. all files are utf8 from extract_movie_sub

            try:
                parsed_subs = pysubs2.load(subfile_path)
            except pysubs2.exceptions.UnknownFPSError:
                # example: 3614024: fps = 0
                parsed_subs = pysubs2.load(subfile_path, fps=self.fallback_pseudo_fps)
            except pysubs2.exceptions.FormatAutodetectionError:
                print(f"FIXME pysubs2.exceptions.FormatAutodetectionError: subfile_path = {subfile_path}")
                keep_sub_tempdir = True
                continue

            def get_all_indices_positive_negative(lst):
                # [0, 1, 2, 3] -> [0, 1, -2, -1]
                full_len = len(lst)
                half_len = round(full_len / 2 + 0.25)
                return list(range(0, half_len)) + list(range((half_len - full_len), 0))

            if len(parsed_subs) < (self.use_first_n_subs + self.use_last_n_subs):
                #raise NotImplementedError(f"sub has only {len(parsed_subs)} textparts. sub_tempdir: {sub_tempdir}")
                # add all textparts
                #parsed_subs_subset = parsed_subs
                parsed_subs_index_list = get_all_indices_positive_negative(parsed_subs)
            else:
                # add first and last textparts
                #parsed_subs_subset = parsed_subs[:self.use_first_n_subs] + parsed_subs[(-1 * self.use_last_n_subs):]
                parsed_subs_index_list = list(range(0, self.use_first_n_subs)) + list(range((-1 * self.use_last_n_subs), 0))

            # no, use index positions, positive and negative
            """
            last_textpart_start = parsed_subs[-1].start
            if last_textpart_start == 0:
                # avoid ZeroDivisionError: division by zero
                last_textpart_start = 999999
            """

            #for textpart in parsed_subs_subset:
            for textpart_idx in parsed_subs_index_list:

                textpart = parsed_subs[textpart_idx]

                sql_query = "INSERT INTO subs_textparts (sub, pos, len, txt) VALUES (?, ?, ?, ?)"
                sql_args = (
                    sub_number,
                    #(textpart.start / last_textpart_start),
                    textpart_idx,
                    (textpart.end - textpart.start), # milliseconds
                    textpart.text
                )
                self.find_ads_db_cursor.execute(sql_query, sql_args)

        if keep_sub_tempdir == False:
            shutil.rmtree(sub_tempdir)



if __name__ == "__main__":
    FindAds().main()
