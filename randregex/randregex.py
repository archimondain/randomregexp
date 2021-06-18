# -*- coding: utf-8 -*-

"""
This files contains the functions to generate 
a random string following some RegEx pattern
"""

import random
import sys
import logging
from enum import Enum

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

class RandRegexException(Exception):
    """
    The randRegex exception class
    """

    pass

from .parsing_structures import (
    CountInfos, EltType, RegexElt, PipeElt, GroupElt
)

from .helper_parse_fct import (
    parse_nb, parse_weight, parse_weight_reverse, parse_occ, 
    parse_def_groupname, parse_use_groupname, parse_sbracket, 
)

def step1_sbracket(charlist):
    """
    Deal with squared bracket
    
    Parameters:
        charlist (list): list of RegexElt

    Returns:
        list: A new list of RegexElt in which '[' '...' ']' 
              have been replaced by a RegexElt of SBRACKET type
    """

    res = []
    backslash = False
    i = 0
    while i < len(charlist):
        if not RegexElt.IsChar(charlist[i]):
            raise RandRegexException(
                "We should never reach this line"
            )    
    
        c = charlist[i].elt_val
        if backslash:
            if c == '[' or c == ']':
                res.append(charlist[i])
            else:
                res.append(RegexElt(EltType.CHAR, '\\'))
                res.append(charlist[i])
            backslash = not backslash
        elif c == '\\':
            backslash = not backslash
        elif c == '[':
            i, li = parse_sbracket(charlist, i+1)
            infos = []
            while i+1 < len(charlist) and charlist[i+1].elt_val == '{':
                i, info = parse_occ(charlist, i+2)
                infos.append(info)
            if not infos:
                infos = [(1, 1, 0)]
            res.append(RegexElt(
                EltType.SBRACKET, li, count_infos=CountInfos(infos)
            ))
        else:
            res.append(charlist[i])
        i = i + 1

    return res



def step2_groups(charlist):
    """
    Deal with groups
    
    Parameters:
        charlist (list): list of RegexElt
    
    Returns:
        list: A new list of GroupElt or RegexElt
              in which every group is now a GroupElt
    """

    return step2_groups_rec(charlist, 0, 0, False)

def step2_groups_rec(charlist, start, nbrec, startP):
    """
    Deal recursively with creating groups   
    """

    res = []
    backslash = False
    i = start
    namePar = ""
    while i < len(charlist):
        c = charlist[i].elt_val
        if charlist[i].elt_type == EltType.SBRACKET:
            res.append(charlist[i])
        else:
            if backslash:
                if c == '(' or c == ')':
                    res.append(charlist[i])
                else:
                    res.append(RegexElt(EltType.CHAR, '\\'))
                    res.append(charlist[i])
                backslash = not backslash
            elif c == '\\':
                backslash = not backslash
            elif c == '(':
                oldnamePar = namePar
                i, li, namePar, isUse = step2_groups_rec(
                    charlist, i+1, nbrec+1, True
                )
                infos = []
                while i+1 < len(charlist) and charlist[i+1].elt_val == '{':
                    i, info = parse_occ(charlist, i+2)
                    infos.append(info)
                if not infos:
                    infos = [(1, 1, 0)]
                if not isUse:
                    res.append(GroupElt(li, CountInfos(infos), namePar))
                else:
                    res.append(RegexElt(
                        EltType.GROUP_NAME, namePar, CountInfos(infos)
                    ))
                namePar = oldnamePar
            elif c == ')':
                if nbrec == 0:
                    raise RandRegexException("Parenthesis error")
                else:
                    return i, res, namePar, False
            elif startP and c == '?':
                i, namePar = parse_def_groupname(charlist, i+1)
                startP = False
            elif startP and c == '$':
                i, namePar = parse_use_groupname(charlist, i+1)
                return i, None, namePar, True
            else:
                res.append(charlist[i])
        i = i + 1

    if nbrec != 0:
        raise RandRegexException("Parenthesis error")
    return res


def step3_pipes(treelist):
    """
    Deal with pipes

    Parameters:
        treelist (list): list of GroupElt or RegexElt
    
    Returns:
        list: list of GroupElt, RegexElt or PipeElt in which 
              every "|" clause have been delt with.
    """

    res = []
    cur = []
    backslash = False
    i = 0
    while i < len(treelist):
        if isinstance(treelist[i], GroupElt):
            cur.append(GroupElt(
                step3_pipes(treelist[i].list_elt), 
                treelist[i].count_infos, treelist[i].name
            ))
        elif RegexElt.IsChar(treelist[i]):
            c = treelist[i].elt_val            
            if backslash:
                if c == '|':
                    cur.append(treelist[i])
                elif c == '<' or c == '>':
                    cur.append(RegexElt(EltType.ESCAPED_CHAR, c))
                else:
                    cur.append(RegexElt(EltType.CHAR, '\\'))
                    cur.append(treelist[i])
                backslash = not backslash
            elif c == '\\':
                backslash = not backslash
            elif c == '|':
                cur, per = parse_weight_reverse(cur)
                res.append((cur, per))
                cur = []
            else:
                cur.append(treelist[i])
        else:
            cur.append(treelist[i])

        i = i + 1

    cur, per = parse_weight_reverse(cur)
    res.append((cur, per))

    return [PipeElt(res, compute=True)]


