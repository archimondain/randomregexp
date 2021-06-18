# Purpose

**Randomregexp** takes regular expressions and randomly generates strings maching them.
It does not take *any* regular expression and there is a few things which can be added to the usual format, in particular to specify probability distributions.

# Usage

````python
import randregex.randregex as randregex
#Create the tree
tree = randregex.parse_rand_regex("toto|titi|tata")
#Generate a random regexp from the tree
res = randregex.produce_randregex_from_tree(mytree)
````

# Format

  * The pipe `"exp1|exp2"` : randomly generates `"exp1"` or `"exp2"` with probability 1/2 each.

    **Example** : `"toto|tata|titi"` generates `"toto"`, `"tata"` or `"titi"` with probability 1/3 each.
    
  * Groups `"(exp)"` : can be used to group things and change probabilities.
  
    **Example** : `"My teacher (rocks|sucks)"` generates `"My teacher rocks"` with probability 1/2 or `"My teacher sucks"` with probability 1/2.
    
    **Example** : `"toto|(tata|titi)"` generates `"toto"` with probability 1/2 and `"tata"` or `"titi"` with probability 1/4.
    
  * Squared brackets `"[a-z]"` : can be used to randomly generate a character in the range.
    
    **Example** : `"[abcxyz]"` generates a character among {a, b, c, x, y, z} with probability 1/6 each.
    
    **Example** : `"[a-z]"` generates a character among {a, b, ..., z} with probability 1/26 each.
    
    **Example** : `"[a-zA-Z0-9_]"` generates a character among {a, ..., z, A, ..., Z, 0, ..., 9, _} with probability 1/63 each.
    
  * Specify quantities - `"{n,m}"` : it is possible to specify a maximum and minimum number of time something is repeated.

    **Example** : `"ahah{1,4}"` generates `"ahah"`, `"ahahh"`, `"ahahhh"` or `"ahahhhh"` with probability 1/4 each.
    
    **Example** : `"(ahah){1,4}"` generates `"ahah"`, `"ahahahah"`, `"ahahahahahah"` or `"ahahahahahahahah"` with 1/4 probability each.
    
    **Example** : `"(a|e|i){1,4}"` generates between 1 and 4 letters picked among {a, e, i}.
    
    **Example** : `"[0-9]{3}"` generates three numbers. 
    
    **Example** : `"[0-9]{3,5}{97,99}{50}"` generates between three and five numbers with 1/3 probability, between 97 and 99 numbers with 1/3 probability and 50 numbers with 1/3 probability.

  * Random numbers - `"%d"` and `"%f"` : can be used to generate random integers or random floats. In this case quantities {n,m} means something different : the lower and upper bounds.

    **Example** : `"%d{-543,543}"` generates a random integer between -543 et 543.
    
    **Example** : `"(%d{1,6} ){3}"` generates three integer between 1 and 6 separated with a space.
    
    **Example** : `"%f{-1.0,1.0}"` generates a float between -1 and 1.

  * The named groups `"(?var=...)"` and `"($var)"` : it is possible to name groups with `?=` and reuse what was generated with `$`.

    **Example** : `"(?var=%d{1,1000}) equals ($var)"` generates a string of the form `"n equals n"` where `n` is randomly picked between 0 and 1000.
    
    **Example** : `"(?blah=[a-z]{5}) is repeated twice in ($blah){2}"` generates a string of the form `"s is repeated twice in ss"` where `s` is a string of 5 lowercase characters.
    
    **Warning** : `"(?var=[a-z]{5}){2} is ($var) repeated twice"` is not well defined because `"[a-z]{5}"` is repeated twice. The current format does not specify which of the two will be `"($var)"`.


  * Specify custom probabilities - `"exp1<30>|exp2<70>"` : It is possible to specify custom probabilities in three different ways : with pipes, inside squared brackets, and inside quantities. The specification of a probability of for instance 30% is done with `"<30>"`.
  
    **Example** : `"toto<10>|titi<20>|tata<70>"` generates `"toto"` with 10% of chance, `"titi"` with 20% of chance and `"tata"` with 70% of chance.
    
    **Example** : `"toto|titi|tata<97>"` generates `"toto"` with 97% of chance, `"titi"` with 1.5% of chance and `"tata"` with 1.5% of chance.
    
    **Example** : `"[a<30>e<50>iouy]"` generates `"a"` with 30% of chance, `"e"` with 50% of chance, and `"i"`, `"o"`, `"u"` or `"y"` each with 5% of chance.
    
    **Example** : `"[a-c<60>d-z_]"` generates a letter among `"a"`, `"b"` or `"c"` with 60% of chance, and a character among {d, ..., z, _} with probability (1/24) * 0.4.
    
    **Example** : `"e{1,2<10>}{9,10}"` generates with 10% of chance either `"e"` or `"ee"`, and with 90% of chance either `"eeeeeeeee"` or `"eeeeeeeeee"`.
    
    **Warning** : `"toto<60>|tata<60>"` gives an error because the sum of percentage goes above 100.
    
    **Warning** : `"toto<60>|tata<10>"` gives an error because the sum of percentage is below 100.


  * Escaped characters : When we are not inside squared brackets, the following characters can be escaped (for other characters `'c'`, `'\c'` will be equal to `'\c'`).
    * '\n' means end of line
	* '\t' means tabulation
    * '\\(' means '('
    * '\\)' means ')'
    * '\\[' means '['
    * '\\]' means ']'
    * '\\|' means '|'
    * '\\{' means '{'
    * '\\}' means '}'
    * '\\%' means '%'
    * '\\<' means '<'
    * '\\>' means '>'
    * '\\\\' means '\\'
  
    When we are not inside square brackets, the following characters can be escaped : 
    * '\\[' means '['
    * '\\]' means ']'
    * '\\<' means '<'
    * '\\>' means '>'
    * '\\\\' means '\\'
				