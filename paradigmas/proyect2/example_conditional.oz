%! comment: This program demonstrates a simple conditional statement (if-then-else) in Oz.

declare X Y %! comment: Declares two variables, X and Y.
X = 10 %! comment: Assigns the value 10 to variable X.
if X > 5 then %! comment: Checks if X is greater than 5.
   Y = 'mayor' %! comment: If the condition is true, Y is assigned the atom 'mayor'.
else %! comment: Otherwise (if the condition is false),
   Y = 'menor_o_igual' %! comment: Y is assigned the atom 'menor_o_igual'.
end
{Show Y} %! comment: Displays the final value of Y (which should be 'mayor' in this case).