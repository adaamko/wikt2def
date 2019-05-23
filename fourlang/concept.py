import re


class Concept():
    def __init__(self, name):
        self.printname = name

    def dot_id(self):
        """node id for dot output"""
        return u"{0}_{1}".format(
            Concept.d_clean(self.dot_printname()), str(id(self))[-4:])

    def dot_printname(self):
        """printname for dot output"""
        return self.printname.split('/')[0].replace('-', '_')

    @staticmethod
    def d_clean(string):
        s = string
        for c in '\\=@-,\'".!:;':
            s = s.replace(c, '_')
        s = s.replace('$', '_dollars')
        s = s.replace('%', '_percent')
        if s == '#':
            s = '_number'
        keywords = ("graph", "node", "strict", "edge")
        if re.match('^[0-9]', s) or s in keywords:
            s = "X" + s
        return s

    def printname(self):
        if '/' in self.printname:
            return self.printname.split('/')[0]
        return self.printname

    def unique_name(self):
        return u"{0}_{1}".format(self.printname, id(self))


def main():
    pass


if __name__ == "__main__":
    main()