from __future__ import unicode_literals, print_function
import os, json, six, codecs, locale
from abc import ABCMeta
from utils import make_pair, get_indentor, RecursiveDict, nest_dict, pandas_to_dict
from ..config import mp_level01_titles
from recparse import RecursiveParser
from pandas import DataFrame
from six import string_types
from collections import OrderedDict

class MPFile(six.with_metaclass(ABCMeta)):
    """Object for representing a MP Contribution File.

    Args:
        parser (RecursiveParser): recursive parser object, init empty RecursiveDict() if None
    """
    def __init__(self, parser=None, comments=None):
        self.comments = OrderedDict() if comments is None else comments
        self.document = RecursiveDict() if parser is None else parser.document

    @staticmethod
    def from_file(filename_or_file):
        """Reads a MPFile from a file.

        Args:
            filename_or_file (str or file): name of file or file containing contribution data.

        Returns:
            MPFile object.
        """
        if isinstance(filename_or_file, string_types):
            lang, encoding = locale.getdefaultlocale()
            file_string = codecs.open(filename_or_file, encoding=encoding).read()
        elif not isinstance(filename_or_file, file):
            file_string = filename_or_file.read().decode('utf-8')
        else:
            file_string = filename_or_file.read()
        return MPFile.from_string(file_string)

    @staticmethod
    def from_string(data):
        """Reads a MPFile from a string.

        Args:
            data (str): String containing contribution data.

        Returns:
            MPFile object.
        """
        # strip comments from data string
        lines, comments = [], OrderedDict()
        for idx,line in enumerate(data.splitlines()):
            idx_str, line = str(idx), line
            line_split = line.lstrip().split('#', 1)
            lines.append(line_split[0])
            if len(line_split) > 1:
                if not line_split[0]: idx_str += '*'
                comments[idx_str] = line_split[1]
        data = '\n'.join(lines)
        # parse remaining data string
        parser = RecursiveParser()
        parser.parse(data)
        # init MPFile
        mpfile = MPFile(parser=parser, comments=comments)
        return mpfile

    def add_comment(self, linenumber, comment):
        """add comment to line <linenumber>. An asterisk appended to
        <linenumber> denotes a comment on its own line"""
        self.comments[linenumber] = comment

    def shift_comment(self, idx_str, shift):
        comment = self.comments.pop(idx_str)
        idx_str_shift = self.get_shifted_comment_index(idx_str, shift)
        self.comments[idx_str_shift] = comment

    def shift_comments(self, shift):
        linenumbers = self.comments.keys()
        if shift > 0: linenumbers.reverse()
        for idx_str in linenumbers:
            self.shift_comment(idx_str, shift)

    def get_comment_index(self, idx_str):
        try:
            idx, ast = int(idx_str), False
        except:
            idx, ast = int(idx_str[:-1]), True
        return idx, ast

    def get_shifted_comment_index(self, idx_str, shift):
        idx, ast = self.get_comment_index(idx_str)
        idx += shift
        return str(idx) + ('*' if ast else '')

    def get_number_of_lines(self, **kwargs):
        return len(self.get_string(**kwargs).split('\n'))

    def split(self):
        general_mpfile = self.pop_first_section() \
                if mp_level01_titles[0] in self.document.keys() else None
        while True:
            try:
                mpfile_single = self.pop_first_section()
                if general_mpfile is not None:
                    mpfile_single.insert_general_section(general_mpfile)
                yield mpfile_single
            except KeyError:
                break

    def pop_first_section(self, n=0):
        """remove first root-level section and return as MPFile"""
        title, data = self.document.popitem(last=False)
        mpfile = MPFile()
        mpfile.document.rec_update(nest_dict(data, [title]))
        nlines = mpfile.get_number_of_lines(with_comments=True)
        for idx_str in self.comments.keys():
            idx = self.get_comment_index(idx_str)[0]
            if idx < nlines:
                comment = self.comments.pop(idx_str)
                mpfile.add_comment(idx_str, comment)
            else:
                self.shift_comment(idx_str, -nlines)
        return mpfile

    def insert_general_section(self, general_mpfile):
        """insert general section into MPFile with single section"""
        if general_mpfile is None: return
        general_title = mp_level01_titles[0]
        general_data = general_mpfile.document[general_title]
        general_nlines = general_mpfile.get_number_of_lines(with_comments=True)
        root_key = self.document.keys()[0]
        nlines_top = 1
        for key, value in self.document[root_key].iteritems():
            if isinstance(value, dict):
                first_sub_key = key
                break
            else:
                nlines_top += 1
        if general_title in self.document[root_key]:
            # FIXME rec_update will probably not play nice with comments
            self.document.rec_update(nest_dict(
                general_data, [root_key, general_title]))
        else:
            self.document[root_key].insert_before(
                first_sub_key, (general_title, general_data))
        for idx_str in reversed(self.comments.keys()):
            idx = self.get_comment_index(idx_str)[0]
            if idx < 1: continue
            self.shift_comment(idx_str, general_nlines-1)
        for idx_str in reversed(general_mpfile.comments.keys()):
            idx_str_shift = self.get_shifted_comment_index(idx_str, nlines_top)
            self.add_comment(idx_str_shift, general_mpfile.comments[idx_str])

    def set_test_mode(self, mp_cat_id, idx=0):
        """insert a key-value entry indicating test submission"""
        if len(self.document) > 1:
            raise ValueError('can set test mode only on single section files')
        first_sub_key = self.document[mp_cat_id].keys()[0]
        self.document[mp_cat_id].insert_before(
            first_sub_key, ('test_index', idx+733773))

    def concat(self, mpfile):
        if not isinstance(mpfile, MPFile):
            raise ValueError('Provide a MPFile to concatenate')
        if len(mpfile.document) > 1:
            raise ValueError('concatenation only possible with single section files')
        mp_cat_id = mpfile.document.keys()[0]
        general_title = mp_level01_titles[0]
        if general_title in mpfile.document[mp_cat_id]:
            general_data = mpfile.document[mp_cat_id].pop(general_title)
            if general_title not in self.document:
                self.document.rec_update(nest_dict(general_data, [general_title]))
        mp_cat_id_idx, mp_cat_id_uniq = 0, mp_cat_id
        while mp_cat_id_uniq in self.document.keys():
            mp_cat_id_uniq = mp_cat_id + '--{}'.format(mp_cat_id_idx)
            mp_cat_id_idx += 1
        self.document.rec_update(nest_dict(
            mpfile.document.pop(mp_cat_id), [mp_cat_id_uniq]
        ))
        # TODO: account for comments
        if mpfile.comments:
            raise NotImplementedError('TODO')
        #shift = mpfile.get_number_of_lines(with_comments=True)
        #for idx_str in mpfile.comments.keys():
        #    idx_str_shift = mpfile.get_shifted_comment_index(idx_str, shift)
        #    self.add_comment(idx_str_shift, mpfile.comments[idx_str])

    def insert_id(self, mp_cat_id, cid):
        """insert entry containing contribution ID for `mp_cat_id`"""
        if len(self.document) > 1:
            raise ValueError('ID insertion only possible for single section files')
        first_sub_key = self.document[mp_cat_id].keys()[0]
        self.document[mp_cat_id].insert_before(first_sub_key, ('cid', str(cid)))
        self.shift_comments(1)

    def get_string(self, with_comments=False):
        """Returns a string to be written as a file"""
        lines = []
        min_indentor = get_indentor()
        table_start = mp_level01_titles[1]+' '
        for key,value in self.document.iterate():
            if key is None and isinstance(value, DataFrame):
                csv_string = value.to_csv(index=False, float_format='%g')[:-1]
                lines += csv_string.split('\n')
            else:
                sep = '' if min_indentor in key else ':'
                if lines and key == min_indentor:
                    lines.append('')
                if isinstance(value, string_types):
                    if value.startswith(table_start):
                        value = value[len(table_start):]
                    if ':' in value: # quote to ignore delimiter
                        value = '"{}"'.format(value)
                lines.append(make_pair(key, value, sep=sep))
        if with_comments:
            for idx_str, comment in self.comments.iteritems():
                idx, ast = self.get_comment_index(idx_str)
                if ast: lines.insert(idx, '#'+comment)
                else: lines[idx] = ' #'.join([lines[idx], comment])
        return '\n'.join(lines) + '\n'

    def __repr__(self):
        return self.get_string()

    def __str__(self):
        """String representation of MPFile file."""
        return self.get_string()

    def write_file(self, filename, **kwargs):
        """Writes MPFile to a file. The supported kwargs are the same as those
        for the MPFile.get_string method and are passed through directly."""
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            file_str = self.get_string(**kwargs) + '\n'
            f.write(file_str)

    def add_data_table(self, identifier, dataframe, name):
        """add a data table/frame to the root-level section for identifier"""
        # TODO: optional table name, required if multiple tables per root-level section
        self.document.rec_update(nest_dict(
            pandas_to_dict(dataframe), [identifier, name]
        ))

    def get_identifiers(self):
        """list of identifiers (i.e. all root-level headers excl. GENERAL"""
        return [ k for k in self.document if k.lower() != mp_level01_titles[0] ]
