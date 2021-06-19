import os
import sys
import re

sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.realpath(__file__)))
)

import randregex.randregex as randregex

class TestsBasic:
    def basic_test(self, pattern, nb=1, testpattern=None):
        if testpattern is None:
            testpattern = pattern
        mytree = randregex.parse_rand_regex(pattern)
        for i in range(nb):
            res = randregex.produce_randregex_from_tree(mytree)
            assert re.fullmatch(testpattern, res) is not None    

    def test_pipe(self):
        self.basic_test("foo|bar")
        self.basic_test("foo|bar|toto")

    def test_parenthesis(self):
        self.basic_test("My teacher (rocks|sucks)")
        self.basic_test("toto|(tata|titi)")

    def test_sbrackets(self):
        self.basic_test("[aeiouy]")
        self.basic_test("[a-dW-Z0-2_]", 50)

    def test_cbrackets(self):
        self.basic_test("ahah{1,4}", 10)
        self.basic_test("(a|e|i){1,4}", 10)
        self.basic_test("[0-9]{3,5}{10,12}{50}", 10, 
                        "[0-9]{3,5}|[0-9]{10,12}|[0-9]{50}")

    def test_int(self):
        self.basic_test("%d{-99,99}", 20, "-?[1-9]?[0-9]")
        self.basic_test("(%d{1,6} ){3}", 10, "([1-6] ){3}")

    def test_float(self):
        mytree = randregex.parse_rand_regex("%f{-1,1}")
        for i in range(20):
            res = randregex.produce_randregex_from_tree(mytree)
            assert -1 <= float(res) and float(res) <= 1
            
    def test_group(self):
        self.basic_test("(?var=titi|tata|toto) is equal to ($var)", 5, 
                        "(titi|tata|toto) is equal to \\1")
        self.basic_test("(?blah=[a-z]{5}) is repeated twice in ($blah){2}", 5,
                        "([a-z]{5}) is repeated twice in \\1\\1")
            
    def test_escapecar(self):
        self.basic_test("[ \t\n]", 5)
        self.basic_test("\\(titi\\)", 5, "\\(titi\\)")
        self.basic_test("\\[titi\\]", 5, "\\[titi\\]")
        self.basic_test("ceci\\|cela|dessus\\|dessous", 5, 
                        "ceci\\|cela|dessus\\|dessous")
        self.basic_test("ahah\\{5\\}", 1, "ahah\\{5\\}")
        self.basic_test("ahah\\{5\\}", 1, "ahah\\{5\\}")
        self.basic_test("10\\%", 1, "10%")
        self.basic_test("ceci\\<30\\>|cela\\<70\\>", 1, "ceci<30>|cela<70>")
        self.basic_test("This is a \\c", 1, "This is a \\\\c")
        self.basic_test("\\\\(titi\\\\|tata\\\\)\\\\{2}", 5, 
                        "\\\\(titi\\\\|tata\\\\)\\\\{2}")

        self.basic_test("[a\\]\\[z\\<\\>]", 10, "[a\\][z<>]")
        self.basic_test("[a-d\\\\]", 10, "[a-d\\\\]")

    def test_weirdcases(self):
        self.basic_test("30>")
        self.basic_test("toto{3,3}")
        self.basic_test("toto{0,1}", 5)
        self.basic_test("((waza))")
        self.basic_test("(?var=[a-z]{5}){2} is ($var) repeated twice", 1, 
                        "([a-z]{5}){2} is [a-z]{5} repeated twice")

class TestsProba:
    def basic_test(self, pattern, nb, tab, err = 0.07):
        mytree = randregex.parse_rand_regex(pattern)
        map = {}
        for elt, p in tab:
            map[elt] = 0
        for i in range(nb):
            res = randregex.produce_randregex_from_tree(mytree)
            for elt, p in tab:
                if re.fullmatch(elt, res) is not None:
                    map[elt] = map[elt] + 1
        for elt, p in tab:
            assert abs(map[elt]/float(nb) - p) < err            


    def test_pipe(self):
        self.basic_test("foo|bar", 1000, [("foo", 1/2.), ("bar", 1/2.)])
        self.basic_test("toto|(tata|titi)", 1000, 
                        [("toto", 1/2.), ("tata", 1/4.), ("titi", 1/4.)])
        self.basic_test("[0-9]{3,5}|[0-9]{10,12}|[0-9]{50}", 1000, [
            ("[0-9]{3,5}", 1/3.), ("[0-9]{10,12}", 1/3.), ("[0-9]{50}", 1/3.)
        ])
        self.basic_test("ic<10>i|lala<10>|vvvvv", 1000, 
                        [("ic<10>i", 9/20.), ("lala", 1/10.), ("vvvvv", 9/20.)])
        
        

    def test_custom_proba(self):
        self.basic_test("toto<10>|titi<20>|tata<70>", 1000, 
                        [("toto", 1/10.), ("titi", 2/10.), ("tata", 7/10.)])
        self.basic_test("toto|titi|tata<90>", 1000, 
                        [("toto", 1/20.), ("titi", 1/20.), ("tata", 9/10.)])
        self.basic_test("[a<30>e<50>iouy]", 1000, [
            ("a", 3/10.), ("e", 5/10.), ("i", 1/20.), 
            ("o", 1/20.), ("u", 1/20.), ("y", 1/20.)
        ])
        self.basic_test("[a-c<70>d-f]", 1000, [
            ("a", 7/30.), ("b", 7/30.), ("c", 7/30.), 
            ("d", 1/10.), ("e", 1/10.), ("f", 1/10.)
        ])
        self.basic_test("e{1,2<20>}{9,10}", 1000, [
            ("e", 1/10.), ("ee", 1/10.), ("e{9}", 4/10.), ("e{10}", 4/10.)
        ])       
    