def brackets_2_pipes(regex_elt):
    """
    Transform RegexElt of type SBRACKET into PipeElt

    Parameters:
        regex_elt (list): A RegexElt of type SBRACKET
    
    Returns:
        PipeElt: the tranformed RegexElt
    """

    charlist = regex_elt.elt_val
    res = []
    backslash = False
    i = 0
    while i < len(charlist):
        c = charlist[i].elt_val

        if backslash:
            if c == '<' or c == '>':
                res.append((RegexElt(EltType.CHAR, c), 0))
            else:
                res.append((RegexElt(EltType.CHAR, '\\'), 0))
                res.append((RegexElt(EltType.CHAR, c), 0))
            backslash = not backslash
        elif c == '\\':
            backslash = not backslash
        elif i+2 < len(charlist) and charlist[i+1].elt_val == '-':
            per = 0
            if i + 3 < len(charlist) and charlist[i+3].elt_val == '<':
                j, per = parse_weight(charlist, i+4)
                tmp = []
                for char in range(ord(c), ord(charlist[i+2].elt_val) + 1):
                    tmp.append((RegexElt(EltType.CHAR, chr(char)), 0))
                res.append((PipeElt(tmp, compute=True), per))
            else:
                j = i + 2
                for char in range(ord(c), ord(charlist[i+2].elt_val) + 1):
                    res.append((RegexElt(EltType.CHAR, chr(char)), 0))
            i = j
        else:
            per = 0
            if i+1 < len(charlist) and charlist[i+1].elt_val == '<':
                i, per = parse_weight(charlist, i+2)
            res.append((RegexElt(EltType.CHAR, c), per))

        i = i + 1

    return PipeElt(res, compute=True)

def step4_misc(treelist):
    """
    Deal with numbers, brackets and some escaping caracters

    Parameters:
        treelist (list): list of GroupElt, RegexElt or PipeElt
    
    Returns:
        list: list of GroupElt, RegexElt or PipeElt in which 
              various things have been dealt with
    """

    res = []

    backslash = False
    i = 0
    while i < len(treelist):
        if isinstance(treelist[i], PipeElt):
            res.append(PipeElt(
                [(step4_misc(elt), per) for elt, per in treelist[i].list_elt],
                treelist[i].expected_weight                
            ))
        elif isinstance(treelist[i], GroupElt):
            res.append(GroupElt(
                step4_misc(treelist[i].list_elt), 
                treelist[i].count_infos, treelist[i].name
            ))
        elif treelist[i].elt_type == EltType.SBRACKET:
            res.append(GroupElt(
                brackets_2_pipes(treelist[i]), 
                treelist[i].count_infos, ""
            ))        
        else:
            c = treelist[i].elt_val
            t = treelist[i].elt_type        
            if backslash:
                if c == '%':
                    res.append(treelist[i])
                elif c == 'n':
                    res.append(RegexElt(t, '\n'))
                elif c == 't':
                    res.append(RegexElt(t, '\t'))
                elif c == '\\':
                    res.append(RegexElt(t, '\\'))
                elif c == '{':
                    res.append(RegexElt(EltType.ESCAPED_CHAR, '{'))
                elif c == '}':
                    res.append(RegexElt(EltType.ESCAPED_CHAR, '}'))
                else:
                    res.append(RegexElt(EltType.CHAR, '\\'))
                    res.append(treelist[i])
                backslash = not backslash
            elif c == '\\':
                backslash = not backslash
            elif c == '%':
                i, nb = parse_nb(treelist, i+1)
                infos = []
                while i+1 < len(treelist) and treelist[i+1].elt_val == '{':
                    i, info = parse_occ(treelist, i+2)
                    infos.append(info)
                if not infos:
                    infos = [(1, 1, 0)]
                res.append(RegexElt(
                    EltType.NUMBER, nb, CountInfos(infos, testneg=False)
                ))
            else:
                res.append(treelist[i])
        i = i + 1

    return res


