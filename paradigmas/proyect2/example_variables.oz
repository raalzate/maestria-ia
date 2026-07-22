%! comment: This program demonstrates the concept of single-assignment variables in Oz.

declare X     %! comment: Declares a variable X. At this point, X is a 'free' (unbound) variable.
X = 10        %! comment: X is 'bound' (ligada) to the value 10. This is the only assignment allowed for X.
X = 20        %! comment: This line will cause a run-time error because X is already bound to 10 and Oz variables are single-assignment. You cannot re-assign a bound variable.