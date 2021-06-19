# -*- coding: utf-8 -*-

"""
This files contains the functions to generate 
a random string following some RegEx pattern
"""

import random
import sys
import logging
from enum import Enum

from .randregex import RandRegexException

class CountInfos:
    """
    Attributes:
        - count_infos : A list of count information of the form 
        (nb1, nb2, weight) where 
            - nb1 is a start integer, 
            - nb2 >= nb1 is an end integer
            - weigth is an integer.
        
        Example : the list [(1,2,30),(3,4,70)] means 
        "between 1 and 2 with 30 percent of chance" and 
        "between 3 and 4 with 70 percent of chance"
    
        - expected_weight : an expected total for all weigth 
                            within the list 
    """

    def __init__(self, count_infos=[(1, 1, 0)], expected_weight=100, 
                 compute=True, testneg=True):
        if not compute:
            self.count_infos = count_infos
            self.expected_weight = expected_weight

        self.count_infos, self.expected_weight = \
            CountInfos.computeWeightInfos(
                count_infos, expected_weight, testneg
            )

    @staticmethod
    def computeWeightInfos(count_infos, expected_weight, testNeg):
        """
        The idea is to return a new count_infos by attributing a
        positive wight to all 0 weighted elements, so that we reach  
        the total expected_weight.
        
        In order to keep integer quantities, everything is multiplied 
        so that a new expected weight is also returned.

        For instance:
            count_infos : [(1,2,30),(3,4,0),(6,7,0)]
            expected_tot : 100
        Would return:
            count_infos : [(1,2,60),(3,4,70),(3,4,70)]
            expected_tot : 200
        """

        totweight = 0
        nbEmpty = 0
        for nb1, _, weight in count_infos:
            if testNeg and nb1 < 0:
                raise RandRegexException(
                    "The quantities {n,m} cannot be negative"
                )
            if weight == 0:
                nbEmpty = nbEmpty+1
            totweight += weight
        if totweight > 100:
            raise RandRegexException(
                "The sum of percentage cannot go over 100"
            )
        if totweight < 100:
            if nbEmpty == 0:
                raise RandRegexException(
                    "The sum of percentage is smaller than 100 "
                    "without any possibility to complete"
                )
            else:
                q = 100 - totweight
                mult = nbEmpty

            newinfos = []
            for nb1, nb2, weight in count_infos:
                if weight == 0:
                    newinfos.append((nb1, nb2, q))
                else:
                    newinfos.append((nb1, nb2, weight * mult))
        else:
            if nbEmpty > 0:
                raise RandRegexException(
                    "Some events have a probability of 0."
                )
            newinfos = infos
            mult = 1

        return newinfos, expected_weight * mult


class EltType(Enum):
    GROUP_NAME = 1
    SBRACKET = 2
    NUMBER = 3
    CHAR = 4
    ESCAPED_CHAR = 5

class RegexElt:
    """
    The class for basic elements in the regex. They may be
        - A group name, corresponding to something like "($var)"
        - A squared bracket, corresponding to something like "[a-z_]"
        - A number, corresponding to something like "%d" or "%f"
        - A char, corresponding to something like "c"
        - An escaped char, corresponding to something like "\\{"
    An element may also contains counting informations,
    for instance "($var){2,3}{4,5}" comes with [(2,3,50),(4,5,50)]
    as count_infos.
    """
    def __init__(self, elt_type, elt_val, count_infos=None):
        self.elt_type = elt_type
        self.elt_val = elt_val
        self.count_infos = count_infos

    @staticmethod
    def IsChar(elt):
        return (isinstance(elt, RegexElt) and 
                    elt.elt_type == EltType.CHAR)

    def __str__(self):
        return (str(self.elt_type) + str(self.elt_val) 
                    + str(self.count_infos))

    def __repr__(self):
        return (repr(self.elt_type) + repr(self.elt_val) 
                    + repr(self.count_infos))

class PipeElt:
    """
    The class for an "or list" of elements in the regex. 
    Atrributes:
        - list_elt: 
          A list of the form [(elt1, weight1), (elt2, weight2), ...]
          Each "elti" may be 
              - a RegexElt
              - a PipeElt 
              - a GroupElt
        - expected_weight: 
          The expected total weight for elements of the list
                           
    """

    def __init__(self, list_elt, expected_weight=100, compute=False):
        if not compute:
            self.list_elt = list_elt
            self.expected_weight = expected_weight        
            return
        
        self.list_elt, self.expected_weight = \
            PipeElt.computeWeightInfos(list_elt, expected_weight)


    @staticmethod
    def computeWeightInfos(list_elt, expected_weight):
        """
        Similar to CountInfos.computeWeightInfos, but for "or lists"
        """
        totper = 0
        nbEmpty = 0
        for choice, per in list_elt:
            if per == 0:
                nbEmpty = nbEmpty+1
            totper += per
        if totper > expected_weight:
            raise RandRegexException(
                "The sum of percentage cannot go over 100"
            )
        if totper < expected_weight:
            if nbEmpty == 0:
                raise RandRegexException(
                    "The sum of percentage is smaller than 100 "
                    "without any possibility to complete"
                )
            else:
                q = expected_weight - totper
                mult = nbEmpty

            newelt = []
            for choice, per in list_elt:
                if per == 0:
                    newelt.append((choice, q))
                else:
                    newelt.append((choice, per * mult))
            return newelt, expected_weight * mult
        else:
            if nbEmpty > 0:
                raise RandRegexException(
                    "Some events have a probability of 0."
                )
            return list_elt, expected_weight

class GroupElt:
    """
    The class for a elements grouped into a parenthesis. 
    Atrributes:
        - list_elt: 
          A list of the form [elt1, elt2, ...]
          Each "elti" may be 
              - a RegexElt
              - a PipeElt 
              - a GroupElt
        - count_infos:
          The CountInfo of the group
        - name: 
          The name of the group
    """

    def __init__(self, list_elt, count_infos=None, name=None):
        self.list_elt = list_elt
        self.count_infos = count_infos
        self.name = name