def step5_characters(treelist):
    """
    Deal with single characters by associating their count informations

    Parameters:
        treelist (list): list of GroupElt, RegexElt or PipeElt
    
    Returns:
        list: list of GroupElt, RegexElt or PipeElt in which 
              single characters have been dealt with
    """

    res = []

    if not isinstance(treelist, list):
        treelist = [treelist]    

    i = 0
    while i < len(treelist):
        if isinstance(treelist[i], PipeElt):
            res.append(PipeElt([
                (step5_characters(elt), per) for 
                    elt, per in treelist[i].list_elt
            ], treelist[i].expected_weight))
        elif isinstance(treelist[i], GroupElt):
            res.append(GroupElt(
                step5_characters(treelist[i].list_elt), 
                treelist[i].count_infos, treelist[i].name
            ))        
        else:
            t = treelist[i].elt_type
            c = treelist[i].elt_val

            if t == EltType.CHAR or t == EltType.ESCAPED_CHAR:
                infos = []
                while (i+1 < len(treelist) and 
                          RegexElt.IsChar(treelist[i+1]) and
                          treelist[i+1].elt_val == '{'):
                    i, info = parse_occ(treelist, i+2)
                    infos.append(info)
                if not infos:
                    infos = [(1, 1, 0)]
                res.append(RegexElt(t, c, CountInfos(infos)))
            else:
                res.append(treelist[i])

        i = i + 1

    return res


def pre_parse_randregex(randregex):
    """
    Transform the regex into list of characters

    Parameters:
        randregex (string): the randregex
    
    Returns:
        list: list of RegexElt
    """

    charlist = []
    for elt in randregex:
        charlist.append(RegexElt(EltType.CHAR, elt))
    return charlist


def parse_rand_regex(randregex):
    """
    Return the randRegEx information Tree.
    The result should be used with 'produce_randregex_from_tree' method

    Parameters:
        randregex (string): the randregex
    
    Returns:
        list: list of GroupElt, RegexElt or PipeElt    
    """        

    charlist = pre_parse_randregex(randregex)
    logging.debug("0/ {}".format(charlist))
    
    charlist = step1_sbracket(charlist)
    logging.debug("1/ {}".format(charlist))
    
    treelist = step2_groups(charlist)
    logging.debug("2/ {}".format(treelist))
    
    treelist = step3_pipes(treelist)
    logging.debug("3/ {}".format(treelist))
    
    treelist = step4_misc(treelist)
    logging.debug("4/ {}".format(treelist))
    
    treelist = step5_characters(treelist)
    logging.debug("5/ {}".format(treelist))
    
    return treelist

def produce_randregex(treelist, names):
    """
    Produce random string recursively.
    Called By produce_randregex_from_tree
    
    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - names : a map of generated group names
    
    Returns:
        string: the random string maching the randregex
    """

    res = ""
    for regex_elt in treelist:            
        if isinstance(regex_elt, PipeElt):
            r = random.randint(0, regex_elt.expected_weight - 1)
            t = 0
            picked = None
            for choice, weight in regex_elt.list_elt:
                t += weight
                if r <= t:
                    picked = choice
                    break
            res += produce_randregex(choice, names)
        else:
            
            r = random.randint(0, regex_elt.count_infos.expected_weight - 1)
            t = 0
            picked = None
            for nb1, nb2, per in regex_elt.count_infos.count_infos:
                t += per
                if r <= t:
                    picked = (nb1, nb2)
                    break

            if (isinstance(regex_elt, GroupElt) or 
                    regex_elt.elt_type != EltType.NUMBER):
                r = random.randint(picked[0], picked[1])
                i = 1
                while i <= r:
                    if isinstance(regex_elt, GroupElt):
                        tmp = produce_randregex(regex_elt.list_elt, names)
                        if regex_elt.name:
                            names[regex_elt.name] = tmp
                    elif regex_elt.elt_type == EltType.GROUP_NAME:
                        if regex_elt.elt_val not in names:                            
                            raise RandRegexException(
                                "The name {} is used before "
                                "being defined.".format(regex_elt.name)
                            )
                        tmp = names[regex_elt.elt_val]
                    elif (regex_elt.elt_type == EltType.CHAR or 
                              regex_elt.elt_type == EltType.ESCAPED_CHAR):
                        tmp = regex_elt.elt_val

                    res += tmp
                    i = i + 1
            else:
                if regex_elt.elt_val == "%d":
                    r = random.randint(picked[0], picked[1])
                else:
                    r = random.uniform(picked[0], picked[1])
                res += str(r)
    return res

def produce_randregex_from_tree(tree):
    """
    Generate a random string according to the information 
    returned by the method 'parse_rand_regex'
    """

    return produce_randregex(tree, {})
