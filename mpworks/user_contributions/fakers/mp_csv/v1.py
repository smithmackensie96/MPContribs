from StringIO import StringIO
from ...config import mp_categories, mp_level01_titles
from base import MPCsvFileBase

class MPCsvFile(MPCsvFileBase):
    """fake a input file for a user contribution"""
    def __init__(
        self, main_general=False, num_level0_sections=3, max_level=3,
        max_num_subsec=3, max_data_rows=3, mp_title_prob=50
    ):
        MPCsvFileBase.__init__(self)
        self.main_general = main_general
        self.num_level0_sections = num_level0_sections
        self.max_level = max_level
        self.max_num_subsec = max_num_subsec
        self.max_data_rows = max_data_rows
        self.mp_title_prob = mp_title_prob

    def _get_mp_cat_id(self):
        """get an arbitrary MP category id"""
        mp_category = self.fake.random_element(elements=mp_categories.keys())
        method_name, text = mp_categories[mp_category]
        method = getattr(self.fake, method_name)
        return method(text=text)

    def _get_level_n_section_line(self, sec, n):
        """get an arbitrary level-n section line

        - format: ">*n TITLE/title # comment"
        - use one of config.mp_level01_titles a few times
        - config.mp_level01_titles can only be level-0 or level-1 titles
        - n = 0: title = GENERAL if sec == 0 and main_general else MP_CAT_ID 
        - n = 1: title = mp_level01_titles if not in 'GENERAL' else random
        - n > 1: title = random
        - append comment using config.csv_comment_char now and then
        - make level-0 titles all-caps
        """
        indentor = self.get_indentor(n)
        if n == 0:
            title = mp_level01_titles[0].upper() \
                    if sec == 0 and self.main_general else \
                    self._get_mp_cat_id().upper()
        elif n == 1 and self.fake.boolean(
            chance_of_getting_true=self.mp_title_prob
        ) and self.section_titles[-1] != mp_level01_titles[0].upper():
            title = self.fake.random_element(elements=mp_level01_titles)
        else:
            title = self.fake.word()
        self.section_titles.append(title)
        return ' '.join([indentor, title, self.get_comment()])

    def _print_key_value(self):
        """print key-value pair
        
        - type(key) = str, type(value) = anything
        - append comment now and then
        """
        print >>self.section, self.get_key_value() + self.get_comment()

    def _make_level_n_section(self, sec, n):
        """recursively generate nested level-n section
        
        - level-1 mp_level01_titles allowed once per level-0 section
        - mp_level01_titles[0] can be arbitrarily deep nested ('general')
        - mp_level01_titles[1:] has no subsections ('data')
        - mp_level01_titles[2] only has level-2 subsections ('plots')
        - mp_level01_titles[1] has csv format, all others key:value
        - randomly throw in comment lines
        """
        comments = self.get_comments()
        if comments != '': print >>self.section, comments
        print >>self.section, self._get_level_n_section_line(sec, n)
        if self.main_general and sec == 0 and n == 0:
            self.get_player_general_section(n)
        comment = self.get_comment()
        if comment != '': print >>self.section, comment
        num_subsec = 0 if n == self.max_level or \
                self.section_titles[-1] == mp_level01_titles[1] or \
                ( n == 2 and self.section_titles[-2] == mp_level01_titles[2] ) \
                else self.fake.random_int(max=self.max_num_subsec)
        for i in range(num_subsec):
            self._make_level_n_section(sec, n+1)
            self.section_structure.append('.'.join(self.section_titles))
            self.section_titles.pop()
        # all subsections processed
        if num_subsec == 0:
            if self.section_titles[-1] == mp_level01_titles[1] or (
                n == 0 and \
                self.section_titles[-1] != mp_level01_titles[0].upper()
            ):
                print >>self.section, '  ==> insert csv'
            elif n == 2 and self.section_titles[-2] == mp_level01_titles[2]:
                print >>self.section, '  ==> special key-value pairs for plot'
            elif not self.main_general and \
                    self.section_titles[-1] == mp_level01_titles[0]:
                self.get_player_general_section(n)
            elif n != 0 or (
                n == 0 and \
                self.section_titles[-1] != mp_level01_titles[0].upper()
            ):
                for r in range(self.max_data_rows): self._print_key_value()

    def make_file(self):
        """produce a fake file structure"""
        for i in range(self.num_level0_sections):
            while 1:
                self.section = StringIO()
                self._make_level_n_section(i, 0)
                self.section_titles.pop()
                if self.level0_section_ok():
                    print >>self.outfile, self.section.getvalue()
                    self.section.close()
                    break
        print self.outfile.getvalue()
        self.outfile.close()