class TestsComplex:
    def basic_test(self, pattern, nb=1, testpattern=None):
        if testpattern is None:
            testpattern = pattern
        mytree = randregex.parse_rand_regex(pattern)
        for i in range(nb):
            res = randregex.produce_randregex_from_tree(mytree)
            assert re.fullmatch(testpattern, res) is not None    

    def test_complex1(self):
        self.basic_test("(ici|lala((foo|b[(co|ol)]a|r)to{2}to|la(lol){1,3}la))", 50)

        self.basic_test("(ici|lala((?var=foo|b[(co|ol)]a|r)to{2}t($var)o|la(lol){1,3}la))", 50, "(?:ici|lala(?:(foo|b[(co|ol)]a|r)to{2}t\\1o|la(lol){1,3}la))")

        self.basic_test("(?var=toto|tata)(?toto=toto|($var))waza($toto)", 50, 
                        "(toto|tata)(toto|\\1)waza\\2")

        self.basic_test(">|d", 50, 
                        ">|d")

class TestsError:
    def basic_test(self, pattern, msg):
        try:        
            mytree = randregex.parse_rand_regex(pattern)
            assert(False)
        except randregex.RandRegexException as e:
            assert(str(e) == msg)

    def test_error1(self):        
        self.basic_test("%(c)", "Error while parsing %d or %f")
        self.basic_test("%[c]", "Error while parsing %d or %f")
        self.basic_test("%s[c]", "Error while parsing %d or %f")

    def test_error2(self):            
        self.basic_test("[a-z]{2<s>}{3}", "Error while parsing <n>")
        self.basic_test("[a-z]{2<[as]>}{3}", "Error while parsing <n>")
        self.basic_test("toto<c>", "Error while parsing <n>: n not an integer")
        self.basic_test("toto<(toto)>", "Error while parsing <n>: n not an integer")
        self.basic_test("toto<>", "A percentage specification <n> cannot be empty")
        
    def test_error3(self):
        self.basic_test("toto{s}", "Error while parsing {n,m} or {n}")
        self.basic_test("toto{[as]}", "Error while parsing {n,m} or {n}")
        self.basic_test("toto{2;3}", "Error while parsing {n,m} or {n}")
        self.basic_test("toto{2,1}", "Quantities {n,m} must be such that n <= m")
        
    def test_error4(self):
        self.basic_test(
            "(?to#to=cool)", 
            "The group names must consists only of alphanumerical caracters"
        )
        self.basic_test(
            "(?=cool)", 
            "The group names must have at least one caracter"
        )
        self.basic_test("(?cool", "Error while parsing the group name")
        self.basic_test("(?[vv]=lol)", "Error while parsing the group name")
        
    def test_error5(self):
        self.basic_test(
            "($to#to)", 
            "The captured group names must consists only of alphanumerical caracters"
        )
        self.basic_test("($)", "The captures group names must have at least one caracter")
        self.basic_test("($cool", "Error while parsing the captured group name")
        self.basic_test("($[vv]=lol)", "Error while parsing the captured group name")
        
    def test_error6(self):
        self.basic_test("[]", "An empty character list [] is forbidden")
        self.basic_test("[toto", "A caracter '[' does not have a closing caracter ']'")
        
    def test_error7(self):
        self.basic_test("(waza))", "Parenthesis error")
        self.basic_test("((waza)", "Parenthesis error")
        self.basic_test("((wa(ss)z(dd)a)tot(d(d)o)", "Parenthesis error")
        
    def test_error8(self):
        self.basic_test("toto<60>|titi<60>", "The sum of percentage cannot go over 100")
        self.basic_test(
            "toto<70>|titi<20>", "The sum of percentage is smaller than 100 "
                                 "without any possibility to complete"
        )
        self.basic_test("toto<100>|titi", "Some events have a probability of 0.")
        
        