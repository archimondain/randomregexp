# -*- coding: utf-8 -*-

"""
This files contains the functions to generate 
a random string following some RegEx pattern
"""

import random
import sys
import logging
from enum import Enum

from .parsing_structures import (
    CountInfos, EltType, RegexElt, PipeElt, GroupElt
)

from .randregex import RandRegexException
#import randregex

def parse_nb(treelist, start):
    """
    Parse %d or %f
    
    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        (int, string): the end position and what was parsed.
    """

    i = start

    if i >= len(treelist) or not RegexElt.IsChar(treelist[i]):
        raise RandRegexException("Error while parsing %d or %f")

    if treelist[i].elt_val == 'd':
        return i, "%d"

    if treelist[i].elt_val == 'f':
        return i, "%f"

    raise RandRegexException("Error while parsing %d or %f")


def parse_weight(treelist, start):
    """
    Parse <n> for an integer n
    
    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        (int, int): the end position and the integer parsed
    """

    i = start
    strper = ""
    while i < len(treelist):
        if not RegexElt.IsChar(treelist[i]):
            raise RandRegexException("Error while parsing <n>")
        if treelist[i].elt_val == '>':
            if strper == "":
                raise RandRegexException(
                    "A percentage specification <n> "
                    "cannot be empty"
                )
            return i, int(strper)
        elif treelist[i].elt_val >= '0' and treelist[i].elt_val <= '9':
            strper += treelist[i].elt_val
        else:
            raise RandRegexException("Error while parsing <n>")

        i = i + 1

    raise RandRegexException("Error while parsing <n>")

def parse_weight_reverse(treelist):
    """
    Reverse parse <n> for an integer n. Meant to be used to parse weight
    of a | clause.
    
    Example : a treelist corresponding to "toto<30>"
    
    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
                     
    Returns:
        (list, int): 
        A new treelist without the "<...>" part together with 
        the parsed weight
        
        Example : on "toto<30>" returns "toto", 30
    """

    if len(treelist) == 0:
        raise RandRegexException("A clause | cannot be empty")

    i = len(treelist) - 1
    if len(treelist) < 2 or not RegexElt.IsChar(treelist[i]):
        return treelist, 0
    
    if treelist[i].elt_val == '>':
        not_int = False
        strper = ""
        i = i - 1
        while i >= 0:
            if not RegexElt.IsChar(treelist[i]):
                not_int = True
            elif treelist[i].elt_val == '<':
                if not_int:
                    raise RandRegexException(
                        "Error while parsing <n>: n not an integer"
                    )
                if strper == "":
                    raise RandRegexException(
                        "A percentage specification <n> "
                        "cannot be empty"                   
                    )
                if i == 0:
                    raise RandRegexException(
                        "A clause | cannot be empty"
                    )
                return treelist[:i], int(strper)
            else:
                strper = treelist[i].elt_val + strper
                if treelist[i].elt_val < '0' or treelist[i].elt_val > '9':
                    not_int = True
            i = i - 1
        return treelist, 0
    else:
        return treelist, 0

    return None

def parse_occ(treelist, start):
    """
    Parse {n,m} or {n} for integers n,m.
    It would also parse things of the form {n,m<w>} or {n<w>}
    
    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        (int, (int, int, int)): 
        (end position, (n, m, weight))
    """

    i = start
    nb1, nb2, strnb1, strnb2 = (1, 1, "", "")
    isNb1 = True
    per = 0
    while i < len(treelist):
        if not RegexElt.IsChar(treelist[i]):
            raise RandRegexException(
                "Error while parsing {n,m} or {n}"
            )
        c = treelist[i].elt_val
        if c == '}':
            if strnb1 == "":
                raise RandRegexException(
                    "Error while parsing {n,m} or {n}"
                )

            try:
                nb1 = int(strnb1)
            except:
                raise RandRegexException(
                    "Error while parsing {n,m} or {n}"
                )
            nb2 = nb1

            if not isNb1:
                if strnb2 == "":
                    raise RandRegexException(
                        "Error while parsing {n,m} or {n}"
                    )
                try:
                    nb2 = int(strnb2)
                except:
                    raise RandRegexException(
                        "Error while parsing {n,m} or {n}"
                    )

            if nb1 > nb2:
                raise RandRegexException(
                    "Quantities {n,m} must be such that n <= m"
                )
            return i, (nb1, nb2, per)
        elif c == ',':
            if not isNb1:
                raise RandRegexException(
                    "Error while parsing {n,m} or {n}"
                )
            else:
                isNb1 = False
        elif c == '<':
            i, per = parse_weight(treelist, i+1)
        elif ((c >= '0' and c <= '9') or c == '.' or c == '-'):
            if isNb1:
                strnb1 += c
            else:
                strnb2 += c
        else:
            raise RandRegexException(
                "Error while parsing {n,m} or {n}"
            )

        i = i + 1

    raise RandRegexException("Error while parsing {n,m} or {n}")

def parse_def_groupname(treelist, start):
    """
    Parse the group name (?var=...)

    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        (int, string): the end position, the parsed name
    """

    i = start
    name = ""
    while i < len(treelist):
        if not RegexElt.IsChar(treelist[i]):
            raise RandRegexException(
                "Error while parsing the group name"
            )            
        c = treelist[i].elt_val
        if c == '=':
            if name == "":
                raise RandRegexException(
                    "The group names must have at least one caracter"
                )
            return i, name
        elif ((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or 
                (c >= '0' and c <= '9') or c == '_'):
            name += c
        else:
            raise RandRegexException(
                "The group names must consists only "
                "of alphanumerical caracters"
            )

        i = i + 1

    raise RandRegexException(
        "Error while parsing the group name"
    )

def parse_use_groupname(treelist, start):
    """
    Parse the captured group name ($var)

    Parameters:
        - treelist (list): list of GroupElt, RegexElt or PipeElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        (int, string): the end position, the parsed name
    """

    name = ""
    nbPar = 0
    backslash = False
    i = start
    while i < len(treelist):
        if not RegexElt.IsChar(treelist[i]):
            raise RandRegexException(
                "Error while parsing the captured group name"
            )
        c = treelist[i].elt_val
        if c == ')':
            if name == "":
                raise RandRegexException(
                    "The captures group names must have at least one caracter"
                )
            return i, name
        elif ((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or 
                  (c >= '0' and c <= '9') or c == '_'):
            name += c
        else:
            raise RandRegexException(
                "The captured group names must consists only "
                "of alphanumerical caracters"
            )
        i = i + 1

    raise RandRegexException(
        "Error while parsing the captured group name"
    )

def parse_sbracket(charlist, start):
    """
    Parse elements within square bracket
    
    Parameters:
        - charlist (list): list of RegexElt
        - start (int): the position to start from in the treelist 
    
    Returns:
        - int : the end position
        - list : A of RegexElt (captured caracters between '[' and ']')
    """

    res = []
    backslash = False
    i = start
    while i < len(charlist):
        if not RegexElt.IsChar(charlist[i]):
            raise RandRegexException(
                "We should never reach this line"
            )    
        c = charlist[i].elt_val
        if backslash:
            if c == ']' or c == '[':
                res.append(charlist[i])
            else:
                res.append(RegexElt(EltType.CHAR, '\\'))
                res.append(charlist[i])
            backslash = not backslash
        elif c == ']':
            if res == []:
                raise RandRegexException(
                    "An empty character list [] is forbidden"
                )
            return i, res
        elif c == '\\':
            backslash = not backslash
        else:
            res.append(charlist[i])
        i = i + 1

    raise RandRegexException(
        "A caracter '[' does not have a closing caracter ']'"
    )